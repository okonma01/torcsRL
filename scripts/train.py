"""Train a small, configurable N-step TD3 run with the current environment API."""
import argparse

import gymnasium as gym
import gym_torcs
import torch
from torcsrl import NStepTD3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=10_000)
    parser.add_argument("--warmup", type=int, default=1_000)
    parser.add_argument("--buffer-size", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--track", default="alpine-1")
    parser.add_argument("--category", default="road")
    parser.add_argument("--device", choices=("cpu", "cuda", "mps"), default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--telemetry-mode", choices=("standard", "enhanced"), default="standard")
    parser.add_argument("--simulator-url", help="Local simulator gateway, e.g. http://127.0.0.1:8000")
    parser.add_argument("--render", action="store_true", help="Show the training race on the container desktop")
    args = parser.parse_args()
    if args.steps < 1 or args.batch_size < 1:
        parser.error("--steps and --batch-size must be positive")
    if args.warmup < args.batch_size + 3 or args.buffer_size < args.batch_size:
        parser.error("warmup must be >= batch-size + 3; buffer-size must be >= batch-size")
    if args.device == "mps" and not torch.backends.mps.is_available():
        parser.error("MPS unavailable; run native macOS Python outside the container")
    print(f"Training on {args.device}; simulator: {args.simulator_url or 'local'}", flush=True)

    train = gym.make("TorcsSCR-v0", track_name=args.track, track_category=args.category,
                     client_connect_attempts=5, telemetry_mode=args.telemetry_mode,
                     simulator_url=args.simulator_url,
                     render_mode="human" if args.render else None)
    val = gym.make("TorcsSCR-v0", port=3002, track_name=args.track,
                   track_category=args.category, client_connect_attempts=5,
                   telemetry_mode=args.telemetry_mode, simulator_url=args.simulator_url)
    try:
        agent = NStepTD3(train, val, ac_kwargs={}, device=args.device, seed=args.seed,
                         buffer_size=args.buffer_size, buffer_start_size=args.warmup,
                         batch_size=args.batch_size)
        agent.train(args.steps)
        agent.save()
        print(f"Saved {args.steps}-step run under checkpoints/nsteptd3/", flush=True)
    finally:
        train.close()
        val.close()


if __name__ == "__main__":
    main()
