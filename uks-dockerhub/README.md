# UKS DockerHub (Initial Structure)

This project is a simplified DockerHub-like web application for managing Docker repositories, following UKS (Software Configuration Management) best practices.

## Architecture

- **Backend:** Django + Django REST Framework
- **Frontend:** Django templates
- **Database:** PostgreSQL
- **Cache:** Redis
- **Reverse Proxy:** NGINX
- **Orchestration:** Docker Compose
- **CI/CD:** Placeholder configuration

Project is clearly separated into backend and frontend, containerized, and ready for CI/CD.

## Local Development (Docker Compose)

1. Copy `.env.example` to `.env` and fill in required values.
2. Run:
   ```sh
   docker-compose up --build
   ```
3. Access backend at http://localhost:8000, frontend at http://localhost:8080

### Database Initialization

The PostgreSQL database and user are automatically created by Docker using environment variables from your `.env` file. 
If you want to run custom SQL on first startup (e.g. create tables, seed data), add scripts to:

```
docker/postgres/docker-entrypoint-initdb.d/
```
All `.sql` files in this folder will be executed automatically the first time the container starts (when the database is empty).

> **Note:** This is an initial project structure. No business logic, models, or endpoints are implemented yet.
