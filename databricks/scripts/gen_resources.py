"""Generate resources/benchmark.yml: every job, pipeline, warehouse and cluster of the benchmark.

Two tests per config:
  full_<cfg>   original TPC-DI single batch (raw files to star schema)
  daily_<cfg>  one simulated day of Shannon Barrow's augmented incremental mode
               (setup and teardown are separate shared jobs, not timed)

Templates in scripts/ come from the TPC-DI repo's own Driver output, with the repo
path swapped for ${var.tpcdi_path}. Pipelines read ${var.scale_factor}, so deploy
once per scale factor:  databricks bundle deploy --var scale_factor=1000
Run: python3 scripts/gen_resources.py
"""
import copy, json, pathlib
import yaml

root = pathlib.Path(__file__).parent.parent
S = root / "scripts"
full_tpl = json.load(open(S / "serverless_job_template.json"))
daily_tpl = json.load(open(S / "daily_job_template.json"))
sdp_tpl = {k: json.load(open(S / f"sdp_{k}_pipeline_template.json")) for k in ("full", "daily")}
ids = json.load(open(S / "serverless_ids.json"))

CATALOG = "firstprinciplesde"
VOL = "/Volumes/firstprinciplesde/tpcdi_raw_data/tpcdi_volume/"
SF = "${var.scale_factor}"
RES = {"sql_warehouses": {}, "clusters": {}, "pipelines": {}, "jobs": {}}
TAGS = {"project": "etl-benchmark"}


def param(name, default):
    return {"name": name, "default": default}


def daily_params(wh_db, n_days="6"):
    return [param("catalog", CATALOG), param("scale_factor", SF), param("tpcdi_directory", VOL),
            param("wh_db", wh_db), param("batch_date", ""), param("incremental_batches_to_run", n_days)]


def classic(node="2xlarge", engine="PHOTON", spot=False, min_w=1, max_w=8):
    # Driver on-demand always (first_on_demand 1). Workers on-demand unless spot.
    # Set explicitly: the workspace default is spot with no on-demand nodes, driver included.
    return {"spark_version": "18.x-scala2.13", "node_type_id": f"m8gd.{node}",
            "runtime_engine": engine, "data_security_mode": "SINGLE_USER",
            "autoscale": {"min_workers": min_w, "max_workers": max_w},
            "aws_attributes": {"availability": "SPOT_WITH_FALLBACK" if spot else "ON_DEMAND",
                               "first_on_demand": 1, "zone_id": "auto"}}


def place(job, tasks, c):
    """Put every notebook task of a job on the config's compute."""
    if c.get("serverless_id"):
        job["job_clusters"] = [{"job_cluster_key": "compute", "serverless_compute": {"policy_id": c["serverless_id"]}}]
    elif c.get("cluster"):
        job["job_clusters"] = [{"job_cluster_key": "compute", "new_cluster": c["cluster"]}]
    if c.get("perf"):
        job["performance_target"] = c["perf"]
    for t in tasks:
        nb = t.get("notebook_task")
        if not nb:
            continue
        if c.get("serverless_id") or c.get("cluster"):
            t["job_cluster_key"] = "compute"
        if c.get("ap"):
            t["existing_cluster_id"] = "${resources.clusters.%s.id}" % c["ap"]
        if c.get("wh"):
            nb["warehouse_id"] = "${resources.sql_warehouses.%s.id}" % c["wh"]


def add(key, job):
    job.setdefault("max_concurrent_runs", 1)
    job.setdefault("queue", {"enabled": True})
    job["tags"] = {**TAGS, **job.get("tags", {})}
    RES["jobs"][key] = job


# ---------- compute configs for the notebook engine ----------
CONFIGS = {
    "srv_standard": {"perf": "STANDARD"},
    "srv_optimized": {"perf": "PERFORMANCE_OPTIMIZED"},
    **{f"srv_{s}": {"serverless_id": ids[s]} for s in ("small", "medium", "large", "xlarge")},
    "jc_xlarge": {"cluster": classic("xlarge")},
    "jc_2xlarge": {"cluster": classic("2xlarge")},
    "jc_8xlarge": {"cluster": classic("8xlarge")},
    "jc_2xlarge_spot": {"cluster": classic("2xlarge", spot=True)},
    "jc_2xlarge_nophoton": {"cluster": classic("2xlarge", engine="STANDARD")},
    "jc_2xlarge_min2": {"cluster": classic("2xlarge", min_w=2)},
    "ap_2xlarge": {"ap": "ap_2xlarge"},
}

