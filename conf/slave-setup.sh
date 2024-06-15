
rm -rf "${PGDATA}"/*

pg_basebackup -d "user=replica password=replica host=db" -D "${PGDATA}" -Fp -Xs -P -R


touch "${PGDATA}"/standby.signal

cat >> "${PGDATA}"/postgresql.conf << EOF
listen_addresses = '*'
hot_standby = on
EOF

cat >> var/lib/postgresql/data/postgresql.auto.conf << EOF
primary_conninfo = 'user=replica password=replica host=db port=5432 sslmode=prefer sslcompression=0 gssencmode=disable target_session_attrs=any application_name=slave_db'
EOF

PGDATA=$PGDATA /usr/local/bin/pg_ctl -w restart