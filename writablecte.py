from threading import Thread
from db_util import get_connection

class WritableCte(Thread):
  def __init__(self, queue, pool, code):
    super().__init__()
    self.q = queue
    self.pool = pool
    self.code = code

  def run(self):
    while True:
      user_id = self.q.get()
      with get_connection(self.pool) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
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
      self.q.task_done()
