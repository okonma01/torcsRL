"""Discover installed TORCS bots and watch them without an SCR client."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from gym_torcs.server import RaceConfig, RaceXml, TorcsServer
from scripts.configure_baseline import MODULE, PROFILES


DATA = Path("/usr/local/share/games/torcs")
LIB = Path("/usr/local/lib/torcs/drivers")
CAMERAS = {
    "follow": (0, 1),
    "bonnet": (0, 2),
    "overhead": (3, 0),
}


def select_bot(race_file, bot, *, display_results="yes"):
    """Replace the SCR entry with one installed native driver."""
    tree = ET.parse(race_file)
    root = tree.getroot()
    drivers = root.find("section[@name='Drivers']")
    RaceXml._set_node(drivers, "focused module", bot["module"], "attstr")
    RaceXml._set_node(drivers, "focused idx", str(bot["index"]), "attnum")
    for section in (drivers.find("section[@name='1']"),
                    root.find("section[@name='Drivers Start List']/section[@name='1']")):
        RaceXml._set_node(section, "module", bot["module"], "attstr")
        RaceXml._set_node(section, "idx", str(bot["index"]), "attnum")
    RaceXml._set_node(root.find("section[@name='Practice']"), "display results", display_results, "attstr")
    tree.write(race_file, encoding="UTF-8", xml_declaration=True)


def catalog(data=DATA, libraries=LIB):
    bots = []
    for folder in sorted((data / "drivers").iterdir()):
        module = folder.name
        definition = folder / f"{module}.xml"
        if module in {"human", "scr_server"} or not definition.is_file():
            continue
        if not (libraries / module / f"{module}.so").is_file():
            continue
        root = ET.parse(definition).getroot()
        for entry in root.findall("./section[@name='Robots']/section[@name='index']/section"):
            name = entry.find("attstr[@name='name']")
            car = entry.find("attstr[@name='car name']")
            if name is not None and car is not None and (data / "cars" / car.get("val")).is_dir():
                bots.append(dict(id=f"{module}:{entry.get('name')}", module=module,
                                 index=int(entry.get("name")), name=name.get("val"), car=car.get("val")))
    tracks = []
    for definition in sorted((data / "tracks").glob("*/*/*.xml")):
        if definition.stem == definition.parent.name:
            tracks.append(dict(id=f"{definition.parent.parent.name}/{definition.stem}",
                               category=definition.parent.parent.name, name=definition.stem))
    comparison = json.loads(Path(__file__).with_name("bot_comparison.json").read_text())
    results_path = Path(__file__).with_name("baseline_results.json")
    baseline = dict(module=MODULE, profiles=PROFILES,
                    runs=json.loads(results_path.read_text()) if results_path.exists() else [])
    return dict(bots=bots, tracks=tracks, comparison=comparison, baseline=baseline)


class NativeRace(TorcsServer):
    def __init__(self, *, bot, track, laps, camera):
        super().__init__(port=3001, render_mode="human", debug=True, startup_sleep=0.5,
                         race_config=RaceConfig(track_name=track["name"],
                                                track_category=track["category"], laps=laps))
        self.bot = bot
        self.camera = camera

    def _prepare_config(self):
        super()._prepare_config()
        select_bot(self.race_file, self.bot)
        self._prepare_camera()

    def _prepare_camera(self):
        target = self.home / ".torcs/config/graph.xml"
        tree = ET.parse(target if target.exists() else DATA / "config/graph.xml")
        display = RaceXml._section(tree.getroot(), "./section[@name='Display Mode']")
        head, camera = CAMERAS[self.camera]
        for name in ("0", self.bot["name"]):
            section = RaceXml._section(display, f"./section[@name='{name}']")
            RaceXml._set_node(section, "camera head list", str(head), "attnum")
            RaceXml._set_node(section, "camera", str(camera), "attnum")
        screen = display.find("section[@name='0']")
        RaceXml._set_node(screen, "current driver", self.bot["name"], "attstr")
        tree.write(target, encoding="UTF-8", xml_declaration=True)
