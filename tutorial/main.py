import time

import gymnasium as gym
import numpy as np
import gym_torcs  # Registers TorcsSCR-v0 with Gymnasium.


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
        # [steering, throttle]: steer straight and apply 30% throttle.
        # Both values range from -1 to 1. Negative throttle means braking.
        action = np.array([0.015, 0.7], dtype=np.float32)
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
