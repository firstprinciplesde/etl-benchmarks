# Conclusions

Source: [results/final_table.md](../results/final_table.md). One run per cell.

| Setup | SF 100 min / $ | SF 1,000 min / $ | SF 10,000 min / $ |
|---|---|---|---|
| Serverless standard | 51.1 / 0.75 | 48.0 / 1.62 | 96.0 / 7.52 |
| Serverless optimized | 18.3 / 1.46 | 25.6 / 5.43 | 56.9 / 14.11 |
| Serverless cap S | 19.6 / 1.56 | 26.4 / 5.24 | 49.6 / 11.81 |
| Serverless cap M | 19.4 / 1.58 | 25.7 / 5.15 | 40.7 / 11.14 |
| Job cluster xlarge | 38.5 / 0.99 | 48.2 / 1.60 | 142.0 / 7.71 |
| Job cluster 2xl | 42.3 / 1.78 | 44.3 / 2.74 | 85.3 / 6.62 |
| 2xl spot | 48.3 / 1.46 | 48.9 / 1.98 | 88.6 / 4.63 |
| 2xl no Photon | 37.3 / 1.58 | 64.0 / 3.12 | 210.2 / 16.91 |
| 2xl min 2 workers | 30.1 / 2.23 | 35.4 / 3.23 | 78.7 / 6.99 |
| 8xl | 27.7 / 5.61 | 31.2 / 7.34 | 53.5 / 13.00 |
| All-purpose 2xl | 32.0 / 3.49 | 36.9 / 5.57 | 72.6 / 13.71 |
| Warehouse (serverless L) | 17.0 / 11.27 | 17.7 / 9.02 | 30.8 / 13.44 |

## Conclusions by section
Cost is Databricks plus AWS list price, one combined number per size: the full load plus six days.

### 1. Overall
- **Cheapest: serverless standard, or close to it at every size.** You don't have to size or tune anything. SF 100: $0.75, the lowest. SF 1,000: $1.62, level with the cheapest classic job ($1.60). SF 10,000: $7.52, a bit above a small cluster on spot ($4.63, estimated).
- **Fast with a cost limit: the serverless size caps** (S to XL). Same speed as performance optimized at SF 100 and 1,000, and cheaper than optimized at SF 10,000 (medium 40.7 min, $11.14 vs 56.9 min, $14.11).
- **Fastest regardless of price: the SQL warehouse**, at every size.
- **Never worth it:** all-purpose for scheduled jobs, Photon off, an 8xlarge job cluster, classic pipelines.

### 2. Serverless
- **Standard:** cheapest, but about 40% of its time is waiting for compute (19.5 of 48.0 min at SF 1,000, about 2 to 3.4 min per run).
- **Performance optimized:** about 2x faster than standard for 3.4x the cost at SF 1,000 (25.6 vs 48.0 min, $5.43 vs $1.62); the priciest serverless job at SF 10,000.
- **Size caps:** the cap jobs run in performance optimized mode (the job page shows Performance optimized: On, see docs/screenshots), so they start as fast as optimized: idle 0.7 to 2.5 min over seven runs, against 21 to 22.5 for standard. The compute object holds only the size. A cap limits how far the executors can scale (a Beta feature), not the total cost.
- **Pipelines:** serverless pipelines cost about the same as optimized jobs, and are 2x slower at SF 10,000.

### 3. Classic job clusters
- **Spot:** 18 to 30% cheaper in total, 4 to 14% more time (SF 100 +6.0 min, SF 1,000 +4.6, SF 10,000 +3.3). The saving is on the AWS part only. If cost is the goal on classic, use spot.
- **Photon:** off is cheaper at SF 100 ($1.58 vs $1.78), then +14% cost and +45% time at SF 1,000, and 2.6x cost and 2.5x time at SF 10,000. The penalty grows with size.
- **Size and workers:** an 8xlarge loses to serverless optimized on both speed and cost; a worker floor of 2 cuts idle time (13.8 vs 20.5 min) but costs 18% more.
- **All-purpose:** about 2x the cost of a job cluster at every size ($3.49 vs 1.78, 5.57 vs 2.74, 13.71 vs 6.62).
- **Idle:** classic spends 40 to 50% of its time starting up (20.5 of 44.3 min for the 2xlarge at SF 1,000).

### 4. SQL warehouse
- Fastest everywhere: 17.0 / 17.7 / 30.8 min at SF 100 / 1,000 / 10,000.
- Also the most expensive: the priciest setup at SF 100 ($11.27) and SF 1,000 ($9.02), and among the priciest at SF 10,000 ($13.44, behind optimized, all-purpose, no-Photon and classic pipelines at that size).
- Premium shrinks with size: 15x standard at SF 100 ($11.27 vs $0.75), 1.8x at SF 10,000 ($13.44 vs $7.52), about level with optimized ($14.11).
- Its six-day load ran as dbt.

