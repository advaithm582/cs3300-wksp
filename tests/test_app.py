import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task collection before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all existing tasks with default priorities."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_success(client):
    """Create a task and return its default Medium priority."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    assert response.get_json()['priority'] == 'Medium'
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_blank_priority_defaults_to_medium(client):
    """Use Medium when a task priority is blank or whitespace."""
    blank_response = client.post(
        '/api/tasks',
        json={"title": "Blank priority", "priority": ""}
    )
    whitespace_response = client.post(
        '/api/tasks',
        json={"title": "Whitespace priority", "priority": "   "}
    )

    assert blank_response.status_code == 201
    assert whitespace_response.status_code == 201
    assert blank_response.get_json()['priority'] == 'Medium'
    assert whitespace_response.get_json()['priority'] == 'Medium'


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_valid_priorities(client, priority):
    """Accept each supported task priority."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


def test_priority_values_are_returned_by_api(client):
    """Return stored priorities when tasks are listed."""
    client.post(
        '/api/tasks',
        json={"title": "Low task", "priority": "Low"}
    )
    client.post(
        '/api/tasks',
        json={"title": "High task", "priority": "High"}
    )

    response = client.get('/api/tasks')
    data = response.get_json()
    returned_priorities = {
        task['title']: task['priority'] for task in data
    }

    assert returned_priorities['Low task'] == 'Low'
    assert returned_priorities['High task'] == 'High'
    assert returned_priorities['Project-1 Report'] == 'Medium'


@pytest.mark.parametrize('priority', ['Urgent', 'low', 1, [], {}])
def test_add_task_rejects_invalid_priorities(client, priority):
    """Reject priorities outside the supported values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority", "priority": priority}
    )

    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_add_task_missing_title(client):
    """Reject tasks that do not include a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
