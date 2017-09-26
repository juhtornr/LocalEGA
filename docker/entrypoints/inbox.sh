#!/bin/bash

set -e

chown root:ega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

pushd /root/ega/auth
make install clean
ldconfig -v
popd

EGA_DB_IP=$(getent hosts ega_db | awk '{ print $1 }')

mkdir -p /etc/ega
cat > /etc/ega/auth.conf <<EOF
debug = ok_why_not

##################
# Databases
##################
db_connection = host=${EGA_DB_IP} port=5432 dbname=lega user=${POSTGRES_USER} password=${POSTGRES_PASSWORD} connect_timeout=1 sslmode=disable

enable_rest = yes
#rest_endpoint = http://localhost:9100/user/%s
rest_endpoint = http://ega_frontend:9100/user/%s

##################
# NSS Queries
##################
nss_get_user = SELECT elixir_id,'x',1000,1000,'EGA User','/ega/inbox/'|| elixir_id,'/sbin/nologin' FROM users WHERE elixir_id = \$1 LIMIT 1
nss_add_user = SELECT insert_user(\$1,\$2,\$3)

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = \$1 LIMIT 1
pam_acct = SELECT elixir_id FROM users WHERE elixir_id = \$1 and current_timestamp < last_accessed + expiration
pam_prompt = aaaannndd...cue music: 
EOF

cat > /usr/local/bin/ega_ssh_keys.sh <<EOF
#!/bin/bash

eid=\${1%%@*} # strip what's after the @ symbol

query="SELECT pubkey from users where elixir_id = '\${eid}' LIMIT 1"

PGPASSWORD=${POSTGRES_PASSWORD} psql -tqA -U ${POSTGRES_USER} -h ega_db -d lega -c "\${query}"
EOF
chmod 755 /usr/local/bin/ega_ssh_keys.sh

echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
