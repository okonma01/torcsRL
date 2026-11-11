from unittest.mock import Mock, patch

from gym_torcs.server import TorcsServer


def test_direct_graphical_start_passes_race_config_and_skips_menu_keys(monkeypatch, tmp_path):
    monkeypatch.setenv("TORCSRL_DIRECT_GUI", "1")
    server = TorcsServer(port=3001, render_mode="human", startup_sleep=0)
    server.home = tmp_path
    server.owns_home = False
    fake = Mock()
    fake.poll.return_value = None
    with patch("gym_torcs.server.subprocess.Popen", return_value=fake) as popen, \
            patch.object(server, "_auto_start_gui_race") as menu_keys:
        server.start()
        assert popen.call_args.kwargs["env"]["TORCSRL_GUI_RACE"] == str(server.race_file)
        menu_keys.assert_not_called()


def test_unpatched_installs_keep_normal_gui_environment(monkeypatch):
    monkeypatch.delenv("TORCSRL_DIRECT_GUI", raising=False)
    monkeypatch.delenv("TORCSRL_GUI_RACE", raising=False)
    server = TorcsServer(port=3001, render_mode="human")
    assert "TORCSRL_GUI_RACE" not in server._env()
