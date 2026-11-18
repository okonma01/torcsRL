from collections import deque
from types import SimpleNamespace
from unittest.mock import Mock

import gymnasium as gym
import numpy as np
import pytest

from gym_torcs.wrappers import ActionRepeatWrapper
from torcsrl.algorithms.n_step_td3 import NStepTD3
from torcsrl.buffers.expert_replay_buffer import ExpertReplayBuffer
from torcsrl.buffers.n_step_replay_buffer import NStepReplayBuffer
from torcsrl.expert import collect_expert_transitions


class CountingEnv(gym.Env):
    def __init__(self, end_at=None, truncated=False, timeout_at=None):
        self.observation_space = gym.spaces.Box(-100, 100, (2,), dtype=np.float32)
        self.action_space = gym.spaces.Box(
            np.array([-1, 0, 0], dtype=np.float32), np.ones(3, dtype=np.float32))
        self.end_at, self.truncated, self.timeout_at = end_at, truncated, timeout_at
        self.count = 0
        self.actions = []

    def info(self):
        return {"action_tita": np.array([self.count / 100, 0.5, 0], dtype=np.float32)}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.count = 0
        return np.zeros(2, dtype=np.float32), self.info()

    def step(self, action):
        self.actions.append(action.copy())
        self.count += 1
        done = self.count == self.end_at
        info = self.info()
        if self.count == self.timeout_at:
            info["torcs_timeout"] = True
        return (np.full(2, self.count, dtype=np.float32), float(self.count),
                done and not self.truncated, done and self.truncated, info)


@pytest.mark.parametrize("repeat", [1, 4])
def test_repeats_identical_actions_and_sums_rewards(repeat):
    base = CountingEnv()
    env = ActionRepeatWrapper(base, repeat)
    _, info = env.reset()
    assert info["action_repeat"] == repeat
    action = info["action_tita"]
    obs, reward, terminated, truncated, info = env.step(action)
    assert reward == sum(range(1, repeat + 1))
    assert not terminated and not truncated
    assert info["steps_executed"] == repeat
    np.testing.assert_array_equal(obs, [repeat, repeat])
    np.testing.assert_array_equal(info["action_tita"], base.info()["action_tita"])
    assert len(base.actions) == repeat
    for sent in base.actions:
        np.testing.assert_array_equal(sent, action)


@pytest.mark.parametrize("truncated", [False, True])
def test_stops_on_either_episode_flag(truncated):
    base = CountingEnv(end_at=2, truncated=truncated)
    env = ActionRepeatWrapper(base)
    _, info = env.reset()
    obs, reward, terminated, actual_truncated, info = env.step(info["action_tita"])
    assert len(base.actions) == 2
    assert reward == 3
    assert terminated == (not truncated) and actual_truncated == truncated
    assert info["steps_executed"] == 2
    np.testing.assert_array_equal(obs, [2, 2])


@pytest.mark.parametrize("repeat", [0, -1, 1.5, True])
def test_invalid_repeat(repeat):
    with pytest.raises(ValueError, match="positive integer"):
        ActionRepeatWrapper(CountingEnv(), repeat)


def test_nested_repeat_is_rejected():
    env = gym.wrappers.OrderEnforcing(ActionRepeatWrapper(CountingEnv()))
    with pytest.raises(ValueError, match="already enabled"):
        ActionRepeatWrapper(env)


def test_collection_and_archive_keep_decision_timing(tmp_path):
    base = CountingEnv(end_at=6)
    expert = ExpertReplayBuffer(2, 3, 2, 2)
    collect_expert_transitions(ActionRepeatWrapper(base), expert, 2)
    assert len(base.actions) == 6 and len(expert) == 2
    np.testing.assert_array_equal(expert.rewards, [10, 11])
    np.testing.assert_array_equal(expert.obs, [[0, 0], [4, 4]])
    np.testing.assert_array_equal(expert.obs_next, [[4, 4], [6, 6]])
    np.testing.assert_array_equal(expert.steps_executed, [4, 2])
    np.testing.assert_array_equal(expert.dones, [0, 1])
    np.testing.assert_allclose(expert.actions[:, 0], [0, 0.04])
    archive = tmp_path / "repeat.npz"
    expert.save(archive)
    restored = ExpertReplayBuffer.load(archive, 2)
    assert restored.action_repeat == 4 and len(restored.sample()) == 5
    np.testing.assert_array_equal(restored.steps_executed, [4, 2])
    with np.load(archive) as data:
        assert data["reward_convention"].item() == "sum_per_decision"


