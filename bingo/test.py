from upstash_redis import Redis

redis = Redis.from_env()

redis.set("foo", "bar")
value = redis.get("foo")