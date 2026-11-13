import xml.etree.ElementTree as ET

import pytest

from scripts.configure_baseline import PROFILES, configure


def fixture_data(tmp_path):
    drivers = tmp_path / "drivers/tita"
    drivers.mkdir(parents=True)
    root = ET.Element("params")
    entries = ET.SubElement(ET.SubElement(root, "section", name="Robots"), "section", name="index")
    for profile in PROFILES:
        entry = ET.SubElement(entries, "section", name=str(profile["index"]))
        ET.SubElement(entry, "attstr", name="car name", val=profile["car"])
        setup = drivers / str(profile["index"])
        setup.mkdir()
        (setup / "default.xml").write_text('<params name="original setup"/>')
        car = tmp_path / "cars" / profile["car"]
        car.mkdir(parents=True)
        (car / f"{profile['car']}.xml").write_text('<params><section name="Drivetrain"><attstr name="type" val="RWD"/></section></params>')
    ET.ElementTree(root).write(drivers / "tita.xml")
    return tmp_path


def test_native_profiles_are_validated_without_changing_simulator_files(tmp_path):
    data = fixture_data(tmp_path)
    before = {p.relative_to(data): p.read_bytes() for p in data.rglob("*") if p.is_file()}
    configure(data)
    configure(data)
    after = {p.relative_to(data): p.read_bytes() for p in data.rglob("*") if p.is_file()}
    assert before == after


def test_wrong_native_entry_is_rejected(tmp_path):
    data = fixture_data(tmp_path)
    path = data / "drivers/tita/tita.xml"
    path.write_text(path.read_text().replace('val="car1-trb1"', 'val="car1-ow1"'))
    with pytest.raises(ValueError, match="Original Tita entry"):
        configure(data)


def test_four_wheel_drive_is_rejected(tmp_path):
    data = fixture_data(tmp_path)
    path = data / "cars/car1-trb1/car1-trb1.xml"
    path.write_text(path.read_text().replace('val="RWD"', 'val="4WD"'))
    with pytest.raises(ValueError, match="rear-wheel-drive"):
        configure(data)
