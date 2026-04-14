# API Documentation

This document describes the available API endpoints and their usage.

## User Registration

**Endpoint:** `/api/users/register/`

**Method:** POST

**Description:**
Register a new user account. Returns the created user data on success.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "password": "StrongPassword123!"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "role": "user"
}
```

---

## Public Repositories

**Endpoint:** `/api/repositories/public/`

**Method:** GET

**Query Parameters:**
- `search` - Search by name or description
- `sort` - Sort order: `newest` (default), `stars`, `name`
- `badge` - Filter by badge: `official`, `verified_publisher`, `sponsored_oss`

**Response (200 OK):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "myrepo",
      "description": "A repository",
      "owner": "username",
      "owner_badge": "none",
      "is_official": false,
      "stars": 5,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

## Container Registry

### Registry Catalog

**Endpoint:** `/api/repositories/registry/catalog/`

**Method:** GET

**Description:**
List all repositories stored in the Docker container registry.

**Response (200 OK):**
```json
{
  "repositories": ["username/myrepo", "admin/nginx"]
}
```

### Registry Tags

**Endpoint:** `/api/repositories/registry/{owner}/{repo_name}/tags/`

**Method:** GET

**Description:**
List all tags for a repository in the container registry, including digest and size.

**Response (200 OK):**
```json
{
  "repository": "username/myrepo",
  "tags": [
    {
      "name": "v1.0",
      "digest": "sha256:abc123...",
      "size": 2415
    }
  ]
}
```

---

## Pushing Docker Images

The application uses a self-hosted Docker Distribution (registry:2) container registry running on port 5000.

### How to push an image

1. Tag your local image with the registry address:
```bash
docker tag myimage localhost:5000/username/reponame:tagname
```

2. Push to the registry:
```bash
docker push localhost:5000/username/reponame:tagname
```

3. The image will appear in the Tags section of your repository in the web UI.

### How to pull an image

```bash
docker pull localhost:5000/username/reponame:tagname
```

### Registry API

The registry also exposes a standard Docker Registry HTTP API V2:
- `GET http://localhost:5000/v2/_catalog` - List all repositories
- `GET http://localhost:5000/v2/{name}/tags/list` - List tags for a repository
