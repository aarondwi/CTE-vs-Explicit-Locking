from queue import Queue
from threading import Thread, current_thread
from time import time
from sys import argv

from writablecte import WritableCte
from normal_style_for_update import LockingAccess
from normal_style_wo_explicit_locking import WithoutLockingAccess
from db_util import create_pool, get_connection

if __name__ == "__main__":
  print(argv)
  if len(argv) != 2 or argv[1] not in ['cte', 'lock', 'wolock']:
    print("Should have 1 argument, whether `cte`, `lock` or `wolock`")
    exit(1)

  pool = create_pool()
  q = Queue()

  with get_connection(pool) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM coupons LIMIT 1")
    code = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users")
    ids = cursor.fetchall()
    for id in ids:
      q.put(id[0])
  
  print("Start Inserting")
  start = time()
  for _ in range(10):
    t = WritableCte(q, pool, code) if argv[1] == 'cte' \
      else LockingAccess(q, pool, code) if argv[1] == 'lock' \
        else WithoutLockingAccess(q, pool, code)
    t.setDaemon(True)
    t.start()

  q.join()
  print(f"It takes {time()-start} seconds")