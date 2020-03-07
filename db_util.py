from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool

import config

def create_pool():
  return SimpleConnectionPool(
    minconn=config.db_pool_minconn,\
    maxconn=config.db_pool_maxconn,\
    user=config.db_username,\
    password=config.db_password,\
    host=config.db_ip,\
    port=config.db_port,\
    database=config.db_name)

@contextmanager
def get_connection(db):
  conn = db.getconn()
  try:
    yield conn
  finally:
    db.putconn(conn)