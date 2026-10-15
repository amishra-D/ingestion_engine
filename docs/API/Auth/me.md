# API: `GET /auth/me`

Validates the caller's JWT access token and returns the authenticated user payload.

---

## Endpoint Details
* **Method**: `GET`
* **Path**: `/auth/me`
* **Auth Required**: Yes (`Bearer <token>`)
* **Allowed Roles**: Any valid authenticated role (`ADMIN`, `BROKER`, `DEALER`, `GROUP`)

---

## Request Specification

### Headers
| Header | Required | Format | Description |
| :--- | :---: | :--- | :--- |
| `Authorization` | **Yes** | `Bearer <access_token>` | Signed JWT token received from `/auth/login` |

*No request body or query parameters.*

---

## Response Specification

### Status: `200 OK`
```json
{
  "sub": "admin001",
  "user_id": 1,
  "role": "ADMIN",
  "exp": "2026-10-15T20:44:00Z"
}
```

### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `sub` | `string` | Authenticated username (Subject) |
| `user_id` | `int` | Database `UserId` integer identifier |
| `role` | `string` | User's active RBAC role |
| `exp` | `string` (ISO datetime) | Token expiration timestamp (UTC) |

---

## Error Responses

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | `"Not authenticated"` | Missing `Authorization` header |
| **`401 Unauthorized`** | `"Token has expired"` | JWT token lifetime (8h) exceeded |
| **`401 Unauthorized`** | `"Could not validate credentials"` | Tampered, malformed, or invalid signature |

---

## Quick Example (PowerShell)

```powershell
Invoke-RestMethod -Method Get `
  -Uri "http://localhost:8000/auth/me" `
  -Headers @{ "Authorization" = "Bearer $token" }
```
