import json
from typing import cast

import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
response = r.ping()
print("Connected:", response)


def fetch_data(key: str) -> dict:

    cached_data = r.get(key)
    if cached_data is not None:
        try:
            return cast(dict, json.loads(cached_data))
        except json.JSONDecodeError:
            r.delete(key)  # Evict corrupt entry and fall through to re-fetch

    data = {"id": key, "value": "example"}
    r.set(key, json.dumps(data), ex=3600)
    return data


result = fetch_data("123")
print(result)
