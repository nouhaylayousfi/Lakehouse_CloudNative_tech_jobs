SELECT 'CREATE DATABASE metastore_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname  'metastore_db')
\gexec

DO 
$$
BEGIN 
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname ='hive') THEN 
        CREATE ROLE hive WITH LOGIN PASSWORD 'hive';
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE metastore_db TO hive;
ALTER DATABASE metastore_db OWNER TO hive; 