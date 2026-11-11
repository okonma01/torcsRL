"""Record an isolated, single-track feasibility pilot with the existing reward."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import gymnasium as gym
import numpy as np
import torch

import gym_torcs
from torcsrl import NStepTD3


class PilotRecorder(gym.Wrapper):
    """Record completed attempts without changing observations or rewards."""

    def __init__(self, env, path, label):
        super().__init__(env)
        self.path = path
        self.label = label
        self.phase = "before_training"
        self.total_steps = 0
        self.episode_steps = 0
        self.episode_return = 0.0
        self.completed = []

    def reset(self, **kwargs):
        result = self.env.reset(**kwargs)
        self.episode_steps = 0
        self.episode_return = 0.0
        return result

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        if info.get("torcs_timeout"):
            raise RuntimeError("Simulator stopped responding; pilot cannot continue reliably")
        if not np.isfinite(obs).all() or not np.isfinite(reward):
            raise RuntimeError("Non-finite observation or reward during pilot")
        self.total_steps += 1
        self.episode_steps += 1
        self.episode_return += float(reward)
        if terminated or truncated:
            completed_lap = bool(info.get("successfulLap", False))
            row = {
                "environment": self.label,
                "phase": self.phase,
                "total_steps": self.total_steps,
                "episode_steps": self.episode_steps,
                "return": self.episode_return,
                "distance_m": float(info["distRaced"]),
                "completed_lap": completed_lap,
                "lap_time_s": float(info["lastLapTime"]) if completed_lap else None,
                "off_track": bool(info["offTrack"]),
                "damage_increased": bool(info["crashed"]),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
            }
            self.completed.append(row)
            with self.path.open("a") as output:
                output.write(json.dumps(row, allow_nan=False) + "\n")
        if self.label == "training" and self.total_steps % 1000 == 0:
            print(f"Driving steps collected: {self.total_steps}", flush=True)
        return obs, reward, terminated, truncated, info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=10_000)
    parser.add_argument("--warmup", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", choices=("cpu", "mps"), default="mps")
    parser.add_argument("--simulator-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.steps < 1 or args.warmup < 259:
        parser.error("steps must be positive and warmup must be at least 259")
    if args.device == "mps" and not torch.backends.mps.is_available():
        parser.error("MPS is unavailable")

    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = root / "checkpoints" / "pilots" / stamp
    run_dir.mkdir(parents=True)
    settings = dict(vars(args), track="alpine-1", category="road",
                    reward="existing centerline-weighted speed", observation_noise=True,
                    batch_size=256, buffer_size=100_000, telemetry_mode="standard",
                    torch_version=torch.__version__, numpy_version=np.__version__,
                    gymnasium_version=gym.__version__, evaluation_seed=args.seed + 1,
                    evaluation_attempts_per_stage=1)
    (run_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    print(f"Pilot folder: {run_dir}", flush=True)

    def environment(port, label):
        env = gym.make("TorcsSCR-v0", port=port, track_name="alpine-1",
                       track_category="road", telemetry_mode="standard",
                       simulator_url=args.simulator_url, client_connect_attempts=5)
        return PilotRecorder(env, run_dir / "attempts.jsonl", label)

    train = environment(3001, "training")
    val = environment(3002, "evaluation")
    original_dir = Path.cwd()
    try:
        # The existing algorithm saves relative to cwd; isolate all pilot outputs.
        os.chdir(run_dir)
        agent = NStepTD3(train, val, ac_kwargs={}, device=args.device, seed=args.seed,
                         buffer_size=100_000, buffer_start_size=args.warmup, batch_size=256)
        print("Checking driving before training", flush=True)
        agent.evaluate()
        print(json.dumps(val.completed[-1]), flush=True)
        train.phase = "training_including_warmup"
        val.phase = "during_training"
        started = time.monotonic()
        agent.train(args.steps)
        training_seconds = time.monotonic() - started
        agent.save()
        val.phase = "after_training"
        print("Checking driving after training", flush=True)
        agent.evaluate()
        agent.save()
        print(json.dumps(val.completed[-1]), flush=True)
        summary = {
            "status": "completed",
            "training_seconds_including_warmup_resets_and_periodic_evaluation": training_seconds,
            "training_interactions": train.total_steps,
            "learning_updates": agent.grad_step_counter - 1,
            "training_interactions_per_wall_second": train.total_steps / training_seconds,
            "completed_training_attempts": len(train.completed),
            "completed_training_laps": sum(row["completed_lap"] for row in train.completed),
            "before_training": val.completed[0],
            "after_training": val.completed[-1],
            "limits": "One seed, one track, one evaluation attempt per stage; feasibility only. "
                      "Unfinished training attempts are not in attempts.jsonl. "
                      "Warmup and learning steps are counted together in training_interactions.",
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
    finally:
        os.chdir(original_dir)
        train.close()
        val.close()


if __name__ == "__main__":
    main()