def test_timeout_discards_incomplete_repeat(tmp_path):
    expert = ExpertReplayBuffer(2, 3, 2, 1)
    env = ActionRepeatWrapper(CountingEnv(timeout_at=6))
    with pytest.raises(RuntimeError, match="no valid next observation"):
        collect_expert_transitions(env, expert, 2)
    assert len(expert) == 1
    expert.save(tmp_path / "partial.npz")
    restored = ExpertReplayBuffer.load(tmp_path / "partial.npz", 1)
    np.testing.assert_array_equal(restored.rewards, [10])
    np.testing.assert_array_equal(restored.steps_executed, [4])


def test_collection_rejects_mixed_repeat_settings():
    expert = ExpertReplayBuffer(2, 3, 3, 1)
    collect_expert_transitions(ActionRepeatWrapper(CountingEnv()), expert, 1)
    base = CountingEnv()
    with pytest.raises(ValueError, match="must match"):
        collect_expert_transitions(ActionRepeatWrapper(base, 2), expert, 1)
    assert len(base.actions) == 0 and len(expert) == 1


def test_old_archive_defaults_to_single_step(tmp_path):
    archive = tmp_path / "old.npz"
    np.savez(archive, obs=np.zeros((2, 2)), actions=np.zeros((2, 3)),
             rewards=np.ones(2), obs_next=np.ones((2, 2)),
             terminated=np.array([False, True]), truncated=np.array([True, False]))
    restored = ExpertReplayBuffer.load(archive, 2)
    assert restored.action_repeat == 1
    np.testing.assert_array_equal(restored.steps_executed, [1, 1])


def test_n_step_returns_count_decisions():
    env = ActionRepeatWrapper(CountingEnv())
    obs, info = env.reset()
    states, actions, rewards = deque([obs]), deque(), deque()
    for _ in range(2):
        action = info["action_tita"]
        obs, reward, _, _, info = env.step(action)
        states.append(obs)
        actions.append(action)
        rewards.append(reward)
    replay = NStepReplayBuffer(2, 3, 2, 1)
    agent = SimpleNamespace(gamma=0.9, replay_buffer=replay)
    NStepTD3.push_n_step_transition(agent, states, actions, rewards, False)
    assert replay.rewards[0] == pytest.approx(10 + 0.9 * 26)
    assert replay.steps[0] == 2
    np.testing.assert_array_equal(replay.obs_next[0], [8, 8])


@pytest.mark.parametrize("repeat", [None, 1, 2])
def test_commands_apply_repeat_to_collection_training_and_evaluation(monkeypatch, tmp_path, repeat):
    from scripts import collect_expert, train

    monkeypatch.setattr(gym, "make", lambda *args, **kwargs: CountingEnv())
    extra = [] if repeat is None else ["--action-repeat", str(repeat)]
    expected = 4 if repeat is None else repeat
    archive = tmp_path / "cli.npz"
    monkeypatch.setattr("sys.argv", ["collect_expert", "--steps", "2", "--output", str(archive), *extra])
    collect_expert.main()
    restored = ExpertReplayBuffer.load(archive, 1)
    assert len(restored) == 2 and restored.action_repeat == expected
    np.testing.assert_array_equal(restored.steps_executed, [expected, expected])
    factory = Mock()
    monkeypatch.setattr(train, "NStepTD3", factory)
    monkeypatch.setattr("sys.argv", ["train", "--steps", "2", *extra])
    train.main()
    train_env, val_env = factory.call_args.args
    assert train_env.action_repeat == val_env.action_repeat == expected
    factory.return_value.train.assert_called_once_with(2)


@pytest.mark.parametrize("command", ["collect_expert", "train"])
def test_commands_validate_repeat_before_creating_environment(monkeypatch, tmp_path, command):
    from scripts import collect_expert, train

    make = Mock()
    monkeypatch.setattr(gym, "make", make)
    args = [command, "--action-repeat", "0"]
    if command == "collect_expert":
        args += ["--output", str(tmp_path / "invalid.npz")]
    monkeypatch.setattr("sys.argv", args)
    with pytest.raises(SystemExit) as error:
        {"collect_expert": collect_expert, "train": train}[command].main()
    assert error.value.code == 2
    make.assert_not_called()
