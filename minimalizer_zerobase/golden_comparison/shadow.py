"""Fail-open shadow delivery for Golden events.

Shadow delivery is observational only. It must never change Golden evaluation
authority or make a native Minimalizer run fail.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Mapping

@dataclass(frozen=True)
class ShadowDeliveryResult:
    attempted: bool
    delivered: bool
    event_id: str
    error: str | None = None

def deliver_shadow(
    event: Mapping[str, Any],
    send: Callable[[Mapping[str, Any]], Any] | None,
) -> ShadowDeliveryResult:
    event_id=str(event.get("event_id",""))
    if not event_id:
        raise ValueError("shadow event requires event_id")
    if send is None:
        return ShadowDeliveryResult(False,False,event_id,None)
    try:
        send(event)
    except Exception as exc:
        return ShadowDeliveryResult(True,False,event_id,type(exc).__name__)
    return ShadowDeliveryResult(True,True,event_id,None)
