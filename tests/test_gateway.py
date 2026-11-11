from unittest.mock import Mock
import signal

import pytest
from scripts import gateway

from scripts.gateway import Session, dispatch, sessions, status


def test_other_run_cannot_restart_or_stop_a_session():
    server = Mock()
    sessions[3001] = Session(server, "first-run")
    try:
        for operation in ("start", "stop", "send", "disconnect"):
            with pytest.raises(RuntimeError, match="belongs to another run"):
                dispatch(operation, {"port": 3001, "session_id": "other-run"})
        server.close.assert_not_called()
        assert sessions[3001].owner == "first-run"
    finally:
        sessions.clear()


def test_disconnect_is_idempotent_and_owned_stop_releases_session():
    server = Mock()
    client = Mock()
    sessions[3001] = Session(server, "run", client)
    try:
        request = {"port": 3001, "session_id": "run"}
        dispatch("disconnect", request)
        dispatch("disconnect", request)
        client.close.assert_called_once()
        dispatch("stop", request)
        dispatch("stop", request)
        server.close.assert_called_once()
        assert 3001 not in sessions
    finally:
        sessions.clear()


def test_status_distinguishes_idle_and_visible_races():
    assert status()["races"] == []
    server = Mock()
    server.race_config.track_name = "alpine-1"
    server.render_mode = "human"
    server.running = True
    sessions[3001] = Session(server, "run")
    try:
        assert status()["races"] == [dict(port=3001, track="alpine-1", visible=True, running=True)]
    finally:
        sessions.clear()


def test_stop_demo_signals_child_and_releases_handle(monkeypatch):
    child = Mock()
    child.poll.return_value = None
    monkeypatch.setattr(gateway, "demo_process", child)
    assert gateway.demo_control("demo-stop") == {"status": "stopped"}
    child.send_signal.assert_called_once_with(signal.SIGTERM)
    child.wait.assert_called_once_with(timeout=90)
    assert gateway.demo_process is None
