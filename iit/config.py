# config.py
import redis.asyncio as redis


def get_redis_client():
    return redis.Redis(host="localhost", port=6379, db=0)


STREAM_NAME = "mystream"
GROUP_NAME = "mygroup"
CONSUMER_NAME = "consumer1"
STATE_STREAM_NAME = "statestream"
STATE_GROUP_NAME = "stategroup"
