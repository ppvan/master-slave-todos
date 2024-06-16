
# Replication guide with postgres and docker compose.

> This guide provide some understanding about replication and implemented by `docker-compose`.
> Realworld replication is strongly tied to deployment.

## Concepts

### Replication

Replication is a solution(among many others) to allow a second server to take over quickly if primary server fails(high availibility) or allow serveral server serve same data (load balancer). This document only focus on replication.

In replication, there are 3 types of server:
- Primary server: read/write queries
- Warn standby server: do nothing until promoted to primary, often use for high availibility
- Hot standby server: read queries, user for load balancing


### Write ahead logs(WAL)

Write ahead logs is a pattern to ensure ACID property of database. Basiclly you write logs before make any changes to database. So you can archive that logs and recorver them on another server.

Replication can be achieved by continously archive WAL on primary and applying them on replication. 

[![](https://mermaid.ink/img/pako:eNqNkE1Pg0AQhv_KZk41AQKLfO3BxMRjvdiDieBhClMhBZYsH4qE_-6W2qZGY7qH-dj3mcm7O0EqMwIBu1K-pzmqjq2fkprpU2HbkYpXj0tmGXa4xZZuXo8yqjQvBsriU8FaUgOpb7ktcSAnXm0O-dfwovJ_Vfcv9dIZM022xXTfN-z5fq27u7OnE3i2plFFqdT2xgU8ursG4tdALhhQkaqwyPRXToeRBLqcKkpA6DJDtU8gqWfNYd_JzVinIDrVkwF9ox9IDwW-KaxA7LBs9W2D9YuUP3oQE3yA4IFn8dD3uWNHbuAZMIIwncjSrWfbYahDFPj-bMDnssC2Is_jrst1cOxb7s9fc1ad_A?type=png)](https://mermaid.live/edit#pako:eNqNkE1Pg0AQhv_KZk41AQKLfO3BxMRjvdiDieBhClMhBZYsH4qE_-6W2qZGY7qH-dj3mcm7O0EqMwIBu1K-pzmqjq2fkprpU2HbkYpXj0tmGXa4xZZuXo8yqjQvBsriU8FaUgOpb7ktcSAnXm0O-dfwovJ_Vfcv9dIZM022xXTfN-z5fq27u7OnE3i2plFFqdT2xgU8ursG4tdALhhQkaqwyPRXToeRBLqcKkpA6DJDtU8gqWfNYd_JzVinIDrVkwF9ox9IDwW-KaxA7LBs9W2D9YuUP3oQE3yA4IFn8dD3uWNHbuAZMIIwncjSrWfbYahDFPj-bMDnssC2Is_jrst1cOxb7s9fc1ad_A)


Note that the process is async by default, so slaves may not be up-to-date with master. This can be solved by streaming WAL over TCP and setup a synchronous slave. Even so, there is a window for data loss should the primary server suffer a catastrophic failure; transactions not yet shipped will be lost

[![](https://mermaid.ink/img/pako:eNp9kE1LxDAQhv9KGFhYoS1tar9yEASP68U9CLYexnbWFvuxJGl1Lf3vpnVlEaUJzDuT551kyAh5VxAIONTde16i1Gz3kLXMrAaVJplu7xdlBWp8QUVXz994s2Eo87IaqEh_EqZIDiTPDlXjQF663c_6p3-hfJX6_9F5X8Zjts0eb3fK6M35wXXM17EPFjQkG6wK8ynjbM5Al9RQBsKkBcq3DLJ2Mj7sdbc_tTkILXuyoD-aOemuwleJDYgD1sqcHrF96rpfNYgRPkDwKHB4HIbccxM_Ciw4gbC9xDFl4LpxbEISheFkwedygeskQcB9n5vgudc8nL4AHKiJ6A?type=png)](https://mermaid.live/edit#pako:eNp9kE1LxDAQhv9KGFhYoS1tar9yEASP68U9CLYexnbWFvuxJGl1Lf3vpnVlEaUJzDuT551kyAh5VxAIONTde16i1Gz3kLXMrAaVJplu7xdlBWp8QUVXz994s2Eo87IaqEh_EqZIDiTPDlXjQF663c_6p3-hfJX6_9F5X8Zjts0eb3fK6M35wXXM17EPFjQkG6wK8ynjbM5Al9RQBsKkBcq3DLJ2Mj7sdbc_tTkILXuyoD-aOemuwleJDYgD1sqcHrF96rpfNYgRPkDwKHB4HIbccxM_Ciw4gbC9xDFl4LpxbEISheFkwedygeskQcB9n5vgudc8nL4AHKiJ6A)

### Slave life-cycle

### Failover problems

## Setup and config

> Heavily specialize in docker evironment.



### Config master node

#### Create archive directory

```sh
sudo mkdir -p /var/lib/postgresql/archive
sudo chmod 700 /var/lib/postgresql/archive
sudo chown postgres:postgres /var/lib/postgresql/archive
```

#### Config postgres.conf

```conf
# var/lib/postgresql/data/postgresql.conf

listen_addresses = '*' # need in docker container
wal_level = hot_standby
synchronous_commit = on # syncchoronous standby
archive_mode = on # also archive WALs
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
max_wal_senders = 2
wal_keep_segments = 10
synchronous_standby_names = 'slave_db' # slave name
```

#### Create replication user with replication priviledge

```sql
CREATE ROLE replica LOGIN REPLICATION PASSWORD 'replica';
ALTER ROLE replica WITH CONNECTION LIMIT 8;
```

### Allow remote replica connect

> Add following to the end of pg_hba.conf
```conf
# /var/lib/postgresql/data/pg_hba.conf

host    replication     replica         0.0.0.0/0         md5
```

### Config slave node

#### Replication master data

```sh
# export PGDATA=/var/lib/postgresql/data

rm -rf "${PGDATA}"/*

pg_basebackup -d "user=replica password=replica host=db" -D "${PGDATA}" -Fp -Xs -P -R
```

#### Create config and standby.signal

> standby.signal is needed so postgres change to standby mode (slave mode)


```conf
# var/lib/postgresql/data/postgresql.conf

listen_addresses = '*' # need in docker container
wal_level = hot_standby
```

```conf
# var/lib/postgresql/data/postgresql.auto.conf
primary_conninfo = 'user=replica password=replica host=db port=5432 sslmode=prefer sslcompression=0 gssencmode=disable target_session_attrs=any application_name=slave_db'
```

```sh
touch var/lib/postgresql/data/standby.signal
```


## Reference

[Postgresql documentation, chapter 27](https://www.postgresql.org/docs/current/high-availability.html)

[Postgres VN, setup master slave](https://www.postgresql.vn/blog/setup_master_slave_for_postgres12)