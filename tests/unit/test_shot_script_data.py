import pytest

from backend.models.ShotScriptData import ShotScriptData, ShotScriptDataInstance


def test_ShotScriptDataInstance_initialization():
    """Test ShotScriptDataInstance stores all fields correctly"""
    inst = ShotScriptDataInstance(time=1.5, rpm=1200, angleDeg=25.0, tiltDeg=5.0)

    assert inst.time == 1.5
    assert inst.rpm == 1200
    assert inst.angleDeg == 25.0
    assert inst.tiltDeg == 5.0


def test_ShotScriptData_add_data():
    """Test adding ShotScriptDataInstance to container"""
    container = ShotScriptData()
    inst = ShotScriptDataInstance(time=0.5, rpm=800, angleDeg=10.0, tiltDeg=1.0)

    container.add_shot_script_data(inst)
    entries = container.get_shot_script_data_entries()

    assert len(entries) == 1
    assert entries[0] == inst


def test_ShotScriptData_get_entries_empty():
    """Test ShotScriptData returns empty list when no data added"""
    container = ShotScriptData()
    entries = container.get_shot_script_data_entries()

    assert entries == []
    assert len(entries) == 0
