# Load test with todos

This is a simple crud todos to try out some optimizations

Simple call create todos and get all todos (order by created at).
Load test is perform by locust with read-write ratio: 6:4
Peak concurrent: 50
Users/second: 5
Connection pool: 25, overflow 5 (max 30)
A table truncate is performed before any test


## Simple, no index: RPS: 21.95

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1571         |0            |2400                |2335.308720560153    |12               |5598             |71875.68300445576   |13.091874600342026|0.0       |2400|3200|3600|3700|4100|4500|4800|5000|5500 |5600  |5600|
|POST|/todos/   |1064         |0            |1800                |1831.6475563909773   |20               |4349             |136.0               |8.866807495075694 |0.0       |1800|2500|2800|3000|3300|3600|3900|4100|4300 |4300  |4300|
|    |Aggregated|2635         |0            |2100                |2131.9328273244782   |12               |5598             |42907.55294117647   |21.95868209541772 |0.0       |2100|2800|3300|3500|3900|4200|4700|4800|5500 |5600  |5600|


## created_at index: RPS: 21.94

```
CREATE INDEX idx_todomodel_created_at ON todos (created_at DESC);
```

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1578         |0            |2300                |2375.491761723701    |10               |5333             |72632.35994930292   |13.162817570236198|0.0       |2300|3200|3600|3900|4400|4700|5000|5100|5300 |5300  |5300|
|POST|/todos/   |1053         |0            |1800                |1819.1006647673314   |19               |4802             |136.0               |8.783553169492217 |0.0       |1800|2400|2700|3000|3500|3800|4000|4200|4300 |4800  |4800|
|    |Aggregated|2631         |0            |2100                |2152.8084378563285   |10               |5333             |43617.2831622957    |21.946370739728415|0.0       |2100|2800|3300|3500|4100|4500|4800|5000|5300 |5300  |5300|

It's really unexpect that postgresql will not use the index and just perform a seq scan, because most records(infact all of them) is fetch, so index does not make any diffirent here.
Also, index overhead is not a problem with a couple hundreds of records.

```sql
EXPLAIN SELECT * FROM todos ORDER BY created_at DESC;
                           QUERY PLAN                           
----------------------------------------------------------------
 Sort  (cost=145.88..148.56 rows=1075 width=48)
   Sort Key: created_at DESC
   ->  Seq Scan on todos  (cost=0.00..91.75 rows=1075 width=48)
(3 rows)
```

## Replication

### Write ahead logs(WAL)

- Write ahead logs is a pattern to ensure ACID property of database. Basiclly you write logs before make any changes to database. So incase of failure, you can just "replay" the logs to database to recover the database.

So master-slave thing all really is just shiping WAL files around. Each time a transaction is committed, a WAL is created and shiped to slaves.
This can be configed to sent in batch or each of them if needed.

If master database crash during an uncommited transaction, there will be **dataloss** when promote slave to master.

