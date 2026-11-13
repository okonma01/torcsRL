import json
from pathlib import Path

import pytest

from scripts.benchmark_bots import read_laps


def test_read_laps_keeps_lap_order_damage_and_speed_units(tmp_path):
    result = tmp_path / "results.xml"
    result.write_text('''<params><section name="Example track"><section name="Results">
      <section name="Practice"><attstr name="driver name" val="Example bot"/>
        <section name="2"><attnum name="time" val="90.2"/>
          <attnum name="dammages" val="10"/><attnum name="top speed" val="50"/></section>
        <section name="1"><attnum name="time" val="100.3"/>
          <attnum name="dammages" val="0"/><attnum name="top speed" val="40"/></section>
      </section></section></section></params>''')
    laps = read_laps(result)
    assert [lap["lap"] for lap in laps] == [1, 2]
    assert laps[1]["time_s"] == pytest.approx(90.2)
    assert laps[1]["damage"] == 10
    assert laps[1]["top_speed_kmh"] == pytest.approx(180)


def test_comparison_data_supports_shortlist_and_duplicate_claim():
    comparison = json.loads((Path(__file__).parents[1] / "scripts/bot_comparison.json").read_text())
    assert 1 <= len(comparison["shortlist"]) <= 5
    assert len(comparison["shortlist"]) == len(set(comparison["shortlist"]))
    runs = comparison["runs"]
    tracks = {run["track"]["id"] for run in runs}
    for track in tracks:
        by_bot = {run["bot"]["id"]: run for run in runs if run["track"]["id"] == track}
        for bot in comparison["shortlist"]:
            assert by_bot[bot]["completed"]
            assert len(by_bot[bot]["laps"]) == 5
        tied = [by_bot[bot]["laps"] for bot in comparison["same_results"]]
        assert all(laps == tied[0] for laps in tied)
