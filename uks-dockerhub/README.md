# UKS DockerHub

A simplified DockerHub-like web application for managing Docker repositories and images. Built as a university project for the *Software Configuration Management* course.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2+ with Django REST Framework |
| Templates | Django templates (server-rendered HTML) |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Reverse Proxy | Nginx |
| Container Registry | Docker Distribution (registry:2) |
| Log Analytics | Elasticsearch 8 |
| Orchestration | Docker Compose |
| CI/CD | GitHub Actions |

For a full architecture overview with diagrams, see [docs/architecture.md](docs/architecture.md).

---

## Prerequisites

- Docker and Docker Compose installed
- For pushing images to the local registry: Docker daemon configured to allow insecure registry at `localhost:5000` (see below)

---

## Quick Start

### 1. Configure environment

```sh
cp .env.example .env
```

Edit `.env` and fill in the required values:

```env
POSTGRES_DB=uksdb
POSTGRES_USER=uksuser
POSTGRES_PASSWORD=strongpassword
DJANGO_SECRET_KEY=your-secret-key-here
```

Generate a Django secret key with:
```sh
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Start the application

```sh
docker compose up --build
```

The application will be available at **http://localhost**

### 3. First login (Superadmin)

On first startup, a superadmin account is automatically created with a generated password. See [docs/superadmin-setup.md](docs/superadmin-setup.md) for login instructions.

---

## Useful Commands

```sh
# Run Django tests
docker compose exec backend python manage.py test --verbosity=2

# Apply migrations
docker compose exec backend python manage.py migrate

# View application logs
docker compose logs backend

# Read superadmin initial password
docker compose exec backend cat superadmin_initial_password.txt
```

---

## Pushing Docker Images to the Local Registry

The application includes a self-hosted Docker registry on port 5000.

### Configure Docker daemon (one-time setup)

Add `localhost:5000` as an insecure registry in your Docker daemon config (`/etc/docker/daemon.json`):

```json
{
  "insecure-registries": ["localhost:5000"]
}
```

Then restart Docker:
```sh
sudo systemctl restart docker
```

### Push an image

```sh
# Tag your image
docker tag myimage localhost:5000/yourusername/reponame:tagname

# Push to the local registry
docker push localhost:5000/yourusername/reponame:tagname
```

The tag will automatically appear in the repository's Tags section in the web UI.

---

## Features

| Feature | Role |
|---|---|
| Browse and search public repositories | All users |
| Register, log in, manage profile | All users |
| Create, edit, delete repositories (public/private) | Authenticated users |
| Manage tags (push via Docker CLI or web UI) | Repository owners |
| Star repositories | Authenticated users |
| View starred repositories | Authenticated users |
| Manage users (block/unblock, assign badges) | Admin |
| Manage official repositories | Admin |
| Search and analyze system logs (Elasticsearch) | Admin |
| Create new admins | Superadmin |

---

## CI/CD

| Trigger | Workflow | Actions |
|---|---|---|
| Pull request → `develop` or `master` | `ci.yml` | Run all Django tests |
| Push → `master` | `cd.yml` | Run tests, build Docker image, push to DockerHub, create git tag |

Docker image published to: `0101dusica/uks-dockerhub` on DockerHub.

---

## Documentation

- [docs/architecture.md](docs/architecture.md) — System architecture and diagrams
- [docs/superadmin-setup.md](docs/superadmin-setup.md) — Superadmin first-login instructions
- [docs/api.md](docs/api.md) — REST API reference
