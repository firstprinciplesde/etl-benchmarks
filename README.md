# etl-benchmarks

**What one ETL pipeline costs, and how long it takes, on each Databricks compute option: 16 setups, 350 runs, a full load plus six days at three data sizes, so you can pick compute from numbers.**

[YouTube channel](https://www.youtube.com/@FirstPrinciplesDE) · [Conclusions](docs/conclusions.md) · [Every run](results/per_run.csv) · [Run it yourself](#run-it-yourself) · [License](LICENSE)

## The answer

- **Cheapest:** serverless standard, or close to it at every size. Nothing to size or tune. The cost is waiting: about 40% of its time is waiting for compute.
- **Fast, with a limit on spend:** a serverless size cap. As fast as performance optimized at SF 100 and 1,000, and better at SF 10,000 (medium: 41 min for $11.14, against 57 min for $14.11).
- **Fastest:** the SQL warehouse, at every size. A Large warehouse was also the most expensive in these runs, and it ran at Large for every size.
- **On classic job clusters:** spot is 18 to 30% cheaper in total for 4 to 14% more time. Photon off was slower and dearer at SF 1,000 and 10,000. All-purpose cost about double a job cluster. Never run scheduled jobs on all-purpose.

The reasoning for each is in [docs/conclusions.md](docs/conclusions.md).

## Results

Each cell is the **full load plus six days** added together: idle minutes (waiting) + run minutes (working) = total minutes, and cost (Databricks plus AWS list price). Every cell is one run.

| Setup | SF 100 | SF 1,000 | SF 10,000 |
|---|---|---|---|
| SQL warehouse, serverless Large | 1 + 16 = **17** min · **$11.27** | 1 + 17 = **18** min · **$9.02** | 1 + 30 = **31** min · **$13.44** † |
| Serverless, standard | 21 + 30 = **51** min · **$0.75** | 20 + 28 = **48** min · **$1.62** | 22 + 74 = **96** min · **$7.52** |
| Serverless, performance optimized | 1 + 18 = **18** min · **$1.46** | 1 + 25 = **26** min · **$5.43** | 1 + 56 = **57** min · **$14.11** |
| Serverless, cap S | 2 + 18 = **20** min · **$1.56** | 2 + 24 = **26** min · **$5.24** | 1 + 49 = **50** min · **$11.81** |
| Serverless, cap M | 2 + 18 = **19** min · **$1.58** | 1 + 24 = **26** min · **$5.15** | 1 + 40 = **41** min · **$11.14** |
| Serverless, cap L | 1 + 18 = **19** min · **$1.71** | 3 + 23 = **26** min · **$5.44** | 1 + 47 = **48** min · **$10.65** |
| Serverless, cap XL | 1 + 18 = **18** min · **$1.65** | 1 + 25 = **26** min · **$4.90** | 1 + 40 = **41** min · **$11.89** |
| Job cluster, xlarge | 18 + 20 = **38** min · **$0.99** | 17 + 31 = **48** min · **$1.60** | 38 + 104 = **142** min · **$7.71** † |
| Job cluster, 2xlarge | 24 + 18 = **42** min · **$1.78** | 20 + 24 = **44** min · **$2.74** | 25 + 60 = **85** min · **$6.62** † |
| 2xlarge, workers on spot | 30 + 18 = **48** min · **$1.46** | 26 + 23 = **49** min · **$1.98** | 26 + 63 = **89** min · **$4.63** † |
| 2xlarge, Photon off | 14 + 24 = **37** min · **$1.58** | 24 + 40 = **64** min · **$3.12** | 26 + 184 = **210** min · **$16.91** † |
| 2xlarge, 2 to 8 workers | 13 + 17 = **30** min · **$2.23** | 14 + 22 = **35** min · **$3.23** | 31 + 48 = **79** min · **$6.99** † |
| Job cluster, 8xlarge | 11 + 16 = **28** min · **$5.61** | 12 + 19 = **31** min · **$7.34** | 24 + 30 = **54** min · **$13.00** † |
| All-purpose cluster, 2xlarge | 14 + 18 = **32** min · **$3.49** | 13 + 24 = **37** min · **$5.57** | 10 + 62 = **73** min · **$13.71** † |
| Pipeline, serverless | 1 + 20 = **20** min · **$1.57** | 1 + 28 = **28** min · **$4.55** | 1 + 108 = **108** min · **$14.95** † |
| Pipeline, classic 2xlarge | 1 + 41 = **42** min · **$3.45** | 1 + 55 = **56** min · **$5.80** | 1 + 141 = **141** min · **$18.63** † |

† SF 10,000 classic, warehouse and pipeline costs are estimates from smaller sizes, see [docs/cost-provenance.md](docs/cost-provenance.md). Per-setup detail (full load and an average day, separately): [results/final_table.md](results/final_table.md).

> [!IMPORTANT]
> One run per cell, so don't trust a two percent gap. AWS costs are node-hours times a price list, not Cost Explorer. Warehouse and all-purpose per-run costs are hourly billing divided between runs by time. This is derived from TPC-DI, not an official TPC-DI result, and is not comparable to published results.

## What was tested

| Group | Setups |
|---|---|
| Serverless jobs | `srv_standard`, `srv_optimized`, `srv_small`, `srv_medium`, `srv_large`, `srv_xlarge` (size caps) |
| Job cluster (m8gd, 1 to 8 workers, driver on demand) | `jc_xlarge`, `jc_2xlarge`, `jc_8xlarge` |
| 2xlarge experiments | `jc_2xlarge_spot`, `jc_2xlarge_nophoton`, `jc_2xlarge_min2`, `ap_2xlarge` (all-purpose) |
| SQL warehouse | `wh_large` (serverless, Large) |
| Pipelines | `sdp_serverless`, `sdp_2xlarge` (Spark Declarative Pipelines) |

Two tests per setup and size: a **full load** (the original TPC-DI single batch, whole job with start-up) and **six days** in a row (each day its own cold run, so every day pays its own start-up). The warehouse's six days ran as dbt, with the SQL on the warehouse, because a warehouse can't run the Python streaming notebooks. Data sizes: SF 100 (about 10 GB), SF 1,000 (about 100 GB), SF 10,000 (about 1 TB). Region: AWS us-east-1.

## How it was set up

The workload is **[Shannon Barrow's databricks-tpc-di](https://github.com/shannon-barrow/databricks-tpc-di)**, a Databricks implementation of TPC-DI (a retail brokerage ETL benchmark). All the credit goes to him. His code runs unchanged; this repo adds the Databricks Asset Bundle that creates one job per setup, the cold-start rules, and the measurement.

> [!NOTE]
> This is derived from TPC-DI. It is not comparable to published TPC-DI results because it does not meet all of the benchmark's requirements, and no TPC metric is reported.

How each run is made fair:

1. **Cold start every time.** Job clusters are new per run. The warehouse is stopped and the all-purpose cluster terminated before each run. Serverless has no off switch, so its start-up is whatever Databricks gives you.
2. **Same data and code** for every setup. Photon is on except where tested off, workers are on demand except where tested on spot, and the driver is always on demand.
3. **Idle counts.** The warehouse bills until auto-stop (5 minutes) and the all-purpose cluster until auto-termination (10 minutes), so cost includes that tail.
4. **Cost** is Databricks list price (`system.billing.usage` times `system.billing.list_prices`) plus AWS node-hours times a price list for classic compute.

What it looked like in the workspace:

![The jobs list: one job per setup, run as a bundle](docs/screenshots/01-jobs-list-all-configs.png)

| One setup's run history | One run's 17-task graph |
|---|---|
| ![Run history of one serverless cap job](docs/screenshots/02-job-run-history-srv_large.png) | ![The 17 tasks of one run](docs/screenshots/03-run-graph-17-tasks.png) |

| Serverless size caps (Beta) | Creating one |
|---|---|
| ![The serverless compute objects](docs/screenshots/04-serverless-compute-sizes-list.png) | ![The size options](docs/screenshots/06-create-serverless-size-options.png) |

More: [a cap's detail page](docs/screenshots/05-serverless-large-details.png), [the benchmark schemas in the catalog](docs/screenshots/07-catalog-schemas.png). The build log and the checks against Databricks docs are in [docs/how-it-was-built.md](docs/how-it-was-built.md).

## Run it yourself

> [!WARNING]
> Running all of it costs real money: the whole benchmark was about $525 at list price. Start with one setup at SF 100. I could not re-run these commands on a clean workspace after the benchmark, so treat the steps as the shape of the setup, not a tested recipe.

1. Import the [databricks-tpc-di](https://github.com/shannon-barrow/databricks-tpc-di) repo into your workspace and generate the data for your scale factor with its Driver notebook, once per size.
2. Create the serverless size compute objects (Beta, enabled by an admin on the Previews page) and put their IDs in `databricks/scripts/serverless_ids.json`.
3. Generate and deploy the bundle, then run a job by its key:

```bash
cd databricks
python3 scripts/gen_resources.py
databricks bundle deploy -p <profile> --var tpcdi_path=/Workspace/Users/<you>/databricks-tpc-di --var scale_factor=100
databricks bundle run full_srv_standard -p <profile> --var tpcdi_path=/Workspace/Users/<you>/databricks-tpc-di
```

Job keys are `full_<setup>` and `daily_<setup>`; run `daily_<setup>` six times for the six days, after `daily_setup`. See [databricks/README.md](databricks/README.md).

## What's inside

| Path | What |
|---|---|
| [`docs/conclusions.md`](docs/conclusions.md) | The conclusions, by section |
| [`docs/design.md`](docs/design.md) | How the benchmark was designed |
| [`docs/cost-provenance.md`](docs/cost-provenance.md) | Where each cost number came from |
| [`docs/how-it-was-built.md`](docs/how-it-was-built.md) | What was done, in order, and what was checked |
| [`results/`](results/) | `final_table.md` and `per_run.csv` (350 runs) |
| [`databricks/`](databricks/) | The bundle and the generator |
| [`scripts/check_numbers.py`](scripts/check_numbers.py) | Recomputes the headline numbers from the results table |

## License

[MIT](LICENSE).
