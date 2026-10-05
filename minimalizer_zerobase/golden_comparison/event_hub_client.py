"""Thin HTTP client for optional Event Hub shadow ingress."""
from __future__ import annotations
import json
import os
from typing import Any, Mapping
from urllib.request import Request, urlopen

class EventHubIngressError(RuntimeError):
    pass

def make_event_hub_sender(
    base_url: str,
    token: str,
    *,
    timeout: float = 3.0,
):
    url=base_url.rstrip("/")+"/ingress/events"
    if not base_url.startswith("https://"):
        raise ValueError("Event Hub shadow ingress requires HTTPS")
    if not token:
        raise ValueError("Event Hub shadow ingress requires token")

    def send(event: Mapping[str,Any]) -> dict[str,Any]:
        body=json.dumps(event,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        req=Request(url,data=body,method="POST",headers={
            "Authorization":"Bearer "+token,
            "Content-Type":"application/json",
        })
        try:
            with urlopen(req,timeout=timeout) as response:
                raw=response.read(65537)
                if len(raw)>65536:
                    raise EventHubIngressError("response_too_large")
                if not 200<=response.status<300:
                    raise EventHubIngressError("http_"+str(response.status))
        except EventHubIngressError:
            raise
        except Exception as exc:
            raise EventHubIngressError(type(exc).__name__) from exc
        try:
            result=json.loads(raw)
        except Exception as exc:
            raise EventHubIngressError("invalid_json") from exc
        if result.get("event_id")!=event.get("event_id"):
            raise EventHubIngressError("event_id_mismatch")
        if result.get("state") not in {"STORED","PENDING","DUPLICATE","BLOCKED"}:
            raise EventHubIngressError("invalid_state")
        return result
    return send

def make_event_hub_sender_from_environment(
    environ: Mapping[str, str] | None = None,
    *,
    timeout: float = 3.0,
):
    """Return an optional sender without exposing or validating secrets early.

    No Event Hub variables means shadow delivery is disabled. Partial or invalid
    configuration is represented by a sender that fails only when invoked, so
    deliver_shadow() can contain the failure after native evaluation succeeds.
    """
    env = os.environ if environ is None else environ
    base_url = env.get("RINKA_EVENT_HUB_URL", "")
    token = env.get("RINKA_EVENT_HUB_TOKEN", "")
    if not base_url and not token:
        return None

    def send(event: Mapping[str, Any]) -> dict[str, Any]:
        return make_event_hub_sender(base_url, token, timeout=timeout)(event)

    return send
