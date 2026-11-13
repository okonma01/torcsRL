"""Validate the four original Tita entries used by the racing baseline."""
from pathlib import Path
import xml.etree.ElementTree as ET


MODULE = "tita"
PROFILES = [
    dict(id="tita:3", index=3, car="car1-trb1", label="TRB1 racer 1 (RWD)"),
    dict(id="tita:4", index=4, car="car2-trb1", label="TRB1 racer 2 (RWD)"),
    dict(id="tita:5", index=5, car="car3-trb1", label="TRB1 racer 3 (RWD)"),
    dict(id="tita:6", index=6, car="car4-trb1", label="TRB1 racer 4 (RWD)"),
]


def configure(data=Path("/usr/local/share/games/torcs")):
    """Require native profiles; do not replace driver setups or car physics."""
    root = ET.parse(data / "drivers/tita/tita.xml").getroot()
    for profile in PROFILES:
        index = profile["index"]
        entry = root.find(f"section[@name='Robots']/section[@name='index']/section[@name='{index}']")
        if entry is None or entry.find("attstr[@name='car name']").get("val") != profile["car"]:
            raise ValueError(f"Original Tita entry does not match {profile['car']}")
        ET.parse(data / "drivers/tita" / str(index) / "default.xml")
        car = profile["car"]
        definition = ET.parse(data / "cars" / car / f"{car}.xml").getroot()
        drive = definition.find("section[@name='Drivetrain']/attstr[@name='type']")
        if drive is None or drive.get("val") != "RWD":
            raise ValueError(f"Expected a rear-wheel-drive car: {car}")


if __name__ == "__main__":
    configure()
    print("Verified four original Tita RWD racing profiles.")
