"""Local gateway transport for a native learner and a Linux simulator."""
from dataclasses import asdict
import json
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gym_torcs.client import DriverAction, ServerState
from gym_torcs.server import scr_idx_from_port


def rpc(url, operation, port, **payload):
    request = Request(f"{url.rstrip('/')}/{operation}",
                      data=json.dumps(dict(port=port, **payload)).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=90) as response:
            return json.load(response)
    except HTTPError as error:
        details = json.loads(error.read())
        message = details.get("error", str(error))
        if details.get("type") == "TimeoutError":
            raise TimeoutError(message) from error
        raise RuntimeError(f"Simulator gateway: {message}") from error


class RemoteTorcsServer:
    """Own a simulator session through the localhost gateway."""
    def __init__(self, *, url, port, render_mode, race_config):
        self.url = url
        self.port = port
        scr_idx_from_port(port)
        self.render_mode = render_mode
        self.race_config = race_config
        self.started = False
        self.session_id = uuid.uuid4().hex

    def restart(self, race_config=None):
        if race_config is not None:
            self.race_config = race_config
        rpc(self.url, "start", self.port, race=asdict(self.race_config),
            render_mode=self.render_mode, session_id=self.session_id)
        self.started = True

    def close(self):
        if self.started:
            rpc(self.url, "stop", self.port, session_id=self.session_id)
            self.started = False


class RemoteTorcsClient:
    def __init__(self, *, url, port, session_id, client_id="SCR", connect_attempts=5, **kwargs):
        self.url = url
        self.port = port
        self.client_id = client_id
        self.connect_attempts = connect_attempts
        self.state = ServerState()
        self.action = DriverAction()
        self.connected = False
        self.session_id = session_id

    def request(self, operation, **payload):
        return rpc(self.url, operation, self.port, session_id=self.session_id, **payload)

    def connect(self):
        self.request("connect", client_id=self.client_id,
            connect_attempts=self.connect_attempts)
        self.connected = True

    def send(self):
        self.request("send", action=asdict(self.action))

    def receive(self, *, max_wait=None, keepalive=False):
        self.state.data = self.request("receive",
                              max_wait=max_wait, keepalive=keepalive)
        return self.state.data

    def restart_race(self):
        self.action.meta = 1
        self.send()
        self.action.meta = 0

    def close(self):
        if self.connected:
            self.request("disconnect")
            self.connected = False