RES["clusters"]["ap_2xlarge"] = {**classic("2xlarge"), "cluster_name": "etl-benchmark-ap_2xlarge",
                                 "autotermination_minutes": 10}
RES["sql_warehouses"]["wh_large"] = {"name": "etl-benchmark-wh_large", "cluster_size": "Large",
                                     "warehouse_type": "PRO", "enable_serverless_compute": True,
                                     "auto_stop_mins": 5}

for key, c in CONFIGS.items():
    # full load
    j = copy.deepcopy(full_tpl)
    j.update(name=f"etl-benchmark-full-{key}", tags={"config": key, "test": "full"})
    for p in j["parameters"]:
        if p["name"] == "wh_db":
            p["default"] = f"etl_full_{key}"
        if p["name"] == "scale_factor":
            p["default"] = SF
    place(j, j["tasks"], c)
    add(f"full_{key}", j)
    # one day of the daily load
    tasks = copy.deepcopy(daily_tpl["tasks"])
    j = {"name": f"etl-benchmark-daily-{key}", "tags": {"config": key, "test": "daily"},
         "parameters": daily_params(f"etl_daily_{key}")[:5], "tasks": tasks}
    place(j, tasks, c)
    add(f"daily_{key}", j)

# ---------- SQL warehouse: SQL notebooks for the full load, dbt for the daily load ----------
j = copy.deepcopy(full_tpl)
j.update(name="etl-benchmark-full-wh_large", tags={"config": "wh_large", "test": "full"})
for p in j["parameters"]:
    if p["name"] == "wh_db":
        p["default"] = "etl_full_wh_large"
    if p["name"] == "scale_factor":
        p["default"] = SF
place(j, j["tasks"], {"wh": "wh_large"})
add("full_wh_large", j)

drop = copy.deepcopy(daily_tpl["tasks"][0])  # simulate_filedrops, on serverless
dbt_vars = ('dbt run --vars \'{"batch_date": "{{job.parameters.batch_date}}", '
            '"scale_factor": "{{job.parameters.scale_factor}}", "wh_db": "{{job.parameters.wh_db}}", '
            '"tpcdi_directory": "{{job.parameters.tpcdi_directory}}", "catalog": "{{job.parameters.catalog}}"}\'')
add("daily_wh_large", {
    "name": "etl-benchmark-daily-wh_large", "tags": {"config": "wh_large", "test": "daily", "engine": "dbt"},
    "performance_target": "PERFORMANCE_OPTIMIZED",
    "parameters": daily_params("etl_daily_wh_large")[:5],
    "environments": [{"environment_key": "dbt", "spec": {"client": "5", "dependencies": ["dbt-databricks==1.11.7"]}}],
    "tasks": [drop, {
        "task_key": "dbt_run", "depends_on": [{"task_key": "simulate_filedrops"}], "environment_key": "dbt",
        "dbt_task": {"project_directory": "${var.tpcdi_path}/src/incremental_batches/augmented_incremental/dbt",
                     "commands": ["dbt deps", dbt_vars], "schema": f"etl_daily_wh_large_{SF}",
                     "warehouse_id": "${resources.sql_warehouses.wh_large.id}", "catalog": CATALOG,
                     "source": "WORKSPACE"},
        "max_retries": 3, "min_retry_interval_millis": 15000, "retry_on_timeout": True}]})

# ---------- Spark Declarative Pipelines ----------
SDP_CLUSTER = [{"label": "default", "node_type_id": "m8gd.2xlarge", "driver_node_type_id": "m8gd.2xlarge",
                "autoscale": {"min_workers": 1, "max_workers": 8, "mode": "ENHANCED"},
                "spark_conf": {"spark.sql.shuffle.partitions": "auto"},
                "aws_attributes": {"availability": "ON_DEMAND", "first_on_demand": 1, "zone_id": "auto"}}]
