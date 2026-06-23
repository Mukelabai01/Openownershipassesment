# Architecture & Design Patterns

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (React + Vite)                    │
│  - useAuth hook (login, refresh, logout)                    │
│  - React Query (data fetching & caching)                    │
│  - React Hook Form + Zod validation                         │
│  - Pages: Login, ApplicationList, ApplicationView, Editor   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ axios client with Authorization header
┌─────────────────────────────────────────────────────────────┐
│              Backend (Django 4.2 + DRF)                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Accounts App (JWT Authentication)                        │ │
│  │ - TokenObtainView → access token + refresh cookie       │ │
│  │ - TokenRefreshView → token rotation                     │ │
│  │ - MeView, LogoutView                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Applications App (Workflow & REST API)                   │ │
│  │ - ApplicationViewSet (CRUD + transitions + audit)       │ │
│  │ - ApplicationSerializer (validation & DTOs)             │ │
│  │ - Permissions (CanEditDraft, IsReviewer)               │ │
│  │ - WorkflowService (state machine + authorization)       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Audits App (Append-Only Audit Log)                       │ │
│  │ - AuditLog model (immutable event store)                │ │
│  │ - Index: (application_id, created_at)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Database (SQLite local, PostgreSQL production)           │ │
│  │ - auth_user (Django built-in)                           │ │
│  │ - applications_application                              │ │
│  │ - audits_auditlog                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Architectural Decisions

### 1. **Service Layer Isolation**

The `WorkflowService` encapsulates all workflow logic, not the view layer.

**Benefits**:

- Single source of truth for state machine rules
- Reusable across views, APIs, CLI commands
- Testable in isolation
- Clear separation of concerns

**Implementation** ([apps/applications/services/workflow.py](../backend/apps/applications/services/workflow.py)):

```python
class WorkflowService:
    ALLOWED_TRANSITIONS = {
        Application.Status.DRAFT: [Application.Status.SUBMITTED],
        Application.Status.SUBMITTED: [Application.Status.UNDER_REVIEW],
        # ... more transitions
    }

    @staticmethod
    def transition(app_id, target_status, user, comment=None):
        # 1. Authorization checks
        # 2. State validation
        # 3. Transactional audit log
        # 4. AuditLog.objects.create() within transaction.atomic()
```

**Why not let the ViewSet handle this?**

- ViewSets are tied to HTTP concerns (serializers, status codes)
- Testing the service is simpler than mocking DRF request objects
- If we add CLI commands, we reuse the service; no code duplication

---

### 2. **Transactional Audit Logging**

All state transitions are logged atomically with the status change.

**Implementation**:

```python
with transaction.atomic():
    # 1. Update application status
    app.status = target_status
    app.save()

    # 2. Create immutable audit record
    AuditLog.objects.create(
        application_id=app.id,
        actor=user,
        from_status=current_status,
        to_status=target_status,
        comment=comment,
        metadata={...}
    )
```

**Benefits**:

- Both the status change and audit record succeed or fail together
- No orphaned audit records
- Forensic trail is guaranteed to be complete

**Why not use Django signals?**

- Signals execute outside the atomic block by default
- Signals introduce hidden dependencies (harder to debug)
- Service layer approach is more explicit and testable

---

### 3. **Double Authorization Checks**

Authorization is checked both at the view level (DRF permissions) and service level.

**View Level** (apps/applications/permissions.py):

```python
class CanEditDraft(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.status == Application.Status.DRAFT and obj.owner_id == request.user.id
```

**Service Level** (apps/applications/services/workflow.py):

```python
if target_status == Application.Status.SUBMITTED and user.id != app.owner_id:
    raise TransitionPermissionDenied(...)
```

**Why duplicate?**

- View permissions are HTTP-specific and don't apply if we add CLI/webhooks
- Service permissions are the source of truth
- Defense-in-depth: view layer catches common mistakes fast, service layer is the authoritative gate

---

### 4. **JWT Authentication with HttpOnly Refresh Cookies**

Short-lived access tokens + long-lived refresh tokens in httpOnly cookies.

**Flow**:

1. **Login** → `/accounts/token/` returns access token in JSON, sets refresh cookie (httpOnly)
2. **Access resource** → Authorization header with access token
3. **Token expires** → `/accounts/token/refresh/` uses cookie, returns new access token, rotates refresh token
4. **Logout** → `/accounts/logout/` clears refresh cookie

**Security Benefits**:

- Access tokens can be stolen from localStorage → short TTL mitigates
- Refresh tokens in httpOnly cookies → XSS cannot steal them
- Cookie SameSite=Lax → CSRF protection built-in
- Token rotation on refresh → limits window of exposure

**Why not use traditional sessions?**

- Sessions are server-stateful; refresh tokens can be stored on client
- Stateless design scales better (no session store needed)
- Easier to implement CORS (tokens are explicit in Authorization header)

---

### 5. **Serializer-Based Validation**

DRF serializers handle input validation and deserialization.

**Example** (apps/applications/serializers.py):

