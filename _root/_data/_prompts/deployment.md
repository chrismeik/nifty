# Deployment

## Overview

The application runs as a Docker Compose stack defined in `_root/_platform/_compose/compose.yml`. Nginx sits in front of everything, routing requests to FastAPI and per-product Astro frontends. Deployed lanes (e.g. prod) will be driven by git branches and GitHub Actions; that setup is not built yet.

---

## Docker Stack

```
nginx                — reverse proxy on port 80
├── api              — FastAPI on port 8000
├── worker           — background task worker on port 8001
├── postgres         — PostgreSQL on port 5432
├── redis            — Redis on port 6379
└── astro-veratreeos — Astro frontend for veratreeos on port 4321
```

Optional services activated via Docker Compose profiles:
- `--profile observability` — Loki + Prometheus + Grafana

Each product with a web frontend runs its own Astro container. There is no shared Astro build.

---

## Nginx Routing

Nginx routes requests to the appropriate upstream based on path prefix:

- `/veratreeos/` → `astro-veratreeos`
- API paths → `api`

Each Astro container's `astro.config.mjs` sets `base: '/<product>'` so all assets are scoped under that prefix.

When adding a new Astro product, add both an upstream block and a location block to `_root/_platform/_nginx/nginx.conf`.

After editing `nginx.conf`, restart the nginx container:
```bash
docker restart <project>-nginx-1
```

---

## Environment Variables

Shared environment lives in `_root/_platform/_compose/.env` (gitignored).

Per-product secrets live in `<name>/.env` (gitignored).

Bootstrap loads per-product `.env` files at startup with `override=False` — the shared `.env` takes precedence.

---

## Environments (deployment lanes)

`ENVIRONMENT` names the lane a stack runs in. `up.sh` sets it to `sandbox` when it is unset, so every local run is the sandbox lane. Deployed lanes set it explicitly (e.g. `ENVIRONMENT=prod`). It is passed into the `api` and `worker` containers, and `up.sh` loads `compose.<ENVIRONMENT>.yml` and `nginx.<ENVIRONMENT>.conf` overrides when they exist.

## Local Development

```bash
bash _root/_platform/up.sh up -d --build
```

The API container runs as root. If Docker creates files owned by root in your local bind-mounted directories, fix ownership with:
```bash
sudo chown -R $(whoami):$(whoami) .
```

To reset a product's database schema and reload seeds:
```bash
docker compose exec postgres psql -U <user> -d <db> -c 'DROP SCHEMA IF EXISTS <schema> CASCADE;'
docker compose restart api
```

---

## Deploying to a Server (EC2)

Deploys to a server will run through GitHub Actions, one lane per git branch (not built yet). The old rsync script (`_root/_ops/sync.sh`) has been removed.

**Do not deploy automatically after making code changes.** Always wait for explicit instruction from the developer before running sync or any remote commands.

---

## Schema Changes on EC2

**Never use `ALTER TABLE` to migrate a live EC2 database.** The rule is:

- **Code-only change** (new page, new endpoint, copy change) → deploy as normal
- **Schema change** (new column, new table, changed type) → full teardown and rebuild on EC2:

```bash
# SSH into EC2, then:
cd ~/veratree/root
docker compose down -v
docker compose up -d --build
```

The `-v` flag removes volumes, wiping postgres. The API bootstrap re-runs `init.sql` on startup, recreating all schemas and reseeding. This means **all existing data is lost** — acceptable for this project, and far simpler than managing migrations.

---

## Docker Compose Profiles

```bash
docker compose --profile observability up -d  # with observability
docker compose up -d                          # core services only
```

---

## Installing Docker on a New Server (Amazon Linux 2023)

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

mkdir -p ~/.docker/cli-plugins
curl -fsSL -L https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-amd64 \
  -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
```
