"""Thin HTTP client for optional Event Hub shadow ingress."""
from __future__ import annotations
import json
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
