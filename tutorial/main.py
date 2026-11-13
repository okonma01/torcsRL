import time

import gymnasium as gym
import numpy as np
import gym_torcs  # Registers TorcsSCR-v0 with Gymnasium.
import csv
from datetime import datetime, timezone
from pathlib import Path

env = gym.make(
    "TorcsSCR-v0",
    simulator_url="http://127.0.0.1:8000",
    render_mode="human",
    track_name="michigan",
    track_category="oval",
    telemetry_mode="standard",
    observation_noise=False,
)

try:
    obs, info = env.reset()
    print("Observation shape:", obs.shape)
    print("Action space:", env.action_space)

    total_reward = 0.0

    for step in range(10000):
        # [steering, accelerator, brake]: nearly straight, 70% gas, no brake.
        # Steering ranges from -1 to 1; each pedal ranges from 0 to 1.
        action = np.array([0.0001, 0.7, 0.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)

        if (step + 1) % 100 == 0:
            heading_degrees = float(obs[7]) * 180
            track_position = float(obs[8])

            print(
                f"Step {step + 1}: "
                f"speed={info['speedX']:.2f} km/h, "
                f"heading={heading_degrees:.2f} degrees, "
                f"position={track_position:.3f}, "
                f"reward={reward:.3f}"
            )

        if terminated or truncated:
            print("Episode ended:", "terminated" if terminated else "truncated")
            print("Episode info:", info)
            break

        # Slow down the Python loop so we can watch the car.
        # time.sleep(0.02)
        # time.sleep(2)

    print(f"Total reward: {total_reward:.3f}")
finally:
    env.close()
result = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "track": env.unwrapped.race_config.track_name,
    "steps": step + 1,
    "total_reward": total_reward,
    "terminated": bool(terminated),
    "truncated": bool(truncated),
    "script_limit_reached": not (terminated or truncated),
    "successful_lap": info["successfulLap"],
    "lap_time_s": info["lastLapTime"] if info["successfulLap"] else None,
    "sim_time_s": info["timeAlive"],
    "distance_m": info["distRaced"],
    "damage": info["damage"],
    "crashed": info["crashed"],
    "off_track": info["offTrack"],
    "telemetry_timeout": info.get("torcs_timeout", False),
    "steering": float(action[0]),
    "accelerator": float(action[1]),
    "brake": float(action[2]),
}
# Keep the earlier two-action CSV separate because its columns differ.
results_path = Path(__file__).with_name("runs_three_actions.csv")
write_header = (
    not results_path.exists()
    or results_path.stat().st_size == 0
)

with results_path.open("a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=result.keys())

    if write_header:
        writer.writeheader()

    writer.writerow(result)

print(f"Run saved to {results_path}")
