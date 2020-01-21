DB_URI = "postgres://postgres:postgres@db_postgres:5432/aiopg"
REDIS_URI = "redis://redis"
RABBIT_HOST = "rabbitmq"

try:
    from local_settings import *
except ImportError:
    pass