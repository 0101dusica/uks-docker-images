# Architecture Overview

## System Description

The application is a simplified DockerHub clone built as a multi-container system. It allows users to manage Docker image repositories, push images to a self-hosted registry, and gives administrators tools to manage users, official repositories, and analyze system logs.

The system is composed of 7 Docker services orchestrated via Docker Compose.

---

## Container Architecture

```mermaid
graph TB
    User(["👤 User / Browser"])
    DockerCLI(["🐳 Docker CLI\n(docker push/pull)"])

    subgraph Docker Compose
        NGINX["nginx:80\n(Reverse Proxy)"]
        Backend["backend:8000\n(Django + Gunicorn)"]
        Postgres["postgres:5432\n(PostgreSQL 15)"]
        Redis["redis:6379\n(Redis 7)"]
        Registry["registry:5000\n(Docker Distribution)"]
        ES["elasticsearch:9200\n(Elasticsearch 8)"]
        LogFwd["log-forwarder\n(management command loop)"]
    end

    LogVolume[("📁 log_data volume\n/app/logs/django.log")]

    User -->|"HTTP :80"| NGINX
    NGINX -->|"proxy_pass :8000"| Backend
    DockerCLI -->|"docker push/pull :5000"| Registry

    Backend --> Postgres
    Backend --> Redis
    Backend -->|"Registry API"| Registry
    Backend -->|"write logs"| LogVolume
    Backend -->|"analytics search"| ES

    LogFwd -->|"read logs"| LogVolume
    LogFwd -->|"bulk index"| ES
```

---

## Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Nginx
    participant Django
    participant Redis
    participant Postgres
    participant ES as Elasticsearch

    User->>Nginx: HTTP GET /public-repositories/?search=ubuntu
    Nginx->>Django: proxy_pass
    Django->>Redis: GET cache key
    alt cache hit
        Redis-->>Django: cached result
    else cache miss
        Django->>Postgres: SELECT repositories WHERE ...
        Postgres-->>Django: rows
        Django->>Redis: SET cache (5 min TTL)
    end
    Django-->>Nginx: HTTP 200 HTML
    Nginx-->>User: response

    Note over User,ES: Admin log search
    User->>Nginx: POST /analytics/
    Nginx->>Django: proxy_pass
    Django->>ES: search index=django-logs
    ES-->>Django: hits
    Django-->>User: rendered results
```

---

## Log Pipeline

```mermaid
flowchart LR
    Django["Django App\n(Python logging)"]
    File["django.log\n(JSON lines, shared volume)"]
    Forwarder["log-forwarder container\n(runs every 60s)"]
    ES["Elasticsearch\nindex: django-logs"]
    AdminUI["Admin Analytics UI\n(/analytics/)"]

    Django -->|"JsonFormatter"| File
    Forwarder -->|"reads new lines\nvia cursor"| File
    Forwarder -->|"bulk index"| ES
    AdminUI -->|"AND/OR/NOT query"| ES
```

---

## Django Application Structure

```mermaid
graph TD
    subgraph Django Project
        Config["config/\nsettings, urls, wsgi"]
        Users["users/\nUser model, auth, roles, badges"]
        Repos["repositories/\nRepository, Star models\nRegistryService"]
        Tags["tags/\nTag model"]
        Analytics["analytics/\nElasticsearch views\nforward_logs_to_es command\nquery_parser"]
        Frontend["frontend/\ntemplate views\nHTML templates"]
    end

    Config --> Users
    Config --> Repos
    Config --> Tags
    Config --> Analytics
    Config --> Frontend

    Frontend --> Users
    Frontend --> Repos
    Frontend --> Tags
    Frontend --> Analytics
```

---

## Services Summary

| Service | Image | Port | Purpose |
|---|---|---|---|
| **backend** | custom (Python 3.12-slim) | 8000 (internal) | Django application served by Gunicorn |
| **nginx** | custom (nginx:alpine) | 80 | Reverse proxy, serves static files |
| **postgres** | postgres:15 | 5432 | Primary relational database |
| **redis** | redis:7 | 6379 | Response cache (5 min TTL on public repos) |
| **registry** | registry:2 | 5000 | Self-hosted Docker image registry |
| **elasticsearch** | elasticsearch:8.11.1 | 9200 | Log storage and full-text search |
| **log-forwarder** | custom (same as backend) | - | Reads django.log, bulk-indexes to ES every 60s |

---

## Data Model

```mermaid
erDiagram
    User {
        int id
        string username
        string email
        string password
        string role
        string badge
        bool is_active
        bool must_change_password
        datetime date_joined
    }

    Repository {
        int id
        string name
        string description
        string visibility
        bool is_official
        int stars
        datetime created_at
        datetime updated_at
    }

    Tag {
        int id
        string name
        datetime created_at
    }

    Star {
        int id
        datetime created_at
    }

    User ||--o{ Repository : "owns"
    Repository ||--o{ Tag : "has"
    User ||--o{ Star : "creates"
    Repository ||--o{ Star : "receives"
```

---

## User Roles

| Role | Capabilities |
|---|---|
| **Unauthenticated** | Browse and search public repositories |
| **User** | + Create/edit/delete own repositories, manage tags, star repositories |
| **Admin** | + Manage users (block/unblock, assign badges), manage official repositories, view analytics logs |
| **Superadmin** | + Create admins, block/unblock admins. Auto-created on first startup with a generated password. |

---

## CI/CD Pipeline

```mermaid
flowchart LR
    PR["Pull Request\n→ develop or master"]
    Push["Push\n→ master"]

    CI["CI Workflow\nci.yml"]
    CD["CD Workflow\ncd.yml"]

    Tests["Run Django tests\n(postgres + redis services)"]
    Build["Build Docker image\n(docker/backend/Dockerfile)"]
    DockerHub["Push to DockerHub\n0101dusica/uks-dockerhub:latest\n0101dusica/uks-dockerhub:{sha}"]
    Tag["Create git tag\nfrom commit message"]

    PR --> CI --> Tests
    Push --> CD --> Tests --> Build --> DockerHub --> Tag
```
