"""Collect a persistent Tita dataset without starting RL training."""
import argparse
from pathlib import Path
import time

import gymnasium as gym
import gym_torcs
from gym_torcs.wrappers import ActionRepeatWrapper

from torcsrl.buffers.expert_replay_buffer import ExpertReplayBuffer
from torcsrl.expert import collect_expert_transitions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100_000)
    parser.add_argument("--action-repeat", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--track", default="alpine-1")
    parser.add_argument("--category", default="road")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--simulator-url")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    if args.action_repeat < 1:
        parser.error("--action-repeat must be positive")
    if args.output.exists():
        parser.error("--output already exists; choose a new file")
    env = gym.make(
        "TorcsSCR-v0", track_name=args.track, track_category=args.category,
        simulator_url=args.simulator_url, telemetry_mode="enhanced",
        observation_noise=False, client_connect_attempts=5,
        render_mode="human" if args.render else None,
    )
    env = ActionRepeatWrapper(env, args.action_repeat)
    dataset = ExpertReplayBuffer(
        env.observation_space.shape[0], env.action_space.shape[0], args.steps, 256,
    )
    try:
        start = time.perf_counter()
        collect_expert_transitions(env, dataset, args.steps, args.seed)
        print(f"Collection took {time.perf_counter() - start:.2f} seconds")
    finally:
        try:
            if len(dataset):
                dataset.save(args.output)
                print(f"Saved {len(dataset)}/{args.steps} transitions to {args.output}", flush=True)
        finally:
            env.close()


if __name__ == "__main__":
    main()
