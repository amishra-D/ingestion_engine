# API Reference Directory

Base URL: `http://localhost:8000`  
Interactive Documentation: [`/documentation`](http://localhost:8000/documentation) (Scalar UI) | [`/docs`](http://localhost:8000/docs) (Swagger UI)

---

## Endpoint Catalog

The platform exposes authentication and trade query endpoints, documented in individual markdown files below:

### 🔐 Authentication (`/auth`)
* **[`POST /auth/login`](file:///d:/ingestion_engine/docs/API/Auth/login.md)**: Authenticates username & password, returns signed 8-hour HS256 JWT access token with role and user ID.
* **[`GET /auth/me`](file:///d:/ingestion_engine/docs/API/Auth/me.md)**: Validates bearer token and returns current user claims from the token payload.

### 📈 Tradebook (`/tradebook`)
* **[`POST /tradebook/get-tradebook`](file:///d:/ingestion_engine/docs/API/Tradebook/get_tradebook.md)**: High-performance trade query endpoint supporting multi-tier RBAC filtering (Admin/Broker/Dealer) and bidirectional keyset pagination via opaque Base64 Trade ID cursors.

---

## Authentication Standard

All endpoints (except `/auth/login`) require standard HTTP Bearer authentication:

```http
Authorization: Bearer <access_token>
```

Tokens are valid for 8 hours and carry:
* `sub`: Login username
* `user_id`: Integer user identifier
* `role`: RBAC role (`ADMIN`, `BROKER`, `DEALER`, `GROUP`)
* `exp`: UTC expiration timestamp
