from threading import Thread

import psycopg2

from db_util import get_connection

class WithoutLockingAccess(Thread):
  def __init__(self, queue, pool, code):
    super().__init__()
    self.q = queue
    self.pool = pool
    self.code = code

  def run(self):
    while True:
      user_id = self.q.get()
      with get_connection(self.pool) as conn:
        conn.set_isolation_level(1) # READ_COMMITTED
        try:
          with conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM coupons WHERE code = %s", (self.code, ))
            coupon_row = cursor.fetchone()
            new_amount = coupon_row['amount'] - 1
            if new_amount < 0:
              raise AssertionError("coupons should not go negative")
            coupon_id = coupon_row['id']
            cursor.execute("UPDATE coupons SET amount = %s WHERE id = %s", (new_amount, coupon_id))
            cursor.execute("INSERT INTO user_coupon_usage VALUES (%s, %s)", (coupon_id, user_id))
          conn.commit()
        except:
          conn.rollback()
      self.q.task_done()