```python
class ApplicationDetailSerializer(serializers.ModelSerializer):
    def validate(self, data):
        instance = self.instance
        if instance and instance.status != Application.Status.DRAFT:
            raise ValidationError("Only DRAFT applications can be edited")
        return data
```

**Why serializers?**

- Unified validation for both API and ORM
- Automatic deserialization (JSON → Python objects)
- Composable validators
- DRF exception handling converts to HTTP 400 automatically

---

## Error Handling Strategy

### Error Response Format

```json
{
  "error": {
    "code": "TRANSITION_PERMISSION_DENIED",
    "message": "Only reviewers can transition to UNDER_REVIEW",
    "details": null
  }
}
```

### Error Mapping

| Exception                    | HTTP Status | Error Code                     |
| ---------------------------- | ----------- | ------------------------------ |
| `IllegalTransition`          | 400         | `INVALID_TRANSITION`           |
| `TransitionPermissionDenied` | 403         | `TRANSITION_PERMISSION_DENIED` |
| `ValidationError`            | 400         | `VALIDATION_ERROR`             |
| Unhandled Exception          | 500         | `INTERNAL_ERROR`               |

**Implementation** (apps/applications/views.py):

```python
def error_response(exc):
    if isinstance(exc, IllegalTransition):
        return Response({"error": {"code": "INVALID_TRANSITION", ...}}, status=400)
    elif isinstance(exc, TransitionPermissionDenied):
        return Response({"error": {"code": "TRANSITION_PERMISSION_DENIED", ...}}, status=403)
    # ... more mappings
```

**Why custom error format?**

- Explicit error codes enable client-side error handling
- Structured format is more parseable than Django's default
- Future: can add localization by mapping codes to messages

---

## Data Model

### Application

- **Status** (TextChoices): DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED
- **owner** (FK → auth.User): The applicant who created it
- **title** (CharField): Application title
- **content** (JSONField): Arbitrary application data (flexible schema)
- **created_at**, **updated_at** (DateTimeField): Timestamps
- **submitted_at** (DateTimeField, nullable): When first transitioned to SUBMITTED

**Why JSONField for content?**

- Flexible schema: no need to predefined all fields
- Supports nested structures (team info, budget breakdown, etc.)
- Scalable: can evolve without migrations
- Trade-off: not queryable by field (but that's okay; we don't filter by "team_size")

### AuditLog

- **application_id** (UUID, denormalized): Which application changed
- **actor_id** (FK → auth.User, nullable): Who made the change (null = system)
- **from_status**, **to_status** (CharField): Transition details
- **comment** (CharField, nullable): Why the transition happened
- **metadata** (JSONField): Extra context (e.g., rejection reason)
- **created_at** (DateTimeField): When it happened

**Index Strategy**:

- `(application_id, created_at)`: Fast audit trail retrieval per application

---

## Testing Strategy

### Unit Tests

- **test_workflow.py**: Test `WorkflowService` state transitions, authorization, validation
- **test_permissions.py**: Test DRF permission classes in isolation

### Integration Tests

- **test_workflow_integration.py**: Full flow: login → create → submit → approve with audit verification

**Running Tests**:

```bash
cd backend
python -m pytest apps/ -v
```

---

## Deployment Considerations

### PostgreSQL for Production

Production settings use PostgreSQL (apps/applications/models.py uses UUIDField which is better supported in PostgreSQL).

### Environment Variables

```bash
# Database
POSTGRES_DB=submission_db
POSTGRES_USER=submission
POSTGRES_PASSWORD=<secret>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
DEBUG=False
SECRET_KEY=<secret>
ALLOWED_HOSTS=example.com,api.example.com
```

### HTTPS/SSL

In production, ensure:

- `DEBUG=False`
- `SECURE_COOKIES=True` (Django middleware)
- `CSRF_COOKIE_SECURE=True`
- `SESSION_COOKIE_SECURE=True`
- Refresh token cookie: `secure=True`

---

## Future Enhancements

1. **Refresh Token Blacklisting**: On logout, add token ID to a Redis blacklist
2. **Rate Limiting**: Use django-ratelimit to prevent brute force attacks
3. **Permission Caching**: Cache reviewer status (is_staff) to avoid repeated DB queries
4. **Webhook Events**: On state transition, publish events to external systems
5. **Approval Workflow**: Multi-level approvals (e.g., manager → director → exec)
6. **Notifications**: Email/Slack alerts on state changes
7. **Versioning**: Track application revisions for audit trails

---

## Project Layout

```
submission-workflow/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── accounts/        # JWT authentication
│   │   ├── applications/    # Workflow & REST API
│   │   ├── audits/          # Audit logging
│   │   └── common/          # Shared utilities
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useAuth.tsx       # Auth context & lifecycle
│   │   ├── api/
│   │   │   └── client.ts         # Axios instance with auth
│   │   ├── pages/                # View components
│   │   ├── components/           # Reusable UI components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── API_SPEC.md
│   ├── ARCHITECTURE.md
│   └── SCHEMA.md
├── docker-compose.yml
├── Dockerfile (backend)
├── Dockerfile (frontend)
└── README.md
```
