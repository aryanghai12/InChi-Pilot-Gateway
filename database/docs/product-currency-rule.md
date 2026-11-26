# Product Currency Rule

## Database responsibility

Product pricing must not receive an implicit currency. The database contract is:

- A product without `price_min` and `price_max` may omit currency.
- A product with either `price_min` or `price_max` must have an explicit
  currency.
- The backend must reject a priced product without currency before saving it.
- Existing records with a stored currency, including `USD`, remain unchanged.
- No new product record should rely on an automatic `USD` default.

## Validation cases

| Price values | Currency | Expected result |
|---|---|---|
| Not supplied | Not supplied | Valid draft |
| Supplied | Supplied | Valid if the currency is approved |
| Supplied | Not supplied | Reject |
| Not supplied | Supplied | Accept only if supported by the product workflow |

## Migration impact

The product registry model is owned by the backend integration area. Any change
that removes a database-level currency default must be implemented by the
backend owner through the authoritative Django migration history.

Before such a migration is created, confirm:

1. Existing product rows have valid stored currency values or are intentionally
   blank.
2. The backend serializer rejects priced products without currency.
3. API and database tests cover the validation cases above.
4. The migration is reviewed by the database owner and backend owner.

This document records the database contract only; it does not change the
registry model or backend validation code.
