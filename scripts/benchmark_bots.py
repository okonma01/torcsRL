"""Run installed native bots alone and save TORCS's per-lap results.

Run inside the TORCS image. Each run has a fresh local configuration, so the
viewer and the bots' persistent learning files are left alone.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import signal
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

from gym_torcs.server import RaceConfig, RaceXml
from scripts.native import catalog, select_bot


DEFAULT_TRACKS = ["road/alpine-2", "road/forza", "oval/michigan", "dirt/dirt-4"]


def read_laps(result_file):
    root = ET.parse(result_file).getroot()
    practice = root.find("./section/section[@name='Results']/section[@name='Practice']")
    if practice is None:
        raise ValueError(f"No practice results in {result_file}")
    laps = []
    for section in practice.findall("section"):
        values = {node.get("name"): float(node.get("val")) for node in section.findall("attnum")}
        laps.append(dict(lap=int(section.get("name")), time_s=values["time"],
                         damage=values["dammages"], top_speed_kmh=values["top speed"] * 3.6))
    return sorted(laps, key=lambda lap: lap["lap"])


def run_race(bot, track, laps, output, timeout):
    folder = output / track["id"].replace("/", "-") / bot["id"].replace(":", "-")
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="torcs-benchmark-") as temporary:
        home = Path(temporary)
        race_file = folder / "practice.xml"
        cfg = RaceConfig(track_name=track["name"], track_category=track["category"], laps=laps)
        RaceXml().write(race_file, cfg)
        select_bot(race_file, bot, display_results="no")
        env = os.environ.copy()
        env["HOME"] = str(home)
        env.pop("TORCSRL_GUI_RACE", None)
        started = time.monotonic()
        timed_out = False
        with (folder / "run.log").open("w") as log:
            process = subprocess.Popen(["/usr/local/bin/torcs", "-r", str(race_file.resolve())],
                                       env=env, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                returncode = process.wait()
        results = sorted((home / ".torcs/results/practice").glob("*.xml"))
        lap_results = []
        if results:
            saved = folder / "results.xml"
            saved.write_bytes(results[-1].read_bytes())
            lap_results = read_laps(saved)
        warm = [lap["time_s"] for lap in lap_results if lap["lap"] > 1]
        record = dict(bot=bot, track=track, requested_laps=laps, laps=lap_results,
                      completed=len(lap_results) == laps and returncode == 0,
                      timed_out=timed_out, returncode=returncode,
                      wall_time_s=round(time.monotonic() - started, 3),
                      best_s=min((lap["time_s"] for lap in lap_results), default=None),
                      mean_s=statistics.mean(lap["time_s"] for lap in lap_results) if lap_results else None,
                      warm_mean_s=statistics.mean(warm) if warm else None,
                      warm_std_s=statistics.pstdev(warm) if warm else None,
                      damage=lap_results[-1]["damage"] if lap_results else None,
                      peak_lap_damage=max((lap["damage"] for lap in lap_results), default=None),
                      damage_free_at_lap_ends=bool(lap_results) and all(lap["damage"] == 0 for lap in lap_results),
                      damage_drop_detected=any(b["damage"] < a["damage"]
                                               for a, b in zip(lap_results, lap_results[1:])))
        (folder / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tracks", nargs="+", default=DEFAULT_TRACKS)
    parser.add_argument("--bots", nargs="+")
    parser.add_argument("--baseline", action="store_true", help="Test the four original Tita RWD cars")
    parser.add_argument("--laps", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    if args.laps < 2 or args.timeout <= 0:
        parser.error("Use at least two laps and a positive timeout")
    installed = catalog()
    if args.baseline:
        by_id = {bot["id"]: bot for bot in installed["bots"]}
        bots = []
        for profile in installed["baseline"]["profiles"]:
            bot = by_id[profile["id"]]
            if bot["car"] != profile["car"]:
                parser.error(f"Car profile is not installed: {profile['car']}")
            bots.append(bot)
    else:
        bots = [bot for bot in installed["bots"] if bot["car"] == "car1-trb1"]
    if args.bots:
        bots = [bot for bot in bots if bot["id"] in args.bots]
        if len(bots) != len(set(args.bots)):
            parser.error("Every requested bot must belong to the selected comparison group")
    tracks_by_id = {track["id"]: track for track in installed["tracks"]}
    if any(track not in tracks_by_id for track in args.tracks):
        parser.error("Unknown track")
    args.output.mkdir(parents=True, exist_ok=True)
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  conditions=("Solo practice, four original Tita RWD profiles, stock driver setups, fuel and damage enabled; fresh local directory per run."
                              if args.baseline else "Solo practice, same car model, default bot setups, fuel and damage enabled; fresh local directory per run."),
                  runs=[])
    for track_id in args.tracks:
        for bot in bots:
            print(f"Running {bot['name']} on {track_id} ({args.laps} laps)", flush=True)
            record = run_race(bot, tracks_by_id[track_id], args.laps, args.output, args.timeout)
            report["runs"].append(record)
            (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            print(f"  finished={record['completed']} laps={len(record['laps'])} "
                  f"best={record['best_s']} mean={record['warm_mean_s']} damage={record['damage']}", flush=True)


if __name__ == "__main__":
    main()
