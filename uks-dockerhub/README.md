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

## Environment Setup (.env)

Before running the application, you must create a `.env` file in the project root (next to `docker-compose.yml`).

1. Copy the example file:
   ```sh
   cp .env.example .env
   ```
2. Open `.env` and fill in the required values. Example:
   ```env
   POSTGRES_DB=uksdb
   POSTGRES_USER=uksuser
   POSTGRES_PASSWORD=strongpassword
   DJANGO_SECRET_KEY=your-generated-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   REDIS_URL=redis://redis:6379/0
   ```
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database name, user, and password (choose your own or use these defaults for development)
   - `DJANGO_SECRET_KEY`: Generate a secure Django key at https://djecrety.ir/
   - `DEBUG`: Use `True` for development
   - `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (e.g. `localhost,127.0.0.1`)
   - `REDIS_URL`: For Docker, use `redis://redis:6379/0` (replace `redis` if your service is named differently)

3. Save the file and continue with the standard Docker Compose workflow.

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

## Implemented Endpoints

- **POST /register/** – User registration endpoint. Allows new users to create an account. Returns basic user info on success.

For detailed API usage and request/response examples, see `docs/api.md`.

