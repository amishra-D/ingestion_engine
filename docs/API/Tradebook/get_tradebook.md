# API: `POST /tradebook/get-tradebook`

Queries the high-performance tradebook read model using bi-directional keyset pagination and database-enforced RBAC scoping.

---

## Endpoint Details
* **Method**: `POST`
* **Path**: `/tradebook/get-tradebook`
* **Auth Required**: Yes (`Bearer <token>`)
* **Allowed Roles**: `ADMIN`, `BROKER`, `DEALER`, `GROUP`
* **Content-Type**: `application/json`

---

## RBAC Authorization Rules

| Caller Role | Permitted Filter Fields | Effective Query Scope |
| :--- | :--- | :--- |
| **`ADMIN`** | Any (`accountcode`, `groupcode`, `userid`) | Global. Can query across all accounts, groups, and dealers. |
| **`BROKER`** | `accountcode` only | Restricted to the broker's authorized account code. |
| **`DEALER`** | None (ignored) | Strictly filtered by accounts mapped to `current_user.username` in `dbo.Config_DealerMap`. |

---

## Request Specification

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Body Fields
| Field | Type | Default | Validation Rule | Description |
| :--- | :--- | :---: | :--- | :--- |
| `accountcode` | `string` | `""` | Optional | Account code filter (Admin / Broker). Ignored for Dealers. |
| `groupcode` | `string` | `""` | Optional | Group category filter (Admin only). |
| `cursor_start` | `string \| int \| null` | `null` | Optional | Base64 Trade ID for **backward** seek (fetch newer trades). |
| `cursor_end` | `string \| int \| null` | `null` | Optional | Base64 Trade ID for **forward** seek (fetch older trades). |
| `limit` | `int` | `10` | `10 <= limit <= 5000` | Number of trade records per page. |

> **Cursor Rule**: You can supply either `cursor_end` (forward) or `cursor_start` (backward), never both. First page passes `null` for both.

### Sample Requests

#### 1. First Page (Initial Load)
```json
{
  "limit": 10
}
```

#### 2. Forward Page (Scroll Down / Next)
```json
{
  "cursor_end": "NTYwOQ==",
  "limit": 10
}
```

#### 3. Backward Page (Scroll Up / Previous)
```json
{
  "cursor_start": "NTYwMA==",
  "limit": 10
}
```

---

## Response Specification

### Status: `200 OK`
```json
{
  "data": [
    {
      "trade_id": 5609,
      "member_code": "MEM001",
      "symbol": "BANKNIFTY",
      "quantity": 30,
      "price": 178.17,
      "trade_time": "2026-10-13 15:03:53.187"
    }
  ],
  "pagination": {
    "cursor_start": "NTYwOQ==",
    "cursor_end": "NTYwMA==",
    "has_prev": false,
    "has_next": true
  }
}
```

### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `data[].trade_id` | `int` | Unique trade identifier (`MainTradeID`) |
| `data[].member_code` | `string` | Exchange member code |
| `data[].symbol` | `string` | Instrument code (e.g. `BANKNIFTY`, `NIFTY`) |
| `data[].quantity` | `int` | Traded share/lot quantity |
| `data[].price` | `decimal` | Execution trade price |
| `data[].trade_time` | `string` | Trade timestamp (`YYYY-MM-DD HH:MM:SS.mmm`) |
| `pagination.cursor_start` | `string \| null` | Base64 Trade ID of the first record on current page |
| `pagination.cursor_end` | `string \| null` | Base64 Trade ID of the last record on current page |
| `pagination.has_prev` | `bool` | True if newer records exist before `cursor_start` |
| `pagination.has_next` | `bool` | True if older records exist after `cursor_end` |

---

## Error Responses

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | `"Not authenticated"` | Missing or expired JWT Bearer token |
| **`403 Forbidden`** | `"Access denied. User role '...' not permitted."` | Unauthorized caller role |
| **`403 Forbidden`** | `"Dealers cannot query arbitrary accounts"` | Dealer attempting to query outside their mapped account list |
| **`422 Unprocessable`** | `"Provide only one cursor per request"` | Both `cursor_start` and `cursor_end` provided in the same request |
| **`422 Unprocessable`** | `"Input should be greater than or equal to 10"` | `limit` parameter is less than 10 |

---

## Quick Example (PowerShell)

```powershell
$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type"  = "application/json"
}

$body = @{
  limit = 10
} | ConvertTo-Json

$page1 = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/tradebook/get-tradebook" `
  -Headers $headers `
  -Body $body

# Next page call using cursor_end:
$nextBody = @{
  cursor_end = $page1.pagination.cursor_end
  limit      = 10
} | ConvertTo-Json

$page2 = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/tradebook/get-tradebook" `
  -Headers $headers `
  -Body $nextBody
```
