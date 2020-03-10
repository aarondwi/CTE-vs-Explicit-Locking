Writable CTE vs Locking
-----------------------

Example (performance, correctness) of using PostgreSQL's writable CTE vs locking (with FOR UPDATE) and blind update (multiple call, without locking). Here, the use case is __only use coupon once for each users, and all data should be properly recorded__

Why?
-----------------------

Sometimes, you want to speed-up your database transaction by reducing the number of calls. Of course, while still being safe. This repo gives an example about how to achieve that.

How to run
-----------------------

1. update config.py to point to your postgressql database
2. run setup.sql before each run
3. run main.py, with one of the following arguments
  * cte ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/writablecte.py))
  * lock ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/normal_style_for_update.py))
  * wolock ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/normal_style_wo_explicit_locking.py))

Details
-----------------------

The code runs in 10 threads
**cte**: combine all transfer code into 1 sql, resulting in only 1 db-call. Locking benefits from Postgres write-lock. __safe and fast__
```python
cursor.execute("""
  WITH cte AS (
    UPDATE coupons
    SET amount=amount-1
    WHERE code = %s
    RETURNING id
  )
  INSERT INTO user_coupon_usage
  SELECT id, %s
  FROM cte
""", (self.code, user_id))
```

**lock**: using explicit locking (`FOR UPDATE` clause), does multiple db calls. __safe but slow__
```python
cursor.execute("SELECT * FROM coupons WHERE code = %s FOR UPDATE", (self.code, ))
coupon_row = cursor.fetchone()
new_amount = coupon_row['amount'] - 1
coupon_id = coupon_row['id']
cursor.execute("UPDATE coupons SET amount = %s WHERE id = %s", (new_amount, coupon_id))
cursor.execute("INSERT INTO user_coupon_usage VALUES (%s, %s)", (coupon_id, user_id))
```

**wolock**: blindly checking the database record, do some computation, and then updating the data. __neither safe nor fast__
```python
cursor.execute("SELECT * FROM coupons WHERE code = %s", (self.code, ))
coupon_row = cursor.fetchone()
new_amount = coupon_row['amount'] - 1
coupon_id = coupon_row['id']
cursor.execute("UPDATE coupons SET amount = %s WHERE id = %s", (new_amount, coupon_id))
cursor.execute("INSERT INTO user_coupon_usage VALUES (%s, %s)", (coupon_id, user_id))
```

Result
-----------------------

All of these numbers are taken at Windows 10 Pro, postgresql 11.2, Core-i7 8550U, 16GB of RAM, 512GB NVMe SSD

**Time result: (all in seconds)**
| run-number/result |   cte   |   lock   |  wolock  |
| ----------------- |:--------|----------|---------:|
| run-1             | 4.40147 | 20.93568 | 11.56369 |
| run-2             | 5.15701 | 21.00785 | 11.78913 |
| run-3             | 4.53813 | 20.90705 | 12.52875 |

**Final coupon count:**
| run-number/result | cte |  lock | wolock |
| ----------------- |:----|-------|-------:|
| run-1             |  0  |   0   |  8746  |
| run-2             |  0  |   0   |  8705  |
| run-3             |  0  |   0   |  8712  |

Beware of the time result, `wolock` seems fast, but it is prone to __race-condition__, which means `wolock` **SHOULD NOT** be used in production settings