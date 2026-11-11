"""Check imports, a real SCR race, and a TD3 update without a long training run."""
import argparse

import gymnasium as gym
import numpy as np
import torch

import gym_torcs  # registers TorcsSCR-v0
from torcsrl import NStepTD3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"), default="cpu")
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--simulator-url")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")

    print(f"PyTorch {torch.__version__}; MPS available: {torch.backends.mps.is_available()}", flush=True)
    # Spaces are sufficient for testing model construction and gradient updates.
    train = gym.make("TorcsSCR-v0", debug=True, client_connect_attempts=5,
                     telemetry_mode="standard", simulator_url=args.simulator_url,
                     render_mode="human" if args.render else None)
    val = gym.make("TorcsSCR-v0", port=3002, telemetry_mode="standard",
                   simulator_url=args.simulator_url)
    try:
        agent = NStepTD3(train, val, ac_kwargs={}, device=args.device, buffer_size=32,
                         batch_size=4, buffer_start_size=4, verbose=False)
        obs = np.zeros(train.observation_space.shape, dtype=np.float32)
        action = agent.act_numpy(obs, deterministic=False)
        for _ in range(8):
            agent.replay_buffer.push(obs, action, 0.0, obs, False, 1)
        agent.n_gradient_steps()
        print(f"TD3 action and gradient update passed on {args.device}", flush=True)
        if args.python_only:
            return

        obs, _ = train.reset(seed=0)
        for _ in range(args.steps):
            obs, reward, terminated, truncated, info = train.step(
                np.array([0.0, 0.3], dtype=np.float32))
            if info.get("torcs_timeout"):
                raise RuntimeError("SCR timed out during smoke test")
            if not np.isfinite(obs).all() or not np.isfinite(reward):
                raise RuntimeError("Non-finite simulator observation or reward")
            if terminated or truncated:
                obs, _ = train.reset()
        print(f"SCR reset and {args.steps} steps passed", flush=True)
    finally:
        train.close()
        val.close()


if __name__ == "__main__":
    main()
