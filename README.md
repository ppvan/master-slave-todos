# Load test with todos

This is a simple crud todos to try out some optimizations

Simple call create todos and get all todos (order by created at, limit 200).

Load test is perform by locust with read-write ratio: 6:4

Peak concurrent: 50

Users/second: 5

Connection pool: 25, overflow 5 (max 30)


## Getting started

Just run `docker compose up`. You 'll have api at [http://localhost:8000/](http://localhost:8000/)

and locust webui at [http://localhost:8089/](http://localhost:8089/).

> You might have to run migration.
> ```
> docker compose up migration -d
> ```

## Performance tuning

### Single database, no limit (get all todos in database)

#### No index

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1571         |0            |2400                |2335.308720560153    |12               |5598             |71875.68300445576   |13.091874600342026|0.0       |2400|3200|3600|3700|4100|4500|4800|5000|5500 |5600  |5600|
|POST|/todos/   |1064         |0            |1800                |1831.6475563909773   |20               |4349             |136.0               |8.866807495075694 |0.0       |1800|2500|2800|3000|3300|3600|3900|4100|4300 |4300  |4300|
|    |Aggregated|2635         |0            |2100                |2131.9328273244782   |12               |5598             |42907.55294117647   |21.95868209541772 |0.0       |2100|2800|3300|3500|3900|4200|4700|4800|5500 |5600  |5600|


#### created_at index

```
CREATE INDEX idx_todomodel_created_at ON todos (created_at DESC);
```

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1578         |0            |2300                |2375.491761723701    |10               |5333             |72632.35994930292   |13.162817570236198|0.0       |2300|3200|3600|3900|4400|4700|5000|5100|5300 |5300  |5300|
|POST|/todos/   |1053         |0            |1800                |1819.1006647673314   |19               |4802             |136.0               |8.783553169492217 |0.0       |1800|2400|2700|3000|3500|3800|4000|4200|4300 |4800  |4800|
|    |Aggregated|2631         |0            |2100                |2152.8084378563285   |10               |5333             |43617.2831622957    |21.946370739728415|0.0       |2100|2800|3300|3500|4100|4500|4800|5000|5300 |5300  |5300|

> It's really unexpect that postgresql will not use the index and just perform a seq scan, ? because most records(infact all of them) is fetch, so index does not make any diffirent here.
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

### 1 master, 1 slave, no limit (get all todos in database)

> Code base does take advantage of slave in read queries.

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|----|-----|------|----|
|GET |/todos/   |1779         |0            |2300                |2086.167509836987    |10               |4997             |78399.50140528387   |14.850802609073337|0.0       |2300|2700|2900|3100|3600|4000|4400|4600|4900 |5000  |5000|
|POST|/todos/   |1194         |0            |1800                |1658.7303182579565   |19               |4133             |136.0               |9.967317771351077 |0.0       |1800|2100|2400|2500|2800|3100|3400|3700|4000 |4100  |4100|
|    |Aggregated|2973         |0            |2000                |1914.502522704339    |10               |4997             |46967.74201143626   |24.818120380424414|0.0       |2000|2500|2700|2900|3300|3800|4200|4500|4800 |5000  |5000|

> At this point a try to improve code base performance instead of databse (queries are too simple)

#### Async handler

```py
@app.get("/todos/{id}", response_model=TodoRead, response_class=ORJSONResponse)
async def todo_index(id: int, db_session: Session = Depends(get_session)):
    db_todo = db_session.query(TodoModel).filter(TodoModel.id == id).one()

    return db_todo
```

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99%  |99.9%|99.99%|100% |
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|-----|-----|------|-----|
|GET |/todos/   |1980         |0            |1600                |1595.4757575757576   |7                |3591             |93617.87525252525   |16.509711939098867|0.0       |1600|2000|2300|2400|2800|3100|3300|3400 |3600 |3600  |3600 |
|POST|/todos/   |1385         |0            |1900                |1823.8519855595669   |19               |4819             |136.0               |11.548460119016127|0.0       |1900|2300|2600|2800|3300|3600|3900|4400 |4800 |4800  |4800 |
|    |Aggregated|3365         |0            |1600                |1689.4731054977713   |7                |4819             |55141.67994056464   |28.058172058114994|0.0       |1600|2100|2400|2600|3000|3300|3700|3900 |4500 |4800  |4800 |

> Massive improvement by just using **async**, even more than replication?

#### Faster JSON encoding

Try to use [orjson](https://fastapi.tiangolo.com/advanced/custom-response/#orjsonresponse). Not good as I expected, maybe FastAPI baseline already fast enough?


|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50% |66% |75% |80% |90% |95% |98% |99%  |99.9%|99.99%|100% |
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|----|----|----|----|----|----|----|-----|-----|------|-----|
|GET |/todos/   |1976         |0            |1600                |1642.467105263158    |7                |3850             |92118.3886639676    |16.479856898212184|0.0       |1600|2100|2400|2600|2900|3100|3400|3500 |3800 |3800  |3800 |
|POST|/todos/   |1323         |0            |1900                |1853.148904006047    |18               |5490             |136.0               |11.033831313934574|0.0       |1900|2500|2800|2900|3300|3800|4000|4200 |5000 |5500  |5500 |
|    |Aggregated|3299         |0            |1700                |1726.9569566535313   |7                |5490             |55230.63473779933   |27.513688212146757|0.0       |1700|2200|2500|2700|3100|3300|3800|3900 |4600 |5500  |5500 |



### 1 master, 1 slave, limit 200 (get 200 order by created_at DESC)


#### no index

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50%|66%|75%|80%|90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|---|---|---|---|----|----|----|----|-----|------|----|
|GET |/todos/   |2137         |0            |860                 |849.6686944314459    |64               |1730             |27601.0             |32.111475198311176|0.0       |860|910|950|980|1100|1300|1300|1300|1600 |1700  |1700|
|POST|/todos/   |1495         |0            |850                 |842.1157190635452    |31               |1625             |137.0               |22.464508854223308|0.0       |850|900|950|980|1100|1300|1300|1400|1600 |1600  |1600|
|    |Aggregated|3632         |0            |860                 |846.5597466960353    |31               |1730             |16296.297356828194  |54.57598405253449 |0.0       |860|910|950|980|1100|1300|1300|1400|1600 |1700  |1700|


#### created_at index.

> With limit, now a index scan is performed which is much better than no index

```sql
EXPLAIN SELECT * FROM todos ORDER BY created_at DESC LIMIT 200;
                                            QUERY PLAN                                             
---------------------------------------------------------------------------------------------------
 Limit  (cost=0.29..4.07 rows=100 width=48)
   ->  Index Scan using idx_todomodel_created_at on todos  (cost=0.29..426.02 rows=11249 width=48)
(2 rows)
```

|Type|Name      |Request Count|Failure Count|Median Response Time|Average Response Time|Min Response Time|Max Response Time|Average Content Size|Requests/s        |Failures/s|50%|66%|75%|80%|90% |95% |98% |99% |99.9%|99.99%|100%|
|----|----------|-------------|-------------|--------------------|---------------------|-----------------|-----------------|--------------------|------------------|----------|---|---|---|---|----|----|----|----|-----|------|----|
|GET |/todos/   |3642         |0            |770                 |759.2468423942888    |52               |1563             |27601.0             |37.59474785086751 |0.0       |770|810|860|870|960 |1000|1100|1200|1200 |1600  |1600|
|POST|/todos/   |2384         |0            |760                 |758.319211409396     |17               |1323             |137.0               |24.608972783214757|0.0       |760|810|850|870|960 |1000|1100|1200|1200 |1300  |1300|
|    |Aggregated|6026         |0            |770                 |758.8798539661467    |17               |1563             |16735.720212412878  |62.20372063408227 |0.0       |770|810|850|870|960 |1000|1100|1200|1200 |1600  |1600|
