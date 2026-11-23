# Deployment

Production runs on the GCE VM at `35.228.54.76` through Docker Compose.

```
GitHub Actions (CI + deploy job)
        │  rsync over SSH on push to main
        ▼
/opt/swe-gunners/app   ← checkout without .git
/opt/swe-gunners/.env  ← production secrets, never overwritten
        │  docker compose -f docker-compose.prod.yml
        ▼
host nginx :80 ──▶ frontend (127.0.0.1:8080) ──/api──▶ backend ──▶ postgres
```

The VM is shared with another site, so the host nginx owns port 80 and the
stack publishes only `127.0.0.1:8080`. PostgreSQL and the API stay on the
internal Docker network.

## One-time server setup

```bash
ssh 35.228.54.76
sudo bash /path/to/deploy/server-setup.sh
```

The script installs Docker, rsync and UFW, adds a 2 GB swap file, and allows
ports 22, 80 and 443. It creates `/opt/swe-gunners` owned by the deploy user and
adds that user to the `docker` group.

Then create the production environment file:

```bash
sudo install -d -o "$USER" -g "$USER" /opt/swe-gunners
cp deploy/env.production.example /opt/swe-gunners/.env
chmod 600 /opt/swe-gunners/.env
# replace POSTGRES_PASSWORD and JWT_SECRET
openssl rand -hex 32
```

`CORS_ORIGINS` must be a JSON array, for example
`["http://35.228.54.76"]`. `SMTP_HOST` can stay empty while no mail provider is
configured; verification messages are then written to the container log.

### Host nginx

Requests by IP reach BiletFlow through `deploy/nginx-biletflow.conf`, which is
the `default_server` on port 80. Other sites on the VM keep their own
`server_name` blocks. Install it once:

```bash
sudo cp /opt/swe-gunners/app/deploy/nginx-biletflow.conf /etc/nginx/sites-available/biletflow
sudo ln -s /etc/nginx/sites-available/biletflow /etc/nginx/sites-enabled/biletflow
sudo nginx -t && sudo systemctl reload nginx
```

## GitHub configuration

The deploy job in `.github/workflows/ci.yml` uses three repository secrets:

| Secret            | Value                                    |
| ----------------- | ---------------------------------------- |
| `SSH_HOST`        | `35.228.54.76`                           |
| `SSH_USER`        | deploy user on the VM                    |
| `SSH_PRIVATE_KEY` | private half of the GitHub deploy SSH key |

The matching public key is appended to `~/.ssh/authorized_keys` on the server.
The key is only used by Actions to sync files and run `deploy/deploy.sh`.

The job runs only after `backend`, `frontend` and `e2e` pass on a push to
`main`. It rsyncs the repository (without `.git`, `mobile` and local
dependencies) and then runs the deploy script, which builds images, applies
Alembic migrations and restarts the stack.

## Manual deployment

```bash
rsync -az --delete --exclude='.git' --exclude='.github' --exclude='.env*' \
  --exclude='node_modules' --exclude='dist' --exclude='.venv' \
  --exclude='__pycache__' --exclude='mobile' \
  ./ amanzholov@35.228.54.76:/opt/swe-gunners/app/

ssh amanzholov@35.228.54.76 'bash /opt/swe-gunners/app/deploy/deploy.sh'
```

Useful commands on the server:

```bash
cd /opt/swe-gunners/app
docker compose --env-file /opt/swe-gunners/.env -f docker-compose.prod.yml ps
docker compose --env-file /opt/swe-gunners/.env -f docker-compose.prod.yml logs -f backend
```

## Notes

- UFW alone is not enough on a GCE VM: the VPC firewall also filters ingress.
  Allow `tcp:80` and `tcp:443` for this VM (or for all instances) in
  **VPC network → Firewall**, for example:

  ```bash
  gcloud compute firewall-rules create allow-http-https \
    --allow tcp:80,tcp:443 --source-ranges 0.0.0.0/0
  ```

  Without that rule the site is reachable only from the VM itself, even though
  UFW is open.
- The site is served over plain HTTP. HTTPS needs a domain name and a
  certificate on the host nginx (certbot), not in the stack.
- Docker publishes ports through its own iptables rules, so keep public ports
  declared explicitly in `docker-compose.prod.yml` rather than relying on UFW
  alone.
- PostgreSQL data lives in the `pgdata` Docker volume and survives deploys.
  Back it up with `docker compose exec postgres pg_dump`.
