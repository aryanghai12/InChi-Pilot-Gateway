# Frontend Integration Guide — Module M5: Buyer Demand & Requirements

**Author:** Abhishek Kumar (Backend & Access Control)  
**Target:** Priyanka Singh (Frontend Web & Client Integration)  
**Status:** Approved & Implemented in Backend (`backend/apps/demand/`)  
**Base URL:** `/api/v1/requirements/`  
**Automated Tests:** 29/29 Passing (`manage.py test apps`)

---

## 1. Overview & Architecture Alignment

Module M5 manages commercial buyer procurement requirements based on **Buyer Requirement Field Dictionary v1.4 (MVP Aligned)**.

### Key Architectural Rules (Decision D-13 & D-15):
1. **No Separate Buyer Profile:** `buyer_organisation_name` is stored directly on the requirement record.
2. **No External Buyer Verification:** `buyer_verification_status` is excluded for MVP.
3. **Strict 3 Workflow Statuses:**
   - `"draft"` (`"Draft"` in UI)
   - `"ready_for_matching"` (`"Ready for matching"` in UI)
   - `"closed"` (`"Closed"` in UI)
4. **Central RBAC Policy:**
   - Commercial Analysts can create, edit, mark ready, and close requirements.
   - Platform Admins and Reviewers have read-only inspection access.

---

## 2. API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/requirements/` | List requirements (supports search & filters) | Session Auth (Any Role) |
| `POST` | `/api/v1/requirements/` | Create a new requirement (Draft or Complete) | Commercial Analyst |
| `GET` | `/api/v1/requirements/{id}/` | Retrieve full requirement details | Session Auth (Any Role) |
| `PATCH` | `/api/v1/requirements/{id}/` | Update requirement fields | Commercial Analyst |
| `POST` | `/api/v1/requirements/{id}/mark-ready/` | Validate gate and transition to `ready_for_matching` | Commercial Analyst |
| `POST` | `/api/v1/requirements/{id}/close/` | Transition requirement to `closed` | Commercial Analyst |

---

## 3. Query Parameters for List Endpoint (`GET /api/v1/requirements/`)

- `?status=draft` or `?status=ready_for_matching` or `?status=closed`
- `?category=Agriculture and Food`
- `?market=China`
- `?search=<text>` (Searches `buyer_organisation_name`, `requirement_title`, `buyer_reference`, `delivery_location`)

> **Note on DRF Pagination:**
> The list endpoint returns DRF's standard paginated envelope:
> ```json
> {
>   "count": 5,
>   "next": null,
>   "previous": null,
>   "results": [ ... ]
> }
> ```
> In TanStack Query / React hooks, extract `res.results || res`.

---

## 4. Dual-Compatibility Built into Backend

To ensure your existing frontend code in `frontend/src/app/(workspace)/requirements/page.tsx` works out-of-the-box without crashes, the backend includes **automatic normalizers and aliases**:

1. **Identifier Aliases:** Backend returns both **`id`** and **`requirement_id`** with identical UUID values.
2. **Category Aliases:** Backend accepts both **`product_category`** and **`product_category_id`**.
3. **Status Casing:** Backend accepts both lowercase (`"draft"`, `"ready_for_matching"`, `"closed"`) and frontend Title Case (`"Draft"`, `"Ready for Matching"`, `"Closed"`).
4. **Order Frequency:** Backend accepts both `"one_off"`, `"One-off"`, `"Monthly"`, `"Quarterly"`, `"Annual"`.
5. **Unit Normalization:** Backend automatically normalizes units (e.g. `"tonnes"` -> `"MT"`, `"kg"` -> `"KG"`).
6. **Computed Readiness Attributes:** Every requirement returned by the API automatically includes:
   - `completeness_status`: `"Complete"` or `"Incomplete"`
   - `matching_ready`: `true` if status is `ready_for_matching`, else `false`
   - `blocking_reasons`: `string[]` (list of reasons why requirement cannot be marked ready yet)

