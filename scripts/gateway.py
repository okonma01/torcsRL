"""Container-local SCR bridge. Publish its HTTP port only on host loopback."""
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import signal
import subprocess
import sys
import threading

from gym_torcs.client import DriverAction, TorcsClient
from gym_torcs.server import RaceConfig, TorcsServer, scr_idx_from_port
from scripts.native import CAMERAS, NativeRace, catalog


@dataclass
class Session:
    server: TorcsServer
    owner: str
    client: TorcsClient | None = None


sessions = {}
lock = threading.RLock()
demo_lock = threading.Lock()
demo_process = None
demo_log = Path("/tmp/torcsrl-demo.log")
native_race = None


def native_control(operation, body):
    global native_race
    with lock:
        if operation == "native-stop":
            if native_race is not None:
                native_race.close()
                native_race = None
            return {"status": "stopped"}
        installed = catalog()
        bots = {bot["id"]: bot for bot in installed["bots"]}
        tracks = {track["id"]: track for track in installed["tracks"]}
        bot = bots[body["bot"]]
        track = tracks[body["track"]]
        laps = body.get("laps", 5)
        camera = body.get("camera", "follow")
        if type(laps) is not int or not 1 <= laps <= 100:
            raise ValueError("Choose between 1 and 100 laps")
        if camera not in CAMERAS:
            raise ValueError("Unknown camera")
        if demo_process is not None and demo_process.poll() is None:
            raise RuntimeError("Stop the demo before starting a bot")
        if any(s.server.render_mode == "human" and s.server.running for s in sessions.values()):
            raise RuntimeError("Stop the current Python race before starting a bot")
        if native_race is not None:
            native_race.close()
        native_race = NativeRace(bot=bot, track=track, laps=laps, camera=camera)
        try:
            native_race.start()
            if not native_race.running:
                raise RuntimeError("TORCS could not start; check the desktop logs")
        except (OSError, RuntimeError, ValueError):
            native_race.close()
            native_race = None
            raise
        return {"status": "running"}


def demo_control(operation):
    global demo_process
    with lock, demo_lock:
        if operation == "demo-start":
            if native_race is not None and native_race.running:
                raise RuntimeError("Stop the bot race before starting the demo")
            if demo_process is not None and demo_process.poll() is None:
                return {"status": "running"}
            with demo_log.open("w") as output:
                demo_process = subprocess.Popen(
                    [sys.executable, "-u", "-m", "scripts.watch", "--seconds", "0"],
                    stdout=output, stderr=subprocess.STDOUT,
                )
            return {"status": "starting"}
        if demo_process is not None and demo_process.poll() is None:
            demo_process.send_signal(signal.SIGTERM)
            demo_process.wait(timeout=90)
        demo_process = None
        return {"status": "stopped"}


def status():
    with lock:
        races = [{"port": port, "track": s.server.race_config.track_name,
                  "visible": s.server.render_mode == "human", "running": s.server.running}
                 for port, s in sessions.items()]
    running_demo = demo_process is not None and demo_process.poll() is None
    error = None
    native = None
    with lock:
        if native_race is not None:
            native = dict(bot=native_race.bot["name"], car=native_race.bot["car"],
                          track=native_race.race_config.track_name, running=native_race.running)
            if not native_race.running:
                error = "The bot race closed. You can start another race."
    if demo_process is not None and demo_process.poll() not in (None, 0):
        lines = demo_log.read_text().strip().splitlines()
        error = lines[-1] if lines else "The driving demo stopped unexpectedly."
    return {"races": races, "demo_running": running_demo, "native": native, "error": error}


def stop(port):
    session = sessions.pop(port, None)
    if session is not None:
        if session.client is not None:
            session.client.close()
        session.server.close()


def dispatch(operation, body):
    port = int(body["port"])
    scr_idx_from_port(port)
    with lock:
        owner = body["session_id"]
        if not isinstance(owner, str) or not owner:
            raise ValueError("A session_id is required")
        if port in sessions and sessions[port].owner != owner:
            raise RuntimeError(f"Port {port} belongs to another run; stop that run first")
        if operation == "stop":
            stop(port)
            return {}
        if operation == "start":
            mode = body.get("render_mode")
            if mode not in (None, "human"):
                raise ValueError("render_mode must be null or human")
            if mode == "human" and any(
                    s.server.render_mode == "human" for p, s in sessions.items() if p != port):
                raise ValueError("Only one graphical race can use the desktop at a time")
            if mode == "human" and native_race is not None and native_race.running:
                raise RuntimeError("Stop the bot race in the viewer before starting a Python race")
            race = RaceConfig(**body["race"])
            race.scr_idx = scr_idx_from_port(port)
            stop(port)
            server = TorcsServer(port=port, render_mode=mode, race_config=race,
                                 debug=True, gui_start_delay=3.0)
            sessions[port] = Session(server, owner)
            try:
                server.start()
                if not server.running:
                    raise RuntimeError("TORCS exited during startup; check container logs")
            except Exception:
                stop(port)
                raise
            return {}
        session = sessions[port]
        if operation == "connect":
            if session.client is not None:
                session.client.close()
            attempts = min(max(int(body.get("connect_attempts", 5)), 1), 20)
            session.client = TorcsClient(port=port, client_id=body.get("client_id", "SCR"),
                                         connect_attempts=attempts)
            session.client.connect()
            return {}
        if operation == "disconnect":
            if session.client is not None:
                session.client.close()
            session.client = None
            return {}
        client = session.client
        if client is None:
            raise RuntimeError("Connect the SCR client first")
        if operation == "send":
            client.action = DriverAction(**body["action"])
            client.send()
            return {}
        if operation == "receive":
            wait = min(max(float(body.get("max_wait") or 15), 0.1), 60)
            return client.receive(max_wait=wait, keepalive=bool(body.get("keepalive")))
        raise ValueError(f"Unknown operation: {operation}")


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self.file(Path(__file__).with_name("viewer.html"))
        elif path.startswith("/novnc/"):
            root = Path("/usr/share/novnc").resolve()
            asset = (root / path.removeprefix("/novnc/")).resolve()
            if asset.is_relative_to(root) and asset.is_file():
                self.file(asset)
            else:
                self.reply(404, {"error": "Unknown asset"})
        elif path == "/status":
            self.reply(200, status())
        elif path == "/catalog":
            self.reply(200, catalog())
        elif path == "/health":
            self.reply(200, {"status": "ok"})
        else:
            self.reply(404, {"error": "Unknown endpoint"})

    def file(self, path):
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.headers.get("Content-Type") != "application/json":
            self.reply(415, {"error": "application/json required"})
            return
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 16384:
                raise ValueError("Invalid request size")
            body = json.loads(self.rfile.read(size))
            operation = self.path.strip("/")
            if operation in ("native-start", "native-stop"):
                result = native_control(operation, body)
            elif operation in ("demo-start", "demo-stop"):
                result = demo_control(operation)
            else:
                result = dispatch(operation, body)
        except (ValueError, KeyError, TypeError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            self.reply(400, {"error": str(error), "type": type(error).__name__})
            return
        self.reply(200, result)

    def log_message(self, format, *args):
        # Log failures; per-step successful RPCs would flood the simulator log.
        if len(args) > 1 and str(args[1]) != "200":
            super().log_message(format, *args)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    try:
        print("SCR gateway ready on port 8000", flush=True)
        server.serve_forever()
    finally:
        server.server_close()
        for port in list(sessions):
            stop(port)
        native_control("native-stop", {})


if __name__ == "__main__":
    main()
