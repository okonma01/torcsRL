"""Append-only expert transitions, stored independently of online replay."""
from pathlib import Path
from numbers import Integral

import numpy as np

from torcsrl.buffers.replay_buffer import ReplayBuffer


class ExpertReplayBuffer(ReplayBuffer):
    """Uses the usual five-field training samples, retaining both episode flags."""

    def __init__(self, obs_dim, action_dim, capacity, batch_size, device="cpu", *, action_repeat=1):
        if capacity < 1 or batch_size < 1:
            raise ValueError("capacity and batch_size must be positive")
        if isinstance(action_repeat, bool) or not isinstance(action_repeat, Integral) or action_repeat < 1:
            raise ValueError("action_repeat must be a positive integer")
        super().__init__(obs_dim, action_dim, capacity, batch_size, device)
        self.action_repeat = int(action_repeat)
        self.truncated = np.empty(capacity, dtype=np.bool_)
        self.steps_executed = np.empty(capacity, dtype=np.int32)

    def push(self, obs, action, reward, obs_next, dones, truncated=False, *, steps_executed=1):
        if self.size == self.capacity:
            raise OverflowError("Expert buffer is full; demonstrations cannot be overwritten")
        for value, shape in ((obs, (self.obs_dim,)), (obs_next, (self.obs_dim,)),
                             (action, (self.action_dim,))):
            if np.shape(value) != shape or not np.isfinite(value).all():
                raise ValueError(f"Expected finite transition array with shape {shape}")
        if not np.isfinite(reward):
            raise ValueError("Reward must be finite")
        if (isinstance(steps_executed, bool) or not isinstance(steps_executed, Integral)
                or not 1 <= steps_executed <= self.action_repeat):
            raise ValueError("steps_executed must be an integer between 1 and action_repeat")
        self.truncated[self.size] = bool(truncated)
        self.steps_executed[self.size] = steps_executed
        super().push(obs, action, reward, obs_next, dones)

    def save(self, path):
        """Write a new archive; never replace an existing demonstration file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as archive:
            np.savez_compressed(
                archive, obs=self.obs[:self.size], actions=self.actions[:self.size],
                rewards=self.rewards[:self.size], obs_next=self.obs_next[:self.size],
                terminated=self.dones[:self.size].astype(np.bool_),
                truncated=self.truncated[:self.size],
                action_repeat=self.action_repeat, reward_convention="sum_per_decision",
                steps_executed=self.steps_executed[:self.size],
            )

    @classmethod
    def load(cls, path, batch_size, device="cpu"):
        with np.load(path, allow_pickle=False) as data:
            arrays = {key: data[key] for key in
                      ("obs", "actions", "rewards", "obs_next", "terminated", "truncated")}
            obs, actions = arrays["obs"], arrays["actions"]
            if obs.ndim != 2 or actions.ndim != 2 or len(obs) == 0:
                raise ValueError("Expected nonempty two-dimensional observations and actions")
            size = len(obs)
            expected = {"actions": (size, actions.shape[1]), "rewards": (size,),
                        "obs_next": obs.shape, "terminated": (size,), "truncated": (size,)}
            for key, shape in expected.items():
                if arrays[key].shape != shape:
                    raise ValueError(f"Invalid {key} shape; expected {shape}")
            metadata = {"action_repeat", "reward_convention", "steps_executed"}
            if metadata.intersection(data.files):
                if not metadata.issubset(data.files):
                    raise ValueError("Incomplete action-repeat metadata")
                repeat = data["action_repeat"].item()
                if data["reward_convention"].item() != "sum_per_decision":
                    raise ValueError("Unsupported reward convention")
                durations = data["steps_executed"]
                if durations.shape != (size,):
                    raise ValueError("Invalid steps_executed shape")
            else:
                repeat, durations = 1, np.ones(size, dtype=np.int32)
            result = cls(obs.shape[1], actions.shape[1], size, batch_size, device,
                         action_repeat=repeat)
            for i in range(size):
                result.push(obs[i], actions[i], arrays["rewards"][i], arrays["obs_next"][i],
                            arrays["terminated"][i], arrays["truncated"][i],
                            steps_executed=durations[i])
        return result
