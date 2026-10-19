"""Trusted control-side LiteLLM native user/key operations for one run."""

from __future__ import annotations

import json
import os
import sys

from native_experiment_budget import (
    LiteLLMNativeAPI,
    NativeExperimentBudgetController,
    P12ExperimentIdentity,
)


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("control request must be an object")
        admin_key = os.environ.get("LITELLM_DEEPSEEK_STAGING_MASTER_KEY", "")
        api = LiteLLMNativeAPI("http://127.0.0.1:4000", admin_key)
        if request.get("operation") == "prepare":
            identity = P12ExperimentIdentity(
                research_budget_identity=request["research_budget_identity"],
                request_id=request["request_id"],
                standing_policy_id=request["standing_policy_id"],
            )
            token, user, key = NativeExperimentBudgetController(api).prepare_owner_oneshot(
                identity,
                owner_activation_confirmed=request.get("owner_activation_confirmed") is True,
            )
            print(json.dumps({
                "classification": "OWNER_ONESHOT_NATIVE_KEY_READY",
                "token": token,
                "user_id": identity.user_id,
                "user_alias": user["user_alias"],
                "user_budget_usd": float(user["max_budget"]),
                "user_spend_usd": float(user.get("spend", 0)),
                "models": key["models"],
                "key_alias": key["key_alias"],
                "key_budget_usd": float(key["max_budget"]),
                "budget_duration": key.get("budget_duration"),
                "expires": key["expires"],
                "max_parallel_requests": key["max_parallel_requests"],
            }, sort_keys=True))
            return 0
        if request.get("operation") == "block":
            token = request.get("token")
            if not isinstance(token, str) or not token.startswith("sk-"):
                raise ValueError("scoped key required")
            status, payload = api.request("POST", "/key/block", {"key": token})
            if status not in (200, 201) or payload.get("blocked") is not True:
                raise RuntimeError("native key block was not confirmed")
            info = api.key_info(token)
            if info.get("blocked") is not True:
                raise RuntimeError("native key blocked state did not persist")
            print(json.dumps({
                "classification": "OWNER_ONESHOT_KEY_BLOCKED",
                "blocked": True,
                "spend": float(info.get("spend", 0)),
                "models": info.get("models"),
            }, sort_keys=True))
            return 0
        raise ValueError("unsupported control operation")
    except Exception as exc:
        print(json.dumps({
            "classification": "DENIED_OWNER_ONESHOT_PROXY_CONTROL",
            "error_type": type(exc).__name__,
        }, sort_keys=True), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
