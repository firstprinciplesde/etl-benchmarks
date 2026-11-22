# How it was built

In order, short.

1. **Workload.** Shannon Barrow's [databricks-tpc-di](https://github.com/shannon-barrow/databricks-tpc-di), run unchanged, in two modes: the original single batch (the full load) and his augmented incremental mode (one simulated day at a time, six days in a row).
2. **Bundle.** `databricks/scripts/gen_resources.py` generates `databricks/resources/benchmark.yml`: one job per setup for the full load and one for a day, the pipelines, the warehouse and the all-purpose cluster. Templates in `databricks/scripts/` come from the TPC-DI repo's own Driver output with the repo path swapped for a bundle variable.
3. **Serverless size caps.** Created as serverless automated compute objects (Small to X-Large, a Beta feature), each attached to jobs through `job_clusters` with a `serverless_compute` policy. A job on a cap runs performance optimized: the job page shows Performance optimized: On.
4. **Cold starts.** Every run starts cold, and the setup that creates each day's starting state is a separate untimed job.
5. **Measurement.** Timings from the Jobs API; DBUs from `system.billing.usage` by job run id, by pipeline cluster, or by warehouse and cluster id split over time; Databricks dollars from `system.billing.list_prices`; AWS dollars from node-hours times a price list.
6. **Fixes along the way.** The warehouse first ran at the wrong size because the size has to be set on the notebook task, not only the job; parallel runs on one job and schema contaminated each other, so every run got its own schema; a stalled serverless start was fixed by pinning an explicit serverless environment version; Photon on the jobs service needs a runtime engine setting and the right runtime key.
7. **Sizes.** SF 100, 1,000 and 10,000 for both tests. SF 10 was used for smoke tests only and is not in the results.

## Checked against Databricks docs and other benchmarks

The product claims behind the conclusions were checked against the Databricks AWS docs, Databricks blog posts and independent benchmarks (Capital One Software, Sync Computing). What came back:

| Claim | Result |
|---|---|
| Serverless modes: optimized starts under a minute, standard typically 4 to 6 minutes, same price per DBU, fewer DBUs for standard | Confirmed in the docs; "up to 70% cheaper" is a Databricks maximum |
| Size caps | A Beta rate limit on executor autoscaling, not a spend budget |
| Photon on by default on classic | Confirmed. The one independent on/off test (SQL, not ETL) found Photon off slightly cheaper, which differs from the result here |
| Spot | Driver on demand; only the AWS part is discounted, so the total saving is smaller than the spot discount |
| All-purpose | Higher DBU rate and billed until it stops; docs advise against it for production jobs |
| SQL warehouse | Starts in seconds; SQL only; dbt runs its SQL on it. Two independent tests found warehouses cheaper per job than serverless jobs; here a Large warehouse was the most expensive, and it ran at Large for every size |
| Scale factor sizes | About 10 GB, 100 GB and 1 TB for SF 100, 1,000 and 10,000 |
| TPC policy | Results must be called "derived from TPC-DI", carry a not-comparable disclaimer, and quote no TPC metric |

These results are one run per cell on one account, so they may differ from independent tests with other workloads.
