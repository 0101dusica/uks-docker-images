# Project Architecture

This document describes the high-level architecture of the project.

- Backend: Django REST Framework
- Frontend: Django templates
- Database: PostgreSQL
- Cache: Redis
- Reverse Proxy: NGINX
- Orchestration: Docker Compose

## Folder Structure

- backend/ - Django project and apps
	- frontend/ - Django templates, views, static (HTML pages)
- docker/ - Dockerfiles and configs
- docs/ - Documentation
- scripts/ - Utility scripts
