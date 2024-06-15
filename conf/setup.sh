
mkdir -p /var/lib/postgresql/archive


cat >> var/lib/postgresql/data/postgresql.conf << EOF
listen_addresses = '*'
wal_level = hot_standby
synchronous_commit = on
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
max_wal_senders = 2
wal_keep_segments = 10
synchronous_standby_names = 'slave_db'
EOF

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE ROLE replica LOGIN REPLICATION PASSWORD 'replica';
	ALTER ROLE replica WITH CONNECTION LIMIT 8;
EOSQL

cat >> /var/lib/postgresql/data/pg_hba.conf << EOF
host    replication     replica         0.0.0.0/0         md5
EOF