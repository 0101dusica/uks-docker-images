# API Documentation

This document describes the available API endpoints and their usage.

## User Registration

**Endpoint:** `/api/users/register/`

**Method:** POST

**Description:**
Register a new user account. Returns the created user data on success.

**Request Body:**
```
{
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "password": "StrongPassword123!"
}
```

**Response (201 Created):**
```
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "role": "user"
}
```

**Response (400 Bad Request):**
```
{
  "email": ["user with this email already exists."]
}
```

---

_This file should be updated as new endpoints are added._
