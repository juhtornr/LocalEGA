FROM centos/postgresql-95-centos7 
LABEL maintainer "Frédéric Haziza, NBIS"

COPY db.sql /docker-entrypoint-initdb.d/db.sql
#CMD postgres --single -D $PGDATA $POSTGRESQL_DATABASE < /docker-entrypoint-initdb.d/db.sql
#PGPASSWORD=$POSTGRESQL_PASSWORD psql -U $POSTGRESQL_USER $POSTGRESQL_DATABASE < /docker-entrypoint-initdb.d/db.sql
