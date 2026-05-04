# API & Interface Reference

The application exposes two types of interfaces:
- **REST API** (`/api/`) — JSON responses, used by external tools or scripts
- **Web Interface** (`/`) — HTML pages rendered by Django templates

---

## REST API Endpoints

### POST `/api/users/register/`

Register a new user account.

**Request body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "password": "StrongPassword123!"
}
```

**Response 201:**
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

### GET `/api/repositories/public/`

List public repositories with optional search, sort, and filter.

**Query parameters:**

| Parameter | Values | Description |
|---|---|---|
| `search` | any string | Filter by name or description |
| `sort` | `newest` (default), `stars`, `name` | Sort order |
| `badge` | `official`, `verified_publisher`, `sponsored_oss` | Filter by badge |

**Response 200:**
```json
{
  "count": 2,
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

### GET `/api/repositories/registry/catalog/`

List all repositories stored in the self-hosted container registry.

**Response 200:**
```json
{
  "repositories": ["username/myrepo", "admin/nginx"]
}
```

---

### GET `/api/repositories/registry/{owner}/{repo_name}/tags/`

List all tags for a repository in the container registry, including digest and compressed size.

**Response 200:**
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

## Web Interface Pages

All pages below return HTML and are accessed through the browser.

### Authentication

| URL | Method | Description | Access |
|---|---|---|---|
| `/login/` | GET, POST | Login form | All |
| `/logout/` | GET | Log out and redirect to login | Authenticated |
| `/register/` | GET, POST | Registration form | All |
| `/register/success/` | GET | Registration success page | All |
| `/change-password/` | GET, POST | Forced password change on first login | Authenticated |

### User Profile

| URL | Method | Description | Access |
|---|---|---|---|
| `/profile/` | GET, POST | View and edit profile (name, email) | Authenticated |
| `/starred/` | GET | List of starred repositories | Authenticated |

### Explore (Public Repositories)

| URL | Method | Description | Access |
|---|---|---|---|
| `/public-repositories/` | GET | Browse, search, and filter public repos | All |
| `/repository/<id>/` | GET | Repository detail view | All |

### Repository Management

| URL | Method | Description | Access |
|---|---|---|---|
| `/my-repositories/` | GET | List own repositories | Authenticated |
| `/repositories/create/` | GET, POST | Create new repository | Authenticated |
| `/repositories/<id>/edit/` | GET, POST | Edit description and visibility | Owner |
| `/repositories/<id>/delete/` | POST | Delete repository and all its data | Owner |
| `/repositories/<id>/star/` | POST | Toggle star on a repository | Authenticated |
| `/repositories/<id>/tags/` | GET, POST | View and manage tags (DB + registry) | Owner |
| `/repositories/<id>/tags/<tag_id>/delete/` | POST | Delete a DB tag | Owner |
| `/repositories/<id>/registry-tags/<tag_name>/delete/` | POST | Delete a tag from the container registry | Owner |

### Admin Dashboard

| URL | Method | Description | Access |
|---|---|---|---|
| `/admin-dashboard/` | GET, POST | Manage users and official repositories | Admin |
| `/admin-dashboard/user/<id>/details/` | GET | User details (JSON) | Admin |
| `/admin-dashboard/user/<id>/block/` | POST | Block a user | Admin |
| `/admin-dashboard/user/<id>/unblock/` | POST | Unblock a user | Admin |
| `/admin-dashboard/user/<id>/assign-badge/` | POST | Assign badge (JSON body: `{"badge": "verified_publisher"}`) | Admin |
| `/admin-dashboard/official/<id>/edit/` | GET, POST | Edit an official repository | Admin |
| `/admin-dashboard/official/<id>/delete/` | POST | Delete an official repository | Admin |

### Superadmin Dashboard

| URL | Method | Description | Access |
|---|---|---|---|
| `/superadmin-dashboard/` | GET, POST | Manage users, admins; create new admins | Superadmin |
| `/superadmin-dashboard/user/<id>/details/` | GET | User details (JSON) | Superadmin |
| `/superadmin-dashboard/user/<id>/block/` | POST | Block a user | Superadmin |
| `/superadmin-dashboard/user/<id>/unblock/` | POST | Unblock a user | Superadmin |
| `/superadmin-dashboard/admin/<id>/details/` | GET | Admin details (JSON) | Superadmin |
| `/superadmin-dashboard/admin/<id>/block/` | POST | Block an admin | Superadmin |
| `/superadmin-dashboard/admin/<id>/unblock/` | POST | Unblock an admin | Superadmin |

### Analytics

| URL | Method | Description | Access |
|---|---|---|---|
| `/analytics/` | GET, POST | Search system logs in Elasticsearch (AND/OR/NOT queries) | Admin |

---

## Pushing Docker Images to the Registry

The self-hosted registry runs on `localhost:5000`.

```sh
# Tag your image
docker tag myimage localhost:5000/yourusername/reponame:tagname

# Push
docker push localhost:5000/yourusername/reponame:tagname

# Pull
docker pull localhost:5000/yourusername/reponame:tagname
```

Tags pushed to the registry appear automatically in the repository's Tags section in the web UI.

> **Note:** Docker daemon must be configured to allow `localhost:5000` as an insecure registry. See [README.md](../README.md#pushing-docker-images-to-the-local-registry) for setup instructions.

---

## Analytics Query Syntax

The analytics search at `/analytics/` supports a custom query language in addition to free-text search.

**Fields:** `level`, `message`, `content` (alias for message), `logger`

**Operators:** `AND`, `OR`, `NOT`, `=`, `CONTAINS`, `(` `)`

**Examples:**

```
level = ERROR
```
```
level = WARNING OR level = ERROR
```
```
(level = ERROR OR level = WARNING) AND content CONTAINS "database"
```
```
NOT level = INFO AND message CONTAINS "failed"
```
```
logger CONTAINS "repositories" AND level = ERROR
```
