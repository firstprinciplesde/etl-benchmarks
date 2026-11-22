# Databricks bundle

One job per benchmark setup, plus the shared setup and teardown jobs, the pipelines, the warehouse and the all-purpose cluster.

## Deploy

1. Import the [databricks-tpc-di](https://github.com/shannon-barrow/databricks-tpc-di) repo into your workspace and generate its data for your scale factor, once per size.
2. Create the four serverless size compute objects (Beta) and put their IDs in [`scripts/serverless_ids.json`](scripts/serverless_ids.json). The file holds placeholders.
3. Generate the resources, deploy once per scale factor, and run a job by its key:

```bash
python3 scripts/gen_resources.py            # needs pyyaml
databricks bundle deploy -p <profile> --var tpcdi_path=/Workspace/Users/<you>/databricks-tpc-di --var scale_factor=100
databricks bundle run full_jc_2xlarge -p <profile> --var tpcdi_path=/Workspace/Users/<you>/databricks-tpc-di
```

## Job keys

| Key | What |
|---|---|
| `full_<setup>` | The full load, for `srv_standard`, `srv_optimized`, `srv_small` to `srv_xlarge`, `jc_xlarge`, `jc_2xlarge`, `jc_8xlarge`, `jc_2xlarge_spot`, `jc_2xlarge_nophoton`, `jc_2xlarge_min2`, `ap_2xlarge`, `wh_large`, `sdp_serverless`, `sdp_2xlarge` |
| `daily_<setup>` | One simulated day. Run it six times, in order |
| `daily_setup`, `daily_setup_dbt`, `daily_setup_sdp_*` | Untimed setup for the six days |
| `daily_teardown` | Cleanup |

`resources/benchmark.yml` is generated. Don't edit it: change `scripts/gen_resources.py` or the templates and run the generator again. The generator uses the catalog `firstprinciplesde` and its volume path; change `CATALOG` and `VOL` at the top for your own.

> [!NOTE]
> I could not re-run these steps on a clean workspace after the benchmark finished.
