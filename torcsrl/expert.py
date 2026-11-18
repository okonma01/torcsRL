"""Collect teacher experience without creating or training an agent."""
import numpy as np

from torcsrl.buffers.expert_replay_buffer import ExpertReplayBuffer


def collect_expert_transitions(env, dataset: ExpertReplayBuffer, steps: int, seed=0):
    """Append exactly steps transitions, retaining final observations before reset."""
    if steps < 1 or steps > dataset.capacity - len(dataset):
        raise ValueError("steps must be positive and fit in the expert buffer")
    obs, info = env.reset(seed=seed)
    repeat = info.get("action_repeat", 1)
    if len(dataset) and dataset.action_repeat != repeat:
        raise ValueError("Environment and expert buffer action_repeat must match")
    dataset.action_repeat = repeat
    for step in range(steps):
        expert_action = info.get("action_tita")
        if expert_action is None:
            raise RuntimeError(
                "Expert collection requires a valid Tita teacher action. "
                "Use a simulator with teacher telemetry enabled."
            )
        action = np.asarray(expert_action, dtype=np.float32)
        if not env.action_space.contains(action):
            raise ValueError("Teacher action must be finite and inside the environment action space")
        # Copy before stepping: environments may reuse observation arrays.
        obs = obs.copy()
        obs_next, reward, terminated, truncated, info = env.step(action)
        if info.get("torcs_timeout"):
            raise RuntimeError("Simulator timeout: no valid next observation; transition was not saved")
        dataset.push(obs, action, reward, obs_next, terminated, truncated,
                     steps_executed=info.get("steps_executed", 1))
        obs = obs_next
        if terminated or truncated:
            obs, info = env.reset()
        if (step + 1) % 1000 == 0:
            print(f"Collected {step + 1}/{steps} expert transitions", flush=True)
    return obs, info