[![](https://mermaid.ink/img/pako:eNp9j01PwzAMhv9K5NMmtVWakLTNAQmJ47iwAxILB9NmbFrTTkkKjKr_nWxwAGmqD35tP5Y_Rqj7xoCCbdt_1Dt0gawedUeiWfTBuM3i4aKkwYCv6M3y5Qf7Ft9Nvlmsz3qdslnKr9G_q0makqe7lY96-7tuHrN5zCEBa5zFfRMfHs_NGsLOWKNBxbBBd9Cguyn24RD69amrQQU3mASGY7zS3O_xzaEFtcXWx-oRu-e-_5eDGuETFCtExkopWU4rXogETqDSvMpiKigty-iqQsopga_LAJpVQjDOWXQ5vWFy-gZilH1v?type=png)](https://mermaid.live/edit#pako:eNp9j01PwzAMhv9K5NMmtVWakLTNAQmJ47iwAxILB9NmbFrTTkkKjKr_nWxwAGmqD35tP5Y_Rqj7xoCCbdt_1Dt0gawedUeiWfTBuM3i4aKkwYCv6M3y5Qf7Ft9Nvlmsz3qdslnKr9G_q0makqe7lY96-7tuHrN5zCEBa5zFfRMfHs_NGsLOWKNBxbBBd9Cguyn24RD69amrQQU3mASGY7zS3O_xzaEFtcXWx-oRu-e-_5eDGuETFCtExkopWU4rXogETqDSvMpiKigty-iqQsopga_LAJpVQjDOWXQ5vWFy-gZilH1v)


There is 2 types of slave replicas, file archirved and Streamming. They both have pros and cons and can work together.

- File archived: Easier to config, better availibility, required 3rd server to save WAL logs, takes more bandwith
- Streamming: Hard to config, less bandwith.

### Result

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1613         |0            |2200                |2280.06385616863     |8                |5919             |78086.55424674519   |13.470618475197266|0.0       |2200|2900|3400|3800|4500|4800|5100|5200|5700 |5900  |5900|
|POST|/todos/   |1142         |0            |1700                |1731.8345008756567   |22               |4736             |135.0306479859895   |9.537164475310155 |0.0       |1700|2200|2600|2800|3500|3700|4000|4200|4700 |4700  |4700|
|    |Aggregated|2755         |0            |2000                |2052.812341197822    |8                |5919             |45774.16225045372   |23.00778295050742 |0.0       |2000|2600|3000|3300|4000|4600|4900|5100|5600 |5900  |5900|

Seems slightly better than without slave?


I try to route read query to slave replica and write query to write replica. A little better than old version.

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1779         |0            |2300                |2086.167509836987    |10               |4997             |78399.50140528387   |14.850802609073337|0.0       |2300|2700|2900|3100|3600|4000|4400|4600|4900 |5000  |5000|
|POST|/todos/   |1194         |0            |1800                |1658.7303182579565   |19               |4133             |136.0               |9.967317771351077 |0.0       |1800|2100|2400|2500|2800|3100|3400|3700|4000 |4100  |4100|
|    |Aggregated|2973         |0            |2000                |1914.502522704339    |10               |4997             |46967.74201143626   |24.818120380424414|0.0       |2000|2500|2700|2900|3300|3800|4200|4500|4800 |5000  |5000|

So I try to increase the peak concurrency to 70, 10/s. Statisics is the same, no considerable improvements.

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1762         |0            |3100                |3019.116345062429    |23               |7321             |76694.49035187287   |14.68658207516257 |0.0       |3100|3600|4400|4700|5300|5800|6300|6700|7300 |7300  |7300|
|POST|/todos/   |1122         |0            |2400                |2360.134581105169    |35               |5545             |136.0               |9.352068722095575 |0.0       |2400|3000|3400|3700|4200|4600|5000|5100|5500 |5500  |5500|
|    |Aggregated|2884         |0            |2900                |2762.744105409154    |23               |7321             |46909.945908460475  |24.038650797258146|0.0       |2900|3400|3900|4300|5000|5500|6100|6500|7200 |7300  |7300|

Change route handler to async

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99%  |99.9%|99.99%|100% |
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|-----|-----|------|-----|
|GET |/todos/   |1980         |0            |1600                |1595.4757575757576   |7                |3591             |93617.87525252525   |16.509711939098867|0.0       |1600|2000|2300|2400|2800|3100|3300|3400 |3600 |3600  |3600 |
|POST|/todos/   |1385         |0            |1900                |1823.8519855595669   |19               |4819             |136.0               |11.548460119016127|0.0       |1900|2300|2600|2800|3300|3600|3900|4400 |4800 |4800  |4800 |
|    |Aggregated|3365         |0            |1600                |1689.4731054977713   |7                |4819             |55141.67994056464   |28.058172058114994|0.0       |1600|2100|2400|2600|3000|3300|3700|3900 |4500 |4800  |4800 |

