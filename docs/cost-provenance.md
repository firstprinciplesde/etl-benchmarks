# Where each cost number came from 

per_run.csv was built when billing was complete up to 2026-11-22 01:10 UTC (a run counts as pending if it ended after 00:10 UTC). workspace_costs.txt is a later pull (complete up to 06:10 UTC).

## Databricks cost
| Rows | Source |
|---|---|
| basis=exact (SF 100 and 1,000 serverless jobs, classic job clusters, the serverless file-drop task; SF 10,000 serverless jobs: 42 rows) | DBUs summed from `system.billing.usage` by `job_run_id`, times `system.billing.list_prices` (`pricing.default`, joined on SKU and the usage end time inside the price window). Not estimated. |
| sdp_2xlarge (classic pipeline) | read from the table by the pipeline's cluster id (`dlt-execution-*`), assigned to the run whose window holds the cluster's first node minute |
| basis=split (wh_large, ap_2xlarge at SF 100 and 1,000; a small part of sdp_serverless) | read from hourly `system.billing.usage` rows by warehouse or cluster id, divided between runs by overlap seconds (tail 5 min warehouse, 10 min all-purpose). Hourly totals are right; per-run values are allocations (a run can absorb idle minutes of its hour, e.g. wh_large SF 100 full load $3.87 for 2 min) |
| SF 10,000 basis=estimated (59 rows: classic jc_*, ap_2xlarge, sdp_2xlarge, sdp_serverless, wh_large six-day runs) | NOT in billing yet. Classic and all-purpose: node-minutes (`system.compute.node_timeline`) times a measured Databricks $ per node-minute from the same config's SF 100 and 1,000 runs. Warehouse and serverless pipelines: run minutes times a measured $ per minute from SF 100 and 1,000. These rates may understate DBU use at SF 10,000. |
| SF 10,000 basis=extrapolated (jc_2xlarge_min2 and jc_8xlarge, 10 rows) | compute tables had no node time yet; the config's SF 1,000 cost scaled by run-minute ratio; only full load and day 1 were run, days 2 to 6 repeat day 1. jc_8xlarge is the weakest number. |

Not in any per-run cost: setup and teardown jobs (only in workspace_costs.txt).

## AWS cost
Every row, including exact ones: node time times an EC2 on-demand price list, NOT Cost Explorer. Node time = rows in `node_timeline` counted as 1 minute each (not checked). Prices from a pricing page: m8gd.xlarge $0.231, 2xlarge $0.461, 8xlarge $1.845 an hour. Spot workers use one spot sample ($0.111 an hour), driver on demand; the table has no market column, so workers are assumed spot. Serverless and warehouse rows have ec2_usd = 0. The account's own EC2 total by node time was about $66.

## What it means for the conclusions
- Solid: SF 100 and 1,000 Databricks costs (read from system tables); all serverless job results at every size, including SF 10,000.
- Allocated but right in total: warehouse and all-purpose per-run costs at SF 100 and 1,000 (the combined table sums seven runs, hourly totals are right).
- Estimates: every SF 10,000 classic, warehouse and pipeline cost, and all EC2 costs. The SF 10,000 rates were measured at smaller sizes and may understate, so "spot on a 2xlarge is the cheapest at SF 10,000" and the Photon-off 2.6x at SF 10,000 are the weakest claims; the serverless numbers they are compared with are exact.
- These estimates were not refreshed once billing landed.
