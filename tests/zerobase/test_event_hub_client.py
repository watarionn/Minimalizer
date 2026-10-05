import json
from unittest.mock import patch
from minimalizer_zerobase.golden_comparison.event_hub_client import (
    EventHubIngressError,make_event_hub_sender,
)

class Response:
    def __init__(self,status=200,body=None):
        self.status=status
        self.body=body or {}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n): return json.dumps(self.body).encode()

def event():
    return {"event_id":"evt_test"}

def test_sender_posts_to_ingress_and_accepts_stored():
    response=Response(body={"event_id":"evt_test","state":"STORED"})
    with patch("minimalizer_zerobase.golden_comparison.event_hub_client.urlopen",return_value=response) as call:
        result=make_event_hub_sender("https://hub.example","token")(event())
    assert result["state"]=="STORED"
    assert call.call_args.args[0].full_url=="https://hub.example/ingress/events"

def test_sender_accepts_duplicate_for_retry():
    response=Response(body={"event_id":"evt_test","state":"DUPLICATE"})
    with patch("minimalizer_zerobase.golden_comparison.event_hub_client.urlopen",return_value=response):
        assert make_event_hub_sender("https://hub.example","token")(event())["state"]=="DUPLICATE"

def test_sender_requires_https_and_token():
    for url,token in [("http://hub.example","token"),("https://hub.example","")]:
        try:
            make_event_hub_sender(url,token)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

def test_sender_rejects_mismatched_event_id():
    response=Response(body={"event_id":"other","state":"STORED"})
    with patch("minimalizer_zerobase.golden_comparison.event_hub_client.urlopen",return_value=response):
        try:
            make_event_hub_sender("https://hub.example","token")(event())
        except EventHubIngressError as exc:
            assert str(exc)=="event_id_mismatch"
        else:
            raise AssertionError("expected EventHubIngressError")
