"""Watch a simple centerline controller; this is a demo, not a trained policy."""
import argparse
import signal
import time

# Shell background jobs can inherit SIGINT ignored. Explicit handlers also let
# the viewer stop its child cleanly with SIGTERM and release the race session.
signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal.default_int_handler)

import gymnasium as gym
import numpy as np
import gym_torcs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator-url", default="http://127.0.0.1:8000")
    parser.add_argument("--track", default="alpine-1")
    parser.add_argument("--seconds", type=float, default=0, help="Duration; 0 runs until stopped")
    args = parser.parse_args()
    if args.seconds < 0:
        parser.error("--seconds must be nonnegative")
    env = gym.make("TorcsSCR-v0", simulator_url=args.simulator_url,
                   render_mode="human", track_name=args.track, track_category="road",
                   telemetry_mode="standard", observation_noise=False,
                   client_connect_attempts=5)
    try:
        print("Centerline driving demo. View http://127.0.0.1:8000/", flush=True)
        obs, _ = env.reset()
        end = time.monotonic() + args.seconds if args.seconds else float("inf")
        while time.monotonic() < end:
            started = time.monotonic()
            angle = float(obs[7]) * np.pi
            track_pos = float(obs[8])
            speed = float(obs[0]) * 250.0
            steer = np.clip(angle / 0.7854 - 0.5 * track_pos, -1.0, 1.0)
            throttle = np.clip((65.0 - speed) / 50.0, -0.3, 0.5)
            action = np.array([steer, max(throttle, 0.0), max(-throttle, 0.0)], dtype=np.float32)
            obs, _, terminated, truncated, info = env.step(action)
            if info.get("torcs_timeout"):
                raise RuntimeError("Simulator stopped responding")
            if terminated or truncated:
                obs, _ = env.reset()
            time.sleep(max(0, 0.02 - (time.monotonic() - started)))
    finally:
        env.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Driving demo stopped", flush=True)
