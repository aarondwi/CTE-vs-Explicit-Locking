Writable CTE vs Locking
-----------------------

Example (performance, correctness) of using PostgreSQL's writable CTE vs locking (with FOR UPDATE) and blind update (multiple call, without locking). Here, the use case is __only use coupon once for each users, and coupons used should not exceed the predefined coupon numbers__.

Why?
-----------------------

Most people (trust me, even in important business apps) blindly assumes that their code will run serially against database, not using any kind of transaction guarantee or proper locking, which may result in logically corrupted state. For those already knowing, they said `lock makes application slow`. While true, but performance doesn't mean anything if the result is incorrect

How to run
-----------------------

1. run `docker-compose -f docker-compose.env.yml` to setup the db
2. run setup.sql before each run
3. run main.py, with one of the following arguments
  * cte ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/writablecte.py))
  * lock ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/normal_style_for_update.py))
  * wolock ([impl](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/normal_style_wo_explicit_locking.py))

Details
-----------------------

The **lock** and **wolock** code style's mimic those of ORM's, in which the data is read from db, updated in the apps, then updated back to the db. See ([here](https://github.com/aarondwi/CTE-vs-Explicit-Locking/blob/master/ORMStyleCode.py)) for example

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
if new_amount < 0:
  raise AssertionError("coupons should not go negative")
coupon_id = coupon_row['id']
cursor.execute("UPDATE coupons SET amount = %s WHERE id = %s", (new_amount, coupon_id))
cursor.execute("INSERT INTO user_coupon_usage VALUES (%s, %s)", (coupon_id, user_id))
```

**wolock**: blindly checking the database record, do some computation, and then updating the data. __neither safe nor fast__
```python
cursor.execute("SELECT * FROM coupons WHERE code = %s", (self.code, ))
coupon_row = cursor.fetchone()
new_amount = coupon_row['amount'] - 1
if new_amount < 0:
  raise AssertionError("coupons should not go negative")
coupon_id = coupon_row['id']
cursor.execute("UPDATE coupons SET amount = %s WHERE id = %s", (new_amount, coupon_id))
cursor.execute("INSERT INTO user_coupon_usage VALUES (%s, %s)", (coupon_id, user_id))
```

Result
-----------------------

All of these numbers are taken at Windows 10 Pro, postgresql 11.2, Core-i7 8550U, 16GB of RAM, 512GB NVMe SSD

**Time result: (all in seconds)**
| run-number/result |   cte   |   lock  |  wolock  |
| ----------------- |:--------|---------|---------:|
| run-1             | 15.3365 | 38.3434 | 83.48423 |
| run-2             | 16.0106 | 38.4878 | 89.16248 |
| run-3             | 15.6987 | 42.4052 | 174.5555 |

**Final coupon count: (select amount from coupons where id=1)**
| run-number/result | cte |  lock | wolock |
| ----------------- |:----|-------|-------:|
| run-1             |  0  |   0   |   0    |
| run-2             |  0  |   0   |   0    |
| run-3             |  0  |   0   |   0    |

**Number of users who got the coupon: (select count(*) from user_coupon_usage)**
| run-number/result |   cte   |  lock  | wolock |
| ----------------- |:--------|--------|-------:|
| run-1             |  10000  | 10000  |  98152 |
| run-2             |  10000  | 10000  |  96897 |
| run-3             |  10000  | 10000  |  98046 |

As can be seen, the `wolock` doesn't return the correct count for the coupon usages, which means the code is basically *unsafe*. It **SHOULD NOT** be used in production.

The main point here is that before optimizing for performance, ensure that your application can give correct results in spite of concurrency, which is common right now.

And if needed (and possible), you can use some of your data store's feature, such as __postgresql's writable cte__ to compensate for performance. This feature can also delegate the task of checking constraint to the database.