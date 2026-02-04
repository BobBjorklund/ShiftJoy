import os
import json
import redis

REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

r = redis.from_url(REDIS_URL, decode_responses=True)

PREFIX = "shiftjoy"

def _key(game_id):
    return f"{PREFIX}:game:{game_id}"

def get_game(game_id):
    data = r.get(_key(game_id))
    return json.loads(data) if data else None

def save_game(game_id, game_data, ttl=60*60*12):
    r.set(_key(game_id), json.dumps(game_data), ex=ttl)

def touch_game(game_id, ttl=60*60*12):
    r.expire(_key(game_id), ttl)

def with_lock(game_id, fn):
    lock = r.lock(f"{PREFIX}:lock:{game_id}", timeout=5, blocking_timeout=5)
    lock.acquire()
    try:
        return fn()
    finally:
        lock.release()