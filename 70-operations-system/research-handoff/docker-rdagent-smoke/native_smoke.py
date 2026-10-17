import json
import os
import socket
import sys
import argparse
from pathlib import Path

from rdagent.oai.backend.litellm import LITELLM_SETTINGS, LiteLLMAPIBackend

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("native", "invalid-key"), default="native")
mode = parser.parse_args().mode
if os.environ.get("P3_TEST_PROXY_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["P3_TEST_PROXY_KEY"]


def public_egress_blocked():
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2).close()
        return False
    except OSError:
        return True


backend = object.__new__(LiteLLMAPIBackend)
if mode == "invalid-key":
    os.environ["OPENAI_API_KEY"] = "sk-invalid-test-only"
    try:
        backend._create_chat_completion_inner_function(
            [{"role": "user", "content": "This invalid test key must be denied."}]
        )
    except Exception as exc:
        print(json.dumps({"classification": "EXPECTED_DENIAL_INVALID_KEY", "exception_type": type(exc).__name__}, sort_keys=True))
        sys.exit(0)
    print(json.dumps({"classification": "UNEXPECTED_SUCCESS_INVALID_KEY"}, sort_keys=True))
    sys.exit(3)

chat, finish = backend._create_chat_completion_inner_function(
    [{"role": "user", "content": "Return only the synthetic smoke marker."}]
)
embedding = backend._create_embedding_inner_function(["synthetic embedding smoke"])
env = os.environ
forbidden = (
    "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY", "LITELLM_MASTER_KEY", "POSTGRES_PASSWORD",
    "AQ_OWNER_SIGNING_PRIVATE_KEY", "OWNER_SIGNING_PRIVATE_KEY",
)
isolation = {
    "uid": os.getuid(),
    "public_egress_blocked": public_egress_blocked(),
    "forbidden_credentials_present": any(env.get(key) for key in forbidden),
    "docker_socket_present": Path("/var/run/docker.sock").exists(),
    "host_p3_env_visible": Path("/home/zhou/UPSTREAM_RUNTIME/rdagent-v1.0.0/.env").exists(),
    "host_drive_visible": Path("/mnt/d").exists(),
    "proxy_key_only": bool(env.get("P3_TEST_PROXY_KEY")) and env.get("OPENAI_API_KEY") == env.get("P3_TEST_PROXY_KEY"),
}
result = {
    "classification": "NATIVE_RDAGENT_PROXY_SMOKE",
    "rdagent_version": "1.0.0",
    "chat_model": LITELLM_SETTINGS.chat_model,
    "embedding_model": LITELLM_SETTINGS.embedding_model,
    "chat_api_base": env.get("OPENAI_API_BASE"),
    "embedding_api_base": env.get("OPENAI_API_BASE"),
    "chat_mock_marker": chat == "synthetic-ok",
    "embedding_dimension": len(embedding[0]) if embedding else 0,
    "finish_reason": finish,
    "isolation": isolation,
}
print(json.dumps(result, sort_keys=True))
passed = (
    result["chat_mock_marker"]
    and result["embedding_dimension"] == 3
    and isolation["uid"] == 10001
    and isolation["public_egress_blocked"]
    and not isolation["forbidden_credentials_present"]
    and not isolation["docker_socket_present"]
    and not isolation["host_p3_env_visible"]
    and not isolation["host_drive_visible"]
    and isolation["proxy_key_only"]
)
sys.exit(0 if passed else 2)