---

## 5. Payloads & Examples

### A. Create / Save Draft Requirement
**Endpoint:** `POST /api/v1/requirements/`

**Minimum Draft Payload:**
```json
{
  "buyer_organisation_name": "Shanghai Agro Trading Corp",
  "product_category_id": "Agriculture and Food",
  "requirement_title": "Organic Basmati Rice 1121",
  "target_market": "China",
  "order_frequency": "One-off"
}
```

**Full Creation Payload (with criteria):**
```json
{
  "buyer_organisation_name": "Shanghai Agro Trading Corp",
  "buyer_reference": "PO-SH-2026-089",
  "requirement_title": "Organic Basmati Rice 1121",
  "target_market": "China",
  "product_category_id": "Agriculture and Food",
  "product_specifications": "Extra long grain, moisture max 12%, broken grains under 2%",
  "quantity_value": 100,
  "quantity_unit": "tonnes",
  "order_frequency": "One-off",
  "target_price_min": 850.00,
  "target_price_max": 950.00,
  "currency_code": "USD",
  "price_basis": "FOB",
  "delivery_location": "Tianjin Port, China",
  "delivery_window_start": "2027-01-15",
  "delivery_window_end": "2027-02-28",
  "required_lead_time_value": 30,
  "required_lead_time_unit": "days",
  "mandatory_criteria": [
    { "id": "m-1", "name": "Valid Organic Accreditation Certificate", "type": "mandatory" },
    { "id": "m-2", "name": "ISO 22000 Food Safety Certification", "type": "mandatory" }
  ],
  "preferred_criteria": [
    { "id": "p-1", "name": "Prior China export track record", "type": "preferred" }
  ],
  "requirement_notes": "First trial shipment; recurring monthly orders upon successful customs inspection.",
  "requirement_status": "Draft"
}
```

**Response (HTTP 201 Created):**
```json
{
  "id": "e4f8d9b2-3c1a-4d5e-8f2a-7b9c1d3e5f7a",
  "requirement_id": "e4f8d9b2-3c1a-4d5e-8f2a-7b9c1d3e5f7a",
  "buyer_organisation_name": "Shanghai Agro Trading Corp",
  "buyer_reference": "PO-SH-2026-089",
  "owner": "00000000-0000-0000-0000-000000000001",
  "requirement_title": "Organic Basmati Rice 1121",
  "target_market": "China",
  "product_category": "Agriculture and Food",
  "product_category_id": "Agriculture and Food",
  "product_specifications": "Extra long grain, moisture max 12%, broken grains under 2%",
  "quantity_value": "100.00",
  "quantity_unit": "MT",
  "order_frequency": "one_off",
  "target_price_min": "850.00",
  "target_price_max": "950.00",
  "currency_code": "USD",
  "price_basis": "FOB",
  "delivery_location": "Tianjin Port, China",
  "delivery_window_start": "2027-01-15",
  "delivery_window_end": "2027-02-28",
  "required_lead_time_value": 30,
  "required_lead_time_unit": "days",
  "mandatory_criteria": [
    { "id": "m-1", "name": "Valid Organic Accreditation Certificate", "type": "mandatory" },
    { "id": "m-2", "name": "ISO 22000 Food Safety Certification", "type": "mandatory" }
  ],
  "preferred_criteria": [
    { "id": "p-1", "name": "Prior China export track record", "type": "preferred" }
  ],
  "required_evidence": [],
  "priority_weights": {},
  "buyer_preferences": {},
  "requirement_notes": "First trial shipment; recurring monthly orders upon successful customs inspection.",
  "requirement_status": "draft",
  "completeness_status": "Complete",
  "matching_ready": false,
  "blocking_reasons": [],
  "version": 1,
  "created_by": "00000000-0000-0000-0000-000000000001",
  "created_at": "2026-11-13T17:15:00.000000Z",
  "updated_at": "2026-11-13T17:15:00.000000Z"
}
```

