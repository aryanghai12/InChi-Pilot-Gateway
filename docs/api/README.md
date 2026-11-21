# InChi Pilot Gateway — API Specifications & Contracts

**Owner:** Abhishek Kumar (Application Backend and Access-Control Engineer)  
**Co-Owner:** Priyanka Singh (Frontend Web and Client-Side Integration Engineer)  
**Status:** OpenAPI 3.0.3 Specification Active — Updated Week 4

---

## 1. Authoritative OpenAPI Schema

The backend Django REST Framework application uses `drf-spectacular` to generate the authoritative OpenAPI 3.0.3 specification:

- **Schema File:** [`openapi.yaml`](openapi.yaml) (OpenAPI 3.0.3)
- **Interactive Swagger UI:** Accessible at `http://localhost:3000/api/schema/swagger-ui/` when running the application.

---

## 2. Generating & Syncing Types

To ensure full type safety between Django REST Framework and the Next.js frontend, types are generated directly from `openapi.yaml`:

### Step 1: Export Schema from Django
```bash
docker compose exec backend python manage.py spectacular --file ../docs/api/openapi.yaml
```

### Step 2: Generate TypeScript Definitions
```bash
cd frontend
npx openapi-typescript ../docs/api/openapi.yaml -o src/lib/api/schema.d.ts
```

The resulting `schema.d.ts` is consumed by `src/lib/api/types.ts` and TanStack Query client hooks.

