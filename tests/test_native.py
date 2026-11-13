from unittest.mock import Mock
import xml.etree.ElementTree as ET

import pytest

from scripts import gateway, native


def test_native_config_selects_bot_and_stable_camera(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "config").mkdir(parents=True)
    (data / "config/graph.xml").write_text('<params name="graph"/>')
    monkeypatch.setattr(native, "DATA", data)
    race = native.NativeRace(bot=dict(module="bt", index=2, name="bt 3", car="car1-trb1"),
                             track=dict(name="alpine-2", category="road"), laps=5, camera="follow")
    race.home = tmp_path / "home"
    race.source_torcs_home = tmp_path / "missing"
    race._prepare_config()
    root = ET.parse(race.race_file).getroot()
    for path in ("Drivers", "Drivers Start List"):
        driver = root.find(f"section[@name='{path}']/section[@name='1']")
        assert driver.find("attstr[@name='module']").get("val") == "bt"
        assert driver.find("attnum[@name='idx']").get("val") == "2"
    graph = ET.parse(race.home / ".torcs/config/graph.xml").getroot()
    for name in ("0", "bt 3"):
        section = graph.find(f"section[@name='Display Mode']/section[@name='{name}']")
        assert section.find("attnum[@name='camera head list']").get("val") == "0"
        assert section.find("attnum[@name='camera']").get("val") == "1"


@pytest.mark.parametrize("changes", [{"laps": 0}, {"laps": 1.5}, {"camera": "unknown"}])
def test_bad_options_do_not_stop_existing_race(monkeypatch, changes):
    monkeypatch.setattr(gateway, "catalog", lambda: dict(
        bots=[dict(id="bt:2")], tracks=[dict(id="road/alpine-2")]))
    existing = Mock()
    monkeypatch.setattr(gateway, "native_race", existing)
    with pytest.raises(ValueError):
        gateway.native_control("native-start", dict(bot="bt:2", track="road/alpine-2", **changes))
    existing.close.assert_not_called()


def test_python_cannot_replace_native_race(monkeypatch):
    monkeypatch.setattr(gateway, "native_race", Mock(running=True))
    with pytest.raises(RuntimeError, match="Stop the bot race"):
        gateway.dispatch("start", dict(port=3001, session_id="training", render_mode="human"))
