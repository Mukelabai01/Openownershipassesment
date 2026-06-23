# API Specification

## Overview

RESTful API for a Submission & Approval Workflow application built with Django REST Framework and djangorestframework-simplejwt for JWT authentication.

**Base URL**: `/api/v1/`

**Authentication**: Bearer token (JWT access token) in `Authorization` header
**Refresh Token**: HttpOnly cookie named `refresh` (Path: `/`, SameSite: Lax, Secure: True in production)

---

## Authentication Endpoints

### POST `/accounts/token/`

Obtain access and refresh tokens via username/password.

**Request Body**:

```json
{
  "username": "alice",
  "password": "password123"
}
```

**Response** (200 OK):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR...",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Developer"
  }
}
```

**Set-Cookie**: `refresh=eyJhbGciOiJIUzI1NiIsInR...; Path=/; HttpOnly; SameSite=Lax`

**Errors**:

- `401 Unauthorized`: Invalid credentials

```json
{ "detail": "Invalid credentials" }
```

---

### POST `/accounts/token/refresh/`

Refresh access token using the refresh token cookie or request body.

**Request Body** (optional - refresh token from cookie takes precedence):

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

**Response** (200 OK):

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR...",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Developer"
  }
}
```

**Errors**:

- `401 Unauthorized`: Refresh token not found or invalid

---

### GET `/accounts/me/`

Get current authenticated user's profile.

**Headers**:

```
Authorization: Bearer {access_token}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Developer"
}
```

**Errors**:

- `401 Unauthorized`: Missing or invalid access token

---

### POST `/accounts/logout/`

Logout by deleting the refresh token cookie.

**Headers**:

```
Authorization: Bearer {access_token}
```

**Response** (200 OK):

```json
{ "detail": "logged out" }
```

**Delete-Cookie**: `refresh`

---

## Application Endpoints

### GET `/applications/`

List all applications (filtered by user role: applicants see own, reviewers see all).

**Headers**:

```
Authorization: Bearer {access_token}
```

**Query Parameters**:

- `status` (optional): Filter by status (DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)
- `owner_id` (optional): Filter by owner (reviewers only)

**Response** (200 OK):

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Project Alpha",
      "status": "SUBMITTED",
      "owner_id": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "submitted_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

**Errors**:

- `401 Unauthorized`: Missing authentication

---

### POST `/applications/`

Create a new application (DRAFT status).

**Headers**:

```
Authorization: Bearer {access_token}
```

**Request Body**:

```json
{
  "title": "Project Alpha",
  "content": {
    "description": "A machine learning pipeline...",
    "technologies": ["Python", "TensorFlow"],
    "team_size": 5,
    "budget_usd": 50000
  }
}
```

**Response** (201 Created):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Project Alpha",
  "status": "DRAFT",
  "owner_id": 1,
  "content": {
    "description": "A machine learning pipeline...",
    "technologies": ["Python", "TensorFlow"],
    "team_size": 5,
    "budget_usd": 50000
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "submitted_at": null
}
```

**Errors**:

- `400 Bad Request`: Missing required fields or validation errors
- `401 Unauthorized`: Missing authentication

---

### GET `/applications/{id}/`

Retrieve a specific application.

**Headers**:

```
Authorization: Bearer {access_token}
```

**Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Project Alpha",
  "status": "SUBMITTED",
  "owner_id": 1,
  "owner": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  },
  "content": {...},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "submitted_at": "2024-01-15T11:00:00Z"
}
```

**Errors**:

- `404 Not Found`: Application does not exist
- `401 Unauthorized`: Missing authentication

---

### PATCH `/applications/{id}/`

Update a DRAFT application (applicant only).

**Headers**:

```
Authorization: Bearer {access_token}
```

**Request Body**:

```json
{
  "title": "Project Alpha - Updated",
  "content": {
    "description": "Updated description...",
    "technologies": ["Python", "TensorFlow", "Kubernetes"],
    "team_size": 6,
    "budget_usd": 60000
  }
}
```

**Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Project Alpha - Updated",
  "status": "DRAFT",
  "owner_id": 1,
  "content": {...},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "submitted_at": null
}
```

**Errors**:

- `403 Forbidden`: Application not in DRAFT status or user is not the owner
- `404 Not Found`: Application does not exist
- `401 Unauthorized`: Missing authentication

---

## Workflow Transition Endpoints

### POST `/applications/{id}/transitions/`

Transition an application through the workflow (state machine).

**Allowed Transitions**:

- DRAFT → SUBMITTED (applicant required, comment optional)
- SUBMITTED → UNDER_REVIEW (reviewer required, comment optional)
- UNDER_REVIEW → APPROVED (reviewer required, comment optional)
- UNDER_REVIEW → DRAFT (reviewer required, comment required)
- UNDER_REVIEW → REJECTED (reviewer required, comment required)

**Headers**:

```
Authorization: Bearer {access_token}
```

**Request Body**:

```json
{
  "target": "SUBMITTED",
  "comment": "Please review my application"
}
```

**Response** (200 OK):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Project Alpha",
  "status": "SUBMITTED",
  "owner_id": 1,
  "content": {...},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "submitted_at": "2024-01-15T11:00:00Z",
  "last_comment": "Please review my application"
}
```

**Errors**:

- `400 Bad Request`: Invalid target status or missing required comment

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Cannot transition from SUBMITTED to DRAFT",
    "details": null
  }
}
```

- `403 Forbidden`: Insufficient permissions (e.g., non-reviewer attempting reviewer action)

```json
{
  "error": {
    "code": "TRANSITION_PERMISSION_DENIED",
    "message": "Only reviewers can transition to UNDER_REVIEW",
    "details": null
  }
}
```

- `404 Not Found`: Application does not exist
- `401 Unauthorized`: Missing authentication

---

### GET `/applications/{id}/audit/`

Get audit log (all state transitions) for an application.

**Headers**:

```
Authorization: Bearer {access_token}
```

**Response** (200 OK):

```json
[
  {
    "id": "uuid-1",
    "application_id": "550e8400-e29b-41d4-a716-446655440000",
    "actor_id": 1,
    "actor": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com"
    },
    "from_status": "DRAFT",
    "to_status": "SUBMITTED",
    "comment": "Please review my application",
    "metadata": {},
    "created_at": "2024-01-15T11:00:00Z"
  },
  {
    "id": "uuid-2",
    "application_id": "550e8400-e29b-41d4-a716-446655440000",
    "actor_id": 2,
    "actor": {
      "id": 2,
      "username": "bob",
      "email": "bob@example.com"
    },
    "from_status": "SUBMITTED",
    "to_status": "UNDER_REVIEW",
    "comment": null,
    "metadata": {},
    "created_at": "2024-01-15T11:30:00Z"
  }
]
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common Error Codes**:

- `INVALID_TRANSITION`: Target status is not allowed from current status
- `TRANSITION_PERMISSION_DENIED`: User lacks permission for this transition
- `INVALID_COMMENT`: Comment is required for this transition but was not provided
- `WORKFLOW_ERROR`: Unexpected error during transition (500)

---

## Pagination

List endpoints support pagination with optional query parameters:

- `page` (default: 1)
- `page_size` (default: 20, max: 100)

Example: `GET /applications/?page=2&page_size=10`

Response includes:

```json
{
  "count": 42,
  "next": "http://api.example.com/api/v1/applications/?page=3&page_size=10",
  "previous": "http://api.example.com/api/v1/applications/?page=1&page_size=10",
  "results": [...]
}
```

---

## Authentication Flow

### Login with Credentials

```
POST /accounts/token/
  → Returns: access token + refresh token (httpOnly cookie)
```

### Access Protected Resources

```
GET /applications/
Headers: Authorization: Bearer {access_token}
  → Returns: list of applications
```

### Refresh Access Token

```
POST /accounts/token/refresh/
Cookie: refresh={refresh_token}
  → Returns: new access token + new refresh token (httpOnly cookie rotation)
```

### Logout

```
POST /accounts/logout/
Headers: Authorization: Bearer {access_token}
  → Clears refresh token cookie
```

---

## Status Codes

| Code | Meaning                                          |
| ---- | ------------------------------------------------ |
| 200  | OK - Request succeeded                           |
| 201  | Created - Resource created                       |
| 400  | Bad Request - Invalid input or state transition  |
| 401  | Unauthorized - Missing or invalid authentication |
| 403  | Forbidden - Insufficient permissions             |
| 404  | Not Found - Resource does not exist              |
| 500  | Internal Server Error                            |

---

## Testing with cURL

### Login

```bash
curl -X POST http://localhost:8000/api/v1/accounts/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

### Create Application

```bash
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Project","content":{"description":"...","team_size":5}}'
```

### Submit Application

```bash
curl -X POST http://localhost:8000/api/v1/applications/{id}/transitions/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"target":"SUBMITTED","comment":"Please review"}'
```

### View Audit Log

```bash
curl -X GET http://localhost:8000/api/v1/applications/{id}/audit/ \
  -H "Authorization: Bearer {access_token}"
```
