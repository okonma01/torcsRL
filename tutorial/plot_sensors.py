"""Capture one sensor observation, close TORCS, then display the scan."""

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
import gym_torcs  # Registers TorcsSCR-v0 with Gymnasium.

from gym_torcs.constants import MAX_TRACK, TRACK_SENSOR_ANGLES


def plot_scan(obs):
    angles = np.deg2rad(TRACK_SENSOR_ANGLES)
    # Undo the environment's scaling: normalized = 2 * distance / MAX_TRACK - 1.
    distances = (obs[9:28] + 1.0) * MAX_TRACK / 2.0

    fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("N")
    ax.set_thetamin(-50)
    ax.set_thetamax(50)
    ax.set_ylim(0, MAX_TRACK)

    for angle, distance in zip(angles, distances):
        ax.plot([angle, angle], [0, distance], color="tab:blue", alpha=0.6)

    at_limit = np.isclose(distances, MAX_TRACK, atol=0.01)
    ax.scatter(angles[~at_limit], distances[~at_limit], label="Road edge")
    ax.scatter(
        angles[at_limit], distances[at_limit], marker="x", color="tab:orange",
        label="Range limit; edge not located",
    )
    ax.set_title("Track sensors: car at origin, straight ahead at 0 degrees", pad=25)
    ax.set_ylabel("Distance (meters)", labelpad=35)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 0.05))
    fig.tight_layout()
    return fig


def main():
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
        obs, _ = env.reset()
    finally:
        env.close()

    # Plot after closing the simulator so the plot cannot delay control messages.
    plot_scan(obs)
    plt.show()


if __name__ == "__main__":
    main()