---

### B. Mark Ready for Matching (`POST /api/v1/requirements/{id}/mark-ready/`)

When a user clicks **"Mark Ready for Matching"**:
- Frontend calls: `POST /api/v1/requirements/{id}/mark-ready/` (no body required, or empty `{}`).
- The backend runs the strict **BUY-032 Readiness Gate**:
  - `buyer_organisation_name` (non-empty)
  - `target_market` (non-empty)
  - `product_category` (valid 1 of 7)
  - `quantity_value` (> 0) and `quantity_unit` (approved)
  - `delivery_location` (destination specified)
  - Conditional Price Gate: if price provided, `target_price_min <= target_price_max`, `currency_code` and `price_basis` present.

**If Incomplete (HTTP 400 Bad Request):**
```json
{
  "code": "validation_error",
  "message": "Requirement cannot be marked ready for matching due to missing mandatory criteria.",
  "field_errors": {
    "blocking_reasons": [
      "Positive procurement quantity is required.",
      "Delivery destination port or city in China is required."
    ]
  },
  "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

**If Complete (HTTP 200 OK):**
```json
{
  "message": "Requirement 'Organic Basmati Rice 1121' successfully marked as Ready for Matching.",
  "requirement": {
    "id": "e4f8d9b2-3c1a-4d5e-8f2a-7b9c1d3e5f7a",
    "requirement_id": "e4f8d9b2-3c1a-4d5e-8f2a-7b9c1d3e5f7a",
    "requirement_status": "ready_for_matching",
    "completeness_status": "Complete",
    "matching_ready": true,
    "version": 2
  }
}
```

---

### C. Close Requirement (`POST /api/v1/requirements/{id}/close/`)

When a requirement is fulfilled or canceled:
- Frontend calls: `POST /api/v1/requirements/{id}/close/`
- **Response (HTTP 200 OK):**
```json
{
  "message": "Requirement 'Organic Basmati Rice 1121' has been closed.",
  "requirement": {
    "id": "e4f8d9b2-3c1a-4d5e-8f2a-7b9c1d3e5f7a",
    "requirement_status": "closed",
    "version": 3
  }
}
```

---

## 6. Optimistic Concurrency & 409 Conflict Handling

To prevent two analysts from overwriting each other's edits (per `BUY-030`):
- When submitting `PATCH /api/v1/requirements/{id}/`, include the current `version`:
  ```json
  {
    "requirement_title": "Updated Title",
    "version": 1
  }
  ```
- If another user updated the record in the meantime, backend returns **HTTP 409 Conflict**:
  ```json
  {
    "code": "conflict",
    "message": "This requirement record has been modified by another process. Please refresh.",
    "field_errors": {},
    "correlation_id": "..."
  }
  ```
- Frontend should simply display this message and prompt the user to refresh the page.

---

## 7. Connecting Frontend Page to Live Backend

In `frontend/src/app/(workspace)/requirements/page.tsx`:
Replace the mock/local fallback with live TanStack Query mutations:
```typescript
// Create Requirement Mutation
const createRequirementMutation = useMutation({
  mutationFn: (payload: any) =>
    apiFetch<BuyerRequirement>("/api/v1/requirements/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["requirements"] });
  },
});

// Mark Ready Action
const markReadyMutation = useMutation({
  mutationFn: (reqId: string) =>
    apiFetch<{ message: string; requirement: BuyerRequirement }>(`/api/v1/requirements/${encodeURIComponent(reqId)}/mark-ready/`, {
      method: "POST",
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["requirements"] });
  },
});

// Close Action
const closeRequirementMutation = useMutation({
  mutationFn: (reqId: string) =>
    apiFetch<{ message: string; requirement: BuyerRequirement }>(`/api/v1/requirements/${encodeURIComponent(reqId)}/close/`, {
      method: "POST",
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["requirements"] });
  },
});
```

All endpoints are live, tested, and ready!
