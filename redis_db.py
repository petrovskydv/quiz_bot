import logging
import os

import redis
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

redis_host = os.environ['REDIS_HOST']
redis_port = os.environ['REDIS_PORT']
redis_password = os.environ['REDIS_PASSWORD']
logger.info('соединяемся с редис')
db_connection = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_password, decode_responses=True)
