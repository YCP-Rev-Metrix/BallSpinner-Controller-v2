import datetime as dt

import pytest

from backend.cloud_api.CloudAPI import CloudAPI
from backend.models.SessionData import SessionData


@pytest.mark.integration
def test_get_test_data_real():
    """Smoke test: ensure the test endpoint returns a successful JSON response."""
    api = CloudAPI()
    status_code, data = api.get_test_data()

    assert status_code == 200
    assert isinstance(data, (dict, list))


@pytest.mark.integration
def test_get_sessions_in_time_range_real():
    """Ensure GetAllPiSessions returns a list of sessions."""
    api = CloudAPI()
    result = api.get_sessions_in_time_range('00000000000000', '99999999999999')

    assert result['status_code'] == 200
    assert isinstance(result['data'], list)
    assert len(result['data']) > 0

    # Ensure each item has the expected keys.
    for session in result['data'][:3]:
        assert 'id' in session
        assert 'timeStamp' in session
        assert 'name' in session
        assert 'isShotMode' in session


@pytest.mark.integration
def test_post_session_data_real():
    """Post a session; the API should accept it and return a successful status."""
    api = CloudAPI()

    session = SessionData(
        id=-1,
        timeStamp=dt.datetime.utcnow(),
        name='pytest-session',
        isShotMode=True,
        Spin_Instruction_Points=['A', 'B'],
        Tilt_Instruction_Points=['C'],
        Angle_Instruction_Points=['D'],
    )

    result = api.post_session_data(session)
    assert result['status_code'] == 200
    assert isinstance(result['data'], (dict, list))


@pytest.mark.integration
def test_get_related_data_endpoints_real():
    """Call related read endpoints using a real session ID."""
    api = CloudAPI()

    # Use a session ID that definitely exists (first session returned). If the API changes,
    # this will still exercise the endpoints without assuming a specific ID.
    sessions = api.get_sessions_in_time_range('00000000000000', '99999999999999')['data']
    assert isinstance(sessions, list)
    assert len(sessions) > 0

    session_id = sessions[0]['id']

    # These endpoints should return lists or dicts without throwing.
    assert isinstance(api.get_diagnostic_script_data_by_session(session_id)['data'], (list, dict))
    assert isinstance(api.get_shot_script_data_by_session(session_id)['data'], (list, dict))
    assert isinstance(api.get_smartdot_data(session_id)['data'], (list, dict))
    assert isinstance(api.get_encoder_data(session_id)['data'], (list, dict))
    assert isinstance(api.get_heat_data(session_id)['data'], (list, dict))
