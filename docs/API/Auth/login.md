# API: `POST /auth/login`

Authenticates credentials and returns a signed JWT access token valid for 8 hours.

---

## Endpoint Details
* **Method**: `POST`
* **Path**: `/auth/login`
* **Auth Required**: No (Public)
* **Content-Type**: `application/json`

---

## Request Specification

### Body Fields
| Field | Type | Required | Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `username` | `string` | **Yes** | Min 8, Max 50 chars | User login ID (e.g. `admin001`, `dealer01`) |
| `password` | `string` | **Yes** | Min 1 char | User's plain text password |

### Sample Request
```json
{
  "username": "admin001",
  "password": "Password@123"
}
```

---

## Response Specification

### Status: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjAwMSIsInVzZXJfaWQiOjEsInJvbGUiOiJBRE1JTiIsImV4cCI6MTc2MDU4MzgxMH0.xxxx",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin001",
  "role": "ADMIN"
}
```

### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `access_token` | `string` | Signed HS256 JWT Bearer token |
| `token_type` | `string` | Token format indicator (`bearer`) |
| `user_id` | `int` | Primary key from `dbo.UserAccount` |
| `username` | `string` | User's login identifier |
| `role` | `string` | Assigned RBAC role (`ADMIN`, `BROKER`, `DEALER`, `GROUP`) |

---

## Error Responses

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | `"Invalid username or password"` | Username does not exist or password hash mismatch |
| **`403 Forbidden`** | `"Account is inactive or disabled"` | User account has `isActive = 0` in database |
| **`422 Unprocessable`** | `"String should have at least 8 characters"` | `username` is shorter than 8 characters or missing |

---

## Quick Example (PowerShell)

```powershell
$response = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/auth/login" `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"username":"admin001","password":"Password@123"}'

$token = $response.access_token
Write-Host "Obtained JWT: $token"
```
