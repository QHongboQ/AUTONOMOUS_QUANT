from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time

counts = {"chat": 0, "embedding": 0}
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, value):
        payload = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        if self.path == "/counts":
            with lock:
                return self._send(200, dict(counts))
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.loads(raw or b"{}")
        if self.path.endswith("/chat/completions"):
            with lock:
                counts["chat"] += 1
            return self._send(200, {
                "id": "chatcmpl-synthetic", "object": "chat.completion",
                "created": int(time.time()), "model": body.get("model", "mock-chat"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "synthetic-ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            })
        if self.path.endswith("/embeddings"):
            with lock:
                counts["embedding"] += 1
            return self._send(200, {
                "object": "list", "model": body.get("model", "mock-embedding"),
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3]}],
                "usage": {"prompt_tokens": 4, "total_tokens": 4},
            })
        return self._send(404, {"error": "not found", "path": self.path})

    def log_message(self, *_):
        pass


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
