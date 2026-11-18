from unittest.mock import Mock

import numpy as np
import pytest
import torch

from gym_torcs.client import DriverAction, ServerState
from gym_torcs.env import TorcsEnv
from torcsrl import DDPG, NStepDDPG
from torcsrl.models.ddpg_networks import ActorMLP


@pytest.fixture
def env():
    environment = TorcsEnv(telemetry_mode="standard", observation_noise=False)
    state = dict(
        speedX=50.0, speedY=0.0, speedZ=0.0, rpm=4000.0, gear=2,
        angle=0.0, trackPos=0.0, wheelSpinVel=[0.0] * 4,
        track=[100.0] * 19, damage=0.0, distRaced=10.0,
        curLapTime=1.0, lastLapTime=0.0, x=0.0, y=0.0, distFromStart=10.0,
    )
    environment.client = Mock(state=ServerState(data=state), action=DriverAction())
    environment.client.receive.return_value = state
    yield environment
    environment.close()


@pytest.mark.parametrize("action, expected", [
    ([0.2, 0.7, 0.4], [0.2, 0.7, 0.4]),
    ([2.0, -0.3, 1.5], [1.0, 0.0, 1.0]),
    ([-2.0, 1.5, -0.3], [-1.0, 1.0, 0.0]),
])
def test_step_sends_independent_pedals_with_component_bounds(env, action, expected):
    np.testing.assert_array_equal(env.action_space.low, [-1, 0, 0])
    np.testing.assert_array_equal(env.action_space.high, [1, 1, 1])
    env.step(np.array(action, dtype=np.float32))
    command = env.client.action
    np.testing.assert_allclose([command.steer, command.accel, command.brake], expected)
    np.testing.assert_allclose(env.prev_action, expected)
    assert command.gear == 2
    env.client.send.assert_called_once()


@pytest.mark.parametrize("action", [
    [0.0, 0.5], [0.0, 0.5, 0.0, 0.0], [[0.0, 0.5, 0.0]],
    [float("nan"), 0.0, 0.0], [0.0, float("inf"), 0.0],
])
def test_invalid_actions_are_rejected_before_sending(env, action):
    with pytest.raises(ValueError, match="Expected action shape|must be finite"):
        env.step(np.array(action, dtype=np.float32))
    env.client.send.assert_not_called()


def test_invalid_teacher_is_not_used():
    assert TorcsEnv._expert_action(dict(
        titaSteer=0.2, titaGas=0.7, titaBrake=0.4, titaValid=0.0,
    )) is None


def test_ddpg_actor_maps_tanh_to_pedal_ranges_and_keeps_gradients(env):
    actor = ActorMLP(45, env.action_space, h1_dim=8, h2_dim=8)
    with torch.no_grad():
        for parameter in actor.parameters():
            parameter.zero_()
        actor.mlp[-2].bias.copy_(torch.atanh(torch.tensor([0.4, -0.6, 0.6])))
    action = actor(torch.zeros(1, 45))
    torch.testing.assert_close(action, torch.tensor([[0.4, 0.2, 0.8]]))
    assert {"action_scale", "action_bias"} <= dict(actor.named_buffers()).keys()
    assert "action_scale" not in dict(actor.named_parameters())
    action.sum().backward()
    gradient = actor.mlp[-2].bias.grad
    assert gradient is not None and torch.isfinite(gradient).all() and (gradient > 0).all()


@pytest.mark.parametrize("algorithm", [DDPG, NStepDDPG])
def test_three_action_ddpg_exploration_replay_and_gradient_update(env, algorithm):
    agent = algorithm(
        env, env, lr_actor=1e-3, lr_critic=1e-3,
        ac_kwargs=dict(h1_dim=16, h2_dim=16), buffer_size=16,
        buffer_start_size=4, batch_size=4, verbose=False,
    )
    rng = np.random.default_rng(0)
    for _ in range(8):
        obs = rng.normal(size=45).astype(np.float32)
        action = agent.act_numpy(obs, deterministic=False)
        assert action.shape == (3,) and env.action_space.contains(action)
        transition = (obs, action, 1.0, obs * 0.9, False)
        if algorithm is NStepDDPG:
            agent.replay_buffer.push(*transition, 3)
        else:
            agent.replay_buffer.push(*transition)
    assert agent.replay_buffer.sample()[1].shape == (4, 3)
    before = [parameter.detach().clone() for parameter in agent.actor.parameters()]
    agent.n_gradient_steps()
    assert any(not torch.equal(old, new) for old, new in zip(before, agent.actor.parameters()))
    assert all(torch.isfinite(parameter).all() for parameter in agent.critic.parameters())


def test_expert_collection_reports_missing_teacher(env):
    agent = DDPG(
        env, env, lr_actor=1e-3, lr_critic=1e-3,
        ac_kwargs=dict(h1_dim=8, h2_dim=8), buffer_size=8,
        buffer_start_size=4, batch_size=4, verbose=False,
    )
    env.reset = Mock(return_value=(np.zeros(45, dtype=np.float32), {"action_tita": None}))
    with pytest.raises(RuntimeError, match="valid Tita teacher action"):
        agent.collect_expert_rollouts()
    env.client.send.assert_not_called()


def test_expert_collection_keeps_persisted_copy_after_online_overwrite(env, tmp_path):
    from torcsrl.buffers.expert_replay_buffer import ExpertReplayBuffer

    agent = DDPG(
        env, env, lr_actor=1e-3, lr_critic=1e-3,
        ac_kwargs=dict(h1_dim=8, h2_dim=8), buffer_size=2,
        buffer_start_size=2, batch_size=2, verbose=False,
    )
    obs = np.zeros(45, dtype=np.float32)
    action = np.array([0.1, 0.5, 0.0], dtype=np.float32)
    env.reset = Mock(return_value=(obs, {"action_tita": action}))
    env.step = Mock(side_effect=[
        (obs + 1, 1.0, False, True, {"action_tita": action}),
        (obs + 2, 2.0, True, False, {"action_tita": action}),
    ])
    archive = tmp_path / "warmup.npz"
    agent.collect_expert_rollouts(dataset_path=archive)
    np.testing.assert_array_equal(agent.replay_buffer.rewards, [1, 2])
    for _ in range(3):
        agent.replay_buffer.push(obs, action, -10, obs, False)
    np.testing.assert_array_equal(agent.expert_buffer.rewards, [1, 2])
    restored = ExpertReplayBuffer.load(archive, batch_size=2)
    np.testing.assert_array_equal(restored.rewards, [1, 2])
    np.testing.assert_array_equal(restored.truncated, [True, False])
