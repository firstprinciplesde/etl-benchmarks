# Benchmark design

Question: **for an ETL pipeline on Databricks, which compute gives you the best time for the money, for a full load plus six days?**

## 1. Workload

Every config runs two separate tests at each scale factor.

| Test | What runs | What we time |
|---|---|---|
| **Full load** | Original TPC-DI single batch: all raw files (CSV, text, XML) to the finished star schema, Batch 1 history plus Batches 2 and 3 | Whole job, cold start included |
| **Six days** | Shannon's augmented incremental mode: start from the loaded warehouse, then 6 days in a row. Each day drops that day's files, Auto Loader into bronze, then the SCD2 and fact MERGEs | Each day on its own, cold start included. Report the average day and the six-day total |

The daily test's starting state (a clone of the staged history) is setup, not benchmark, so it is not timed. Each day is its own job run, triggered like a daily schedule, so every day pays its own start-up, the same as in production.

Scale factors: **SF 100, SF 1,000 and SF 10,000.**

## 2. Configs (16)

Compute is the main axis. Engine is the second, because how you build the ETL decides which compute you can even use.

| # | Config | Engine | Compute |
|---|---|---|---|
| 1 | `srv_standard` | SQL notebooks (job) | Serverless, standard mode |
| 2 | `srv_optimized` | SQL notebooks (job) | Serverless, performance optimized |
| 3-6 | `srv_small`, `srv_medium`, `srv_large`, `srv_xlarge` | SQL notebooks (job) | Serverless with a size limit (the `vid12-bench-serverless-*` objects) |
| 7 | `jc_xlarge` | SQL notebooks (job) | Job cluster m8gd.xlarge, 1 to 8 workers |
| 8 | `jc_2xlarge` | SQL notebooks (job) | Job cluster m8gd.2xlarge, 1 to 8 workers |
| 9 | `jc_8xlarge` | SQL notebooks (job) | Job cluster m8gd.8xlarge, 1 to 8 workers (quota caps it near 4) |
| 10 | `jc_2xlarge_spot` | SQL notebooks (job) | Same as 8, workers on spot |
| 11 | `jc_2xlarge_nophoton` | SQL notebooks (job) | Same as 8, Photon off |
| 12 | `jc_2xlarge_min2` | SQL notebooks (job) | Same as 8, 2 to 8 workers |
| 13 | `ap_2xlarge` | SQL notebooks (job) | All-purpose cluster, same shape as 8 |
| 14 | `wh_large` | Full load: SQL notebooks. Daily: dbt | SQL warehouse, serverless Large |

The warehouse can't run the daily Python streaming notebooks, and Shannon's repo only wires dbt for the daily mode. So the warehouse gets the engine it would really use for each test.

All the code comes from [shannon-barrow/databricks-tpc-di](https://github.com/shannon-barrow/databricks-tpc-di), unchanged. Within an engine, every compute runs identical code.

## 3. Fairness rules

1. **Cold start for every run, every day.** The warehouse is STOPPED and the all-purpose cluster TERMINATED before each run, and checked again just before the job starts. Job clusters are always new. Serverless has no off switch, so its start-up is whatever Databricks gives you, and the write-up says so.
2. **Same data and code** per engine. DBR 18.x everywhere, Photon on everywhere except config 11, on-demand everywhere except config 10, and the driver the same type as the workers.
3. **Idle cost counts.** A warehouse bills until auto-stop, and an all-purpose cluster until auto-termination. Real daily jobs pay that tail, so cost includes it. Auto-stop is 5 min on the warehouse and 10 min on the cluster.
4. **One run per test.** Single runs, stated plainly in the write-up.
5. **No overlap on classic.** Classic configs run one at a time (128 vCPU quota). Serverless and warehouse runs go in parallel, since they don't share compute.
6. **Untimed:** data generation, the daily-test setup clone, and cleanup.

## 4. What we measure

| Metric | Source |
|---|---|
| Total time, start-up, processing | Jobs API task timings |
| DBUs | `system.billing.usage` by job run, pipeline or warehouse, plus the idle tail |
| Databricks $ | DBUs × `system.billing.list_prices` |
| AWS $ (classic only) | Node-hours from cluster events × EC2 on-demand price (spot price for config 10) |
| **Cost per full load, cost per day, cost per six days** | Derived |

Billing data lags a few hours, so the cost columns fill in after the runs.

## 5. Order and budget

1. **SF100**, all 16 configs, both tests. This is the smoke test, and it also gives the "small job" numbers.
2. **SF1000**, all 16, both tests. This is the main result.
3. **SF10000**: an estimate from SF1000 first. It's roughly 10x the data, so classic runs take hours and AWS likely goes past the $20 cap. It runs once the cost is cleared.

AWS spend for steps 1 and 2 should be about $10 to $15. DBUs show up on the Databricks bill, not AWS.

## 6. Output

One table per scale factor, plus the answer in one line each:
- **Best for a big load:** fastest, and cheapest per load.
- **Best for six days of loads:** cheapest at an acceptable time.
- **When each compute makes sense,** .
