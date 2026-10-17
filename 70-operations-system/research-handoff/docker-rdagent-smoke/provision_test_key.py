"""Generate one short-lived model-scoped virtual key inside the test Proxy."""

import json
import os
import urllib.request

request = urllib.request.Request(
    "http://127.0.0.1:4000/key/generate",
    data=json.dumps({"models": ["deepseek-chat", "qwen3-embedding:0.6b"]}).encode(),
    headers={
        "Authorization": f"Bearer {os.environ['LITELLM_MASTER_KEY']}",
        "Content-Type": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(request, timeout=15) as response:
    result = json.load(response)
token = result.get("key") or result.get("token")
if not isinstance(token, str) or not token:
    raise RuntimeError("Proxy did not return a virtual key")
print(json.dumps({"classification": "TEST_PROXY_KEY_CREATED", "token": token}, separators=(",", ":")))
