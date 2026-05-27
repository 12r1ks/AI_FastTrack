# Database Schema

SQLite. All datetimes stored as `YYYY-MM-DD HH:MM` (no seconds).

---

## Table: `spots`

Static reference data — seeded once, not modified at runtime.

| Column       | Type     | Notes                              |
|--------------|----------|------------------------------------|
| `id`         | TEXT PK  | e.g. `A1`, `B1`, `T3`             |
| `location`   | TEXT     | `central` or `east`               |
| `type`       | TEXT     | `standard`, `premium`, `truck`    |
| `hourly_rate`| REAL     |                                    |
| `daily_rate` | REAL     |                                    |

---

## Table: `bookings`

Holds both client reservations and company blocks.

| Column         | Type              | Notes                                    |
|----------------|-------------------|------------------------------------------|
| `id`           | INTEGER PK        | Auto-increment                           |
| `spot_id`      | TEXT FK → spots   |                                          |
| `location`     | TEXT              | `central` or `east`                     |
| `booking_type` | TEXT              | `reservation` or `block`                |
| `name`         | TEXT              | Client full name OR `CityPark`          |
| `car_number`   | TEXT              | Nullable for blocks                      |
| `reason`       | TEXT              | Nullable for reservations                |
| `start_dt`     | DATETIME          | YYYY-MM-DD HH:MM                                 |
| `end_dt`       | DATETIME          | YYYY-MM-DD HH:MM                                 |
| `status`       | TEXT              | `approved`, `cancelled` |
| `created_at`   | DATETIME          | YYYY-MM-DD HH:MM, set on insert                 |

### Availability check

A spot is unavailable for a requested `[start, end)` range if any booking exists where:

```sql
spot_id = ? AND location = ? AND status = 'approved'
AND start_dt < requested_end AND end_dt > requested_start
```

### Notes

- `pending` bookings do NOT block availability — only `approved` ones do.
- Company blocks use `booking_type = 'block'`, `name = 'CityPark'`, `car_number = NULL`.
- The `(spot_id, location)` pair is the true unique key for a spot.
