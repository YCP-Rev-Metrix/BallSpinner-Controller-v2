import pytest
import datetime as dt

from backend.models.SmartDotData import SmartDotData, SmartDotDataInstance


def test_SmartDotDataInstance_initialization():
    """Test SmartDotDataInstance stores all sensor data correctly"""
    test_time = dt.datetime.now()
    inst = SmartDotDataInstance(
        time=test_time,
        data_selector=1,
        accelerometer_x=1.0,
        accelerometer_y=2.0,
        accelerometer_z=3.0,
        gyroscope_x=4.0,
        gyroscope_y=5.0,
        gyroscope_z=6.0,
        magnetometer_x=7.0,
        magnetometer_y=8.0,
        magnetometer_z=9.0,
        light=100
    )

    assert inst.time == test_time
    assert inst.data_selector == 1
    assert inst.accelerometer_x == 1.0
    assert inst.accelerometer_y == 2.0
    assert inst.accelerometer_z == 3.0
    assert inst.gyroscope_x == 4.0
    assert inst.gyroscope_y == 5.0
    assert inst.gyroscope_z == 6.0
    assert inst.magnetometer_x == 7.0
    assert inst.magnetometer_y == 8.0
    assert inst.magnetometer_z == 9.0
    assert inst.light == 100


def test_SmartDotDataInstance_string_representation():
    """Test SmartDotDataInstance __str__() contains class name"""
    inst = SmartDotDataInstance(
        time=dt.datetime.now(),
        data_selector=0,
        accelerometer_x=1.0,
        accelerometer_y=2.0,
        accelerometer_z=3.0,
        gyroscope_x=4.0,
        gyroscope_y=5.0,
        gyroscope_z=6.0,
        magnetometer_x=7.0,
        magnetometer_y=8.0,
        magnetometer_z=9.0,
        light=50
    )

    s = str(inst)
    assert "SmartDotDataInstance" in s


def test_SmartDotData_add_data():
    """Test adding SmartDotDataInstance to container"""
    container = SmartDotData()
    inst = SmartDotDataInstance(
        time=dt.datetime.now(),
        data_selector=0,
        accelerometer_x=1.0,
        accelerometer_y=1.0,
        accelerometer_z=1.0,
        gyroscope_x=1.0,
        gyroscope_y=1.0,
        gyroscope_z=1.0,
        magnetometer_x=1.0,
        magnetometer_y=1.0,
        magnetometer_z=1.0,
        light=1
    )

    container.add_new_data(inst)
    entries = container.get_data_entries()

    assert len(entries) == 1
    assert entries[0] == inst


def test_SmartDotData_get_entries_empty():
    """Test SmartDotData returns empty list when no data added"""
    container = SmartDotData()
    entries = container.get_data_entries()

    assert entries == []
    assert len(entries) == 0
