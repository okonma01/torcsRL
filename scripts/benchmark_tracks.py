"""Compare four racing cars across tracks in a disposable TORCS container.

This changes driver slot 2 inside that container from p406 to car1-stock1.
Do not run it inside the active viewer container.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from scripts.benchmark_bots import run_race
from scripts.native import DATA, catalog


def prepare_racing_cars():
    drivers = DATA / "drivers"
    backup = drivers / ".torcsrl-original-berniw2"
    if not backup.exists():
        shutil.copytree(drivers / "berniw2", backup)
    definition = drivers / "berniw2/berniw2.xml"
    tree = ET.parse(backup / "berniw2.xml")
    profiles = [(4, "car1-ow1", drivers / "tita/1"),
                (3, "car1-trb1", drivers / "tita/3"),
                (2, "car1-stock1", drivers / "berniw/1"),
                (1, "pw-focuswrc", backup / "1")]
    for index, car, source in profiles:
        destination = drivers / "berniw2" / str(index)
        shutil.rmtree(destination)
        shutil.copytree(source, destination)
        entry = tree.getroot().find(f"section[@name='Robots']/section[@name='index']/section[@name='{index}']")
        entry.find("attstr[@name='car name']").set("val", car)
    tree.write(definition, encoding="UTF-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tracks", nargs="+")
    parser.add_argument("--laps", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if args.laps < 2 or args.timeout <= 0:
        parser.error("Use at least two laps and a positive timeout")
    prepare_racing_cars()
    installed = catalog()
    tracks = installed["tracks"]
    if args.tracks:
        unknown = set(args.tracks) - {t["id"] for t in tracks}
        if unknown:
            parser.error(f"Unknown tracks: {sorted(unknown)}")
        tracks = [t for t in tracks if t["id"] in args.tracks]
    bots = {bot["id"]: bot for bot in installed["bots"]}
    ids = ["berniw2:4", "berniw2:3", "berniw2:2", "berniw2:1"]
    args.output.mkdir(parents=True, exist_ok=True)
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  conditions="Berniw2, five-lap solo practice by default; fuel and damage enabled; fresh local settings for each run; car-specific ported setups, no physics changes.",
                  setup_sources={"car1-ow1": "tita/1", "car1-trb1": "tita/3",
                                 "car1-stock1": "berniw/1", "pw-focuswrc": "original berniw2/1"},
                  runs=[])
    for track in tracks:
        for bot_id in ids:
            bot = bots[bot_id]
            result = run_race(bot, track, args.laps, args.output, args.timeout)
            report["runs"].append(result)
            temporary = args.output / "report.tmp"
            temporary.write_text(json.dumps(report, indent=2) + "\n")
            temporary.replace(args.output / "report.json")
            print(f"{track['id']} {bot['car']} completed={result['completed']} "
                  f"warm_mean={result['warm_mean_s']} damage={result['damage']}", flush=True)


if __name__ == "__main__":
    main()