for x, serverless in (("serverless", True), ("2xlarge", False)):
    for test in ("full", "daily"):
        p = copy.deepcopy(sdp_tpl[test])
        conf = p["configuration"]
        conf["scale_factor"] = SF
        p.update(name=f"etl-benchmark-{test}-sdp_{x}", catalog=CATALOG,
                 target=f"etl_{test}_sdp_{x}_{SF}", serverless=serverless)
        if test == "daily":
            conf["wh_db"] = f"etl_daily_sdp_{x}"
        if not serverless:
            p["clusters"] = SDP_CLUSTER
            p["edition"] = "PRO" if test == "full" else "ADVANCED"
        RES["pipelines"][f"pl_{test}_sdp_{x}"] = p
    pid = "${resources.pipelines.pl_%s_sdp_%s.id}"
    add(f"full_sdp_{x}", {"name": f"etl-benchmark-full-sdp_{x}", "tags": {"config": f"sdp_{x}", "test": "full"},
                          "tasks": [{"task_key": "pipeline", "pipeline_task": {"pipeline_id": pid % ("full", x), "full_refresh": True}}]})
    drop = copy.deepcopy(daily_tpl["tasks"][0])
    add(f"daily_sdp_{x}", {
        "name": f"etl-benchmark-daily-sdp_{x}", "tags": {"config": f"sdp_{x}", "test": "daily"},
        "performance_target": "PERFORMANCE_OPTIMIZED", "parameters": daily_params(f"etl_daily_sdp_{x}")[:5],
        "tasks": [drop, {"task_key": "pipeline", "depends_on": [{"task_key": "simulate_filedrops"}],
                         "pipeline_task": {"pipeline_id": pid % ("daily", x), "full_refresh": False}}]})
    # daily setup for SDP: Shannon's flow (setup, load history in the pipeline, switch it to incremental)
    swap = lambda flag: {"task_key": f"set_pipeline_{'historical' if flag == 'true' else 'incremental'}",
                         "notebook_task": {"notebook_path": "${var.tpcdi_path}/src/incremental_batches/augmented_incremental/DLT/update_pipeline_notebook",
                                           "base_parameters": {"historical_flag": flag, "pipeline_id": pid % ("daily", x)}}}
    s0 = copy.deepcopy(daily_tpl["sdp_setup"])
    h, i = swap("true"), swap("false")
    h["depends_on"] = [{"task_key": "setup"}]
    run_h = {"task_key": "run_historical_pipeline", "depends_on": [{"task_key": h["task_key"]}],
             "pipeline_task": {"pipeline_id": pid % ("daily", x), "full_refresh": True}}
    i["depends_on"] = [{"task_key": "run_historical_pipeline"}]
    add(f"daily_setup_sdp_{x}", {"name": f"etl-benchmark-daily-setup-sdp_{x}", "tags": {"test": "setup"},
                                 "performance_target": "PERFORMANCE_OPTIMIZED",
                                 "parameters": daily_params(f"etl_daily_sdp_{x}"), "tasks": [s0, h, run_h, i]})

# ---------- shared daily setup and teardown (serverless, not timed) ----------
for name, task_key, nb in (("daily_setup", "setup", None), ("daily_setup_dbt", "setup", "setup_dbt"),
                           ("daily_teardown", "teardown", None)):
    t = copy.deepcopy(daily_tpl["teardown" if name == "daily_teardown" else "setup"])
    t.pop("depends_on", None)
    t.pop("run_if", None)
    if nb:
        t["notebook_task"]["notebook_path"] = t["notebook_task"]["notebook_path"].rsplit("/", 1)[0] + "/" + nb
    add(name, {"name": f"etl-benchmark-{name.replace('_', '-')}", "tags": {"test": "setup"},
               "performance_target": "PERFORMANCE_OPTIMIZED", "max_concurrent_runs": 20,
               "parameters": daily_params(""), "tasks": [t]})

out = {"resources": {k: v for k, v in RES.items() if v}}
(root / "resources/benchmark.yml").write_text(
    "# GENERATED by scripts/gen_resources.py. Edit the script, not this file.\n"
    + yaml.safe_dump(out, sort_keys=False, width=200))
print(len(RES["jobs"]), "jobs,", len(RES["pipelines"]), "pipelines")
