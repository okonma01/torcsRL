import numpy as np
import pytest

from gym_torcs.env import TorcsEnv


def standard_state():
    return dict(speedX=50.0, speedY=0.0, speedZ=0.0, rpm=4000.0,
                angle=0.0, trackPos=0.4, wheelSpinVel=[0.0] * 4,
                track=[100.0] * 19, damage=0.0)


def test_standard_scr_observation_and_centerline_reward():
    env = TorcsEnv(telemetry_mode="standard", observation_noise=False)
    try:
        state = standard_state()
        adapted = env._adapt_telemetry(state)
        obs = env._obs(adapted)
        assert obs.shape == (45,)
        assert np.isfinite(obs).all()
        np.testing.assert_array_equal(obs[3:6], 0.0)
        np.testing.assert_array_equal(obs[-12:], 0.0)
        assert env._expert_action(adapted) is None
        assert env._reward(adapted, state, np.zeros(3)) == pytest.approx(0.16)
        assert "accelX" not in state
    finally:
        env.close()


def test_enhanced_scr_fails_with_actionable_error():
    env = TorcsEnv()
    try:
        with pytest.raises(RuntimeError, match="telemetry_mode='standard'"):
            env._adapt_telemetry(standard_state())
    finally:
        env.close()


def test_existing_enhanced_fields_are_preserved():
    env = TorcsEnv(telemetry_mode="standard")
    try:
        state = dict(standard_state(), accelX=2.0, curv25=0.1,
                     titaSteer=0.2, titaGas=0.7, titaBrake=0.1)
        adapted = env._adapt_telemetry(state)
        assert adapted["accelX"] == 2.0
        assert adapted["curv25"] == 0.1
        np.testing.assert_allclose(env._expert_action(adapted), [0.2, 0.7, 0.1])
    finally:
        env.close()
