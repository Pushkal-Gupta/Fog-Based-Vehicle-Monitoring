

# 📁 `app/` — Application Root

Everything related to the FastAPI app lives here.

```
app/
 ├── main.py
 ├── core/
 ├── api/
 ├── models/
 ├── repositories/
 ├── services/
 └── utils/
```

---

## 📄 `main.py` — App Bootstrapper

**What it does**

* Creates the FastAPI app
* Loads config
* Connects routers
* Starts the server

**Illustration**

```
[ Server Starts ]
        ↓
[ main.py ]
        ↓
[ FastAPI App Ready ]
```

No business logic here. Only wiring.

---

# 📁 `core/` — Infrastructure Layer

Low-level stuff the whole app depends on.

```
core/
 ├── config.py
 ├── db.py
 └── security.py
```

### `config.py`

* Reads environment variables
* Central place for settings

```
.env → config.py → rest of app
```

---

### `db.py`

* Creates MongoDB connection (Motor)
* Exposes database object

```
MongoDB
   ↑
db.py
```

No queries here — only connection setup.

---

### `security.py`

* API keys
* Auth checks (edge, cloud AI)

```
Request → security.py → allow / reject
```

---

# 📁 `api/` — HTTP Boundary (Thin Layer)

This is **how the outside world talks to you**.

```
api/
 ├── health.py
 ├── ingest.py
 ├── intelligence.py
 └── insights.py
```

### Important Rule

❌ No DB code
❌ No business logic
✅ Call services only

---

### `health.py`

Simple health checks.

```
Client → /health → OK
```

---

### `ingest.py`

Edge sends intelligence data here.

```
Edge
  ↓
ingest.py
  ↓
ingest_service
```

---

### `intelligence.py`

Reads stored intelligence for:

* Frontend dashboard
* Cloud AI

```
Frontend / Cloud AI
        ↓
intelligence.py
        ↓
repository
```

---

### `insights.py`

Cloud AI sends **long-term recommendations** here.

```
Cloud AI
   ↓
insights.py
   ↓
insights_repo
```

---

# 📁 `models/` — Data Contracts (Very Important)

Defines **what data is allowed**.

```
models/
 ├── ingest.py
 ├── intelligence.py
 ├── insights.py
 └── responses.py
```

### `ingest.py`

Schema for **edge → backend** payload.

```
Incoming JSON
   ↓
Pydantic Model
   ↓
Validated Data
```

---

### `intelligence.py`

Schema for data **stored & read back**.

```
Mongo Document ↔ Pydantic Model
```

---

### `insights.py`

Schema for **cloud AI → backend** payload.

* Flexible
* Versioned

---

### `responses.py`

Common response formats.

```
{ status: "ok" }
```

---

# 📁 `repositories/` — Database Access Layer

This is the **only place** that talks to MongoDB.

```
repositories/
 ├── intelligence_repo.py
 ├── insights_repo.py
 └── state_cache_repo.py
```

### `intelligence_repo.py`

* Insert edge intelligence
* Fetch history / latest

```
Service → Repo → MongoDB
```

---

### `insights_repo.py`

* Store long-term AI insights
* Fetch for dashboard

---

### `state_cache_repo.py`

Maintains **latest-per-vehicle** snapshot.

```
New data → overwrite cache doc
```

This avoids heavy queries.

---

# 📁 `services/` — Business Logic Layer

This is the **brain** of your backend.

```
services/
 ├── ingest_service.py
 └── cache_service.py
```

### `ingest_service.py`

Orchestrates:

1. Validate
2. Store intelligence
3. Update cache

```
API
 ↓
Service
 ↓
Repo + Cache
```

---

### `cache_service.py`

Keeps `vehicle_state_cache` in sync.

---

# 📁 `utils/` — Shared Helpers

Reusable utilities.

```
utils/
 ├── time.py
 └── validators.py
```

Examples:

* Timestamp normalization
* Custom validation rules

---

# 📁 `tests/` — Safety Net

```
tests/
 ├── test_ingest.py
 └── test_insights.py
```

* Tests endpoints
* Tests schema validation

---

