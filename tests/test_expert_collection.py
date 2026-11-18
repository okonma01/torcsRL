from unittest.mock import Mock

from gymnasium import spaces
import numpy as np
import pytest

from torcsrl.buffers.expert_replay_buffer import ExpertReplayBuffer
from torcsrl.buffers.replay_buffer import ReplayBuffer
from torcsrl.expert import collect_expert_transitions


def environment():
    action = np.array([0.2, 0.7, 0.0], dtype=np.float32)
    env = Mock(action_space=spaces.Box(
        np.array([-1, 0, 0], dtype=np.float32), np.ones(3, dtype=np.float32)))
    env.reset.side_effect = [
        (np.array([0, 1], dtype=np.float32), {"action_tita": action}),
        (np.array([10, 11], dtype=np.float32), {"action_tita": -action * [1, 0, 0]}),
        (np.array([20, 21], dtype=np.float32), {"action_tita": action}),
    ]
    env.step.side_effect = [
        (np.array([2, 3], dtype=np.float32), 1.0, False, True, {"action_tita": action}),
        (np.array([12, 13], dtype=np.float32), -1.0, True, False, {}),
    ]
    return env


def test_episode_boundaries_persistence_and_online_overwrite(tmp_path):
    env = environment()
    expert = ExpertReplayBuffer(2, 3, 2, 2)
    collect_expert_transitions(env, expert, 2, seed=7)
    np.testing.assert_array_equal(expert.obs, [[0, 1], [10, 11]])
    np.testing.assert_array_equal(expert.obs_next, [[2, 3], [12, 13]])
    np.testing.assert_array_equal(expert.dones, [0, 1])
    np.testing.assert_array_equal(expert.truncated, [True, False])
    np.testing.assert_array_equal(expert.actions[0], env.step.call_args_list[0].args[0])
    archive = tmp_path / "expert.npz"
    expert.save(archive)
    restored = ExpertReplayBuffer.load(archive, batch_size=2)
    for key in ("obs", "actions", "rewards", "obs_next", "dones", "truncated"):
        np.testing.assert_array_equal(getattr(restored, key), getattr(expert, key))
    assert len(restored.sample()) == 5
    with pytest.raises(FileExistsError):
        expert.save(archive)
    with pytest.raises(OverflowError):
        expert.push(expert.obs[0], expert.actions[0], 0, expert.obs_next[0], False)
    online = ReplayBuffer(2, 3, 1, 1)
    for i in range(3):
        online.push(np.zeros(2), np.zeros(3), i, np.zeros(2), False)
    np.testing.assert_array_equal(restored.rewards, [1, -1])


def test_timeout_does_not_store_placeholder_observation():
    env = environment()
    env.step.side_effect = [(np.zeros(2), 0.0, False, True, {"torcs_timeout": True})]
    expert = ExpertReplayBuffer(2, 3, 2, 1)
    with pytest.raises(RuntimeError, match="no valid next observation"):
        collect_expert_transitions(env, expert, 2)
    assert len(expert) == 0


def test_partial_archive_contains_only_valid_transitions(tmp_path):
    env = environment()
    env.step.side_effect = [
        (np.array([2, 3], dtype=np.float32), 1, False, False, {"action_tita": None}),
    ]
    expert = ExpertReplayBuffer(2, 3, 3, 1)
    with pytest.raises(RuntimeError, match="valid Tita teacher action"):
        collect_expert_transitions(env, expert, 3)
    expert.save(tmp_path / "partial.npz")
    assert len(ExpertReplayBuffer.load(tmp_path / "partial.npz", 1)) == 1
