"""End-to-end tests of the session cookie and the endpoints hanging off it.

The whole app runs here against a fake Redis: no auth means the cookie is the
only thing standing between one visitor's connected databases and another's, so
it is worth checking that it actually gates every route.
"""
import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """The real app, with a fake Redis swapped in for the lifespan's real one."""
    app.state.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await app.state.redis.aclose()


async def test_health_reports_redis(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "ok"}


async def test_starting_a_session_sets_the_cookie(client):
    response = await client.post("/api/session", json={"name": "Venu Reddy"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Venu Reddy"
    assert body["session_id"].startswith("venu-reddy-")
    assert "sql_agent_session" in response.cookies


async def test_session_round_trips_on_the_cookie_alone(client):
    created = (await client.post("/api/session", json={"name": "Venu"})).json()

    # httpx keeps the cookie; nothing else is sent.
    current = await client.get("/api/session")

    assert current.status_code == 200
    assert current.json()["session_id"] == created["session_id"]
    assert current.json()["connection_count"] == 0


async def test_a_name_is_required(client):
    assert (await client.post("/api/session", json={"name": "   "})).status_code == 422
    assert (await client.post("/api/session", json={})).status_code == 422


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/api/session"),
        ("DELETE", "/api/session"),
        ("GET", "/api/connections"),
        ("POST", "/api/connections"),
        ("GET", "/api/connections/abc"),
        ("DELETE", "/api/connections/abc"),
        ("POST", "/api/connections/abc/natural-query"),
        ("GET", "/api/connections/abc/conversations"),
        ("GET", "/api/connections/abc/conversations/xyz"),
    ],
)
async def test_every_route_needs_a_session(client, method, path):
    """Without a cookie there is no caller, so there is nothing to answer with."""
    response = await client.request(method, path, json={})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NO_SESSION"


async def test_a_session_deleted_server_side_stops_working(client):
    """The cookie outliving the Redis key must fail closed, not 500."""
    sid = (await client.post("/api/session", json={"name": "Venu"})).json()["session_id"]
    await app.state.redis.delete(f"session:{sid}")

    response = await client.get("/api/connections")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "NO_SESSION"


async def test_ending_a_session_clears_everything(client):
    sid = (await client.post("/api/session", json={"name": "Venu"})).json()["session_id"]

    assert (await client.delete("/api/session")).status_code == 204

    assert await app.state.redis.keys(f"session:{sid}*") == []
    assert (await client.get("/api/session")).status_code == 401


async def test_sessions_cannot_see_each_other(client):
    """Two visitors, one Redis: neither should find the other's connections."""
    await client.post("/api/session", json={"name": "Venu"})
    await app.state.redis.hset(
        f"session:{(await client.get('/api/session')).json()['session_id']}:connections",
        "c1",
        '{"name": "mine", "db_type": "postgresql", "host": "h", "port": 1,'
        ' "username": "u", "password": "x", "database_name": "d",'
        ' "created_at": "2025-01-01T00:00:00+00:00"}',
    )
    assert (await client.get("/api/connections")).json()["total"] == 1

    client.cookies.clear()
    await client.post("/api/session", json={"name": "Someone Else"})

    assert (await client.get("/api/connections")).json()["total"] == 0
    assert (await client.get("/api/connections/c1")).status_code == 404


async def test_unsupported_database_type_is_refused(client):
    """Refused before any connection is attempted, with a usable message."""
    await client.post("/api/session", json={"name": "Venu"})

    response = await client.post(
        "/api/connections",
        json={
            "name": "mongo",
            "db_type": "mongodb",
            "credentials": {
                "host": "localhost",
                "port": 27017,
                "username": "u",
                "password": "p",
                "database_name": "d",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_DB_TYPE"


async def test_unreachable_database_is_refused_at_connect_time(client):
    """Better to fail here, with the host in the message, than mid-question."""
    await client.post("/api/session", json={"name": "Venu"})

    response = await client.post(
        "/api/connections",
        json={
            "name": "nowhere",
            "db_type": "postgresql",
            "credentials": {
                "host": "127.0.0.1",
                "port": 1,
                "username": "u",
                "password": "p",
                "database_name": "d",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] in {"INVALID_CREDENTIALS", "CONNECTION_ERROR"}


# ─── The conversation cycle ──────────────────────────────────────────────────
#
# These stub the agent. Everything around it -- guarding, connecting, running
# the SQL -- is covered elsewhere or needs a live model; what is worth pinning
# down here is that a turn is stored, replayed, and thrown away with its
# connection.

@pytest.fixture
async def connected(client, monkeypatch):
    """A session with one connection, and an agent that answers without a model."""
    monkeypatch.setattr(
        "app.connections.service._verify_credentials", lambda *a, **kw: None
    )
    monkeypatch.setattr("app.query.service._engine_for", lambda record: object())

    await client.post("/api/session", json={"name": "Venu"})
    response = await client.post(
        "/api/connections",
        json={
            "name": "demo",
            "db_type": "postgresql",
            "credentials": {
                "host": "demo-db",
                "port": 5432,
                "username": "demo",
                "password": "demo",
                "database_name": "demo",
            },
        },
    )
    return response.json()["id"]


def _agent_returning(query, rows, message=None):
    def run(question, history, engine, db_type=None, database_name=None):
        run.seen_history = history
        return {
            "valid": True,
            "error": None,
            "query": query,
            "result": {"columns": ["city", "n"], "rows": rows},
            "message": message,
        }

    run.seen_history = None
    return run


async def test_a_turn_is_stored_and_replays(client, connected, monkeypatch):
    agent = _agent_returning("SELECT city, count(*) n FROM customers GROUP BY city", [{"city": "London", "n": 2}])
    monkeypatch.setattr("app.query.service.run_agent", agent)

    answer = await client.post(
        f"/api/connections/{connected}/natural-query",
        json={"question": "how many customers per city?"},
    )

    assert answer.status_code == 200
    body = answer.json()
    assert body["rows"] == [{"city": "London", "n": 2}]
    assert body["conversation_id"]

    detail = (
        await client.get(
            f"/api/connections/{connected}/conversations/{body['conversation_id']}"
        )
    ).json()
    assert detail["title"] == "how many customers per city?"
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    # The result snapshot is what makes a conversation reload as you left it.
    assert detail["messages"][1]["sql_query"] == body["query"]
    assert detail["messages"][1]["result"]["rows"] == body["rows"]


async def test_a_follow_up_replays_the_previous_sql(client, connected, monkeypatch):
    """"Now only London" only works if the earlier query reaches the prompt."""
    first = _agent_returning("SELECT city FROM customers", [{"city": "London", "n": 2}])
    monkeypatch.setattr("app.query.service.run_agent", first)
    conversation_id = (
        await client.post(
            f"/api/connections/{connected}/natural-query",
            json={"question": "customers per city?"},
        )
    ).json()["conversation_id"]

    second = _agent_returning("SELECT city FROM customers WHERE city='London'", [])
    monkeypatch.setattr("app.query.service.run_agent", second)
    await client.post(
        f"/api/connections/{connected}/natural-query",
        json={"question": "now only London", "conversation_id": conversation_id},
    )

    replayed = [m.content for m in second.seen_history]
    assert replayed[0] == "customers per city?"
    assert "SELECT city FROM customers" in replayed[1]


async def test_a_failed_turn_is_not_stored(client, connected, monkeypatch):
    """An unanswered question must not poison the next turn's context."""
    def boom(**kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr("app.query.service.run_agent", boom)

    response = await client.post(
        f"/api/connections/{connected}/natural-query", json={"question": "anything"}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "QUERY_ERROR"
    assert (await client.get(f"/api/connections/{connected}/conversations")).json()["total"] == 0


async def test_an_answer_without_a_query_is_not_a_failure(client, connected, monkeypatch):
    """A greeting or a refusal is a real answer; it just has no rows."""
    monkeypatch.setattr(
        "app.query.service.run_agent",
        _agent_returning(None, [], message="Hello! Ask me about your data."),
    )

    body = (
        await client.post(
            f"/api/connections/{connected}/natural-query", json={"question": "hi"}
        )
    ).json()

    assert body["query"] is None
    assert body["message"] == "Hello! Ask me about your data."
    detail = (
        await client.get(
            f"/api/connections/{connected}/conversations/{body['conversation_id']}"
        )
    ).json()
    assert detail["messages"][1]["result"] is None


async def test_deleting_a_connection_takes_its_conversations(client, connected, monkeypatch):
    """History for a database you can no longer reach should not linger."""
    monkeypatch.setattr("app.query.service.run_agent", _agent_returning("SELECT 1", []))
    await client.post(
        f"/api/connections/{connected}/natural-query", json={"question": "anything"}
    )
    sid = (await client.get("/api/session")).json()["session_id"]
    assert await app.state.redis.hlen(f"session:{sid}:conversations") == 1

    assert (await client.delete(f"/api/connections/{connected}")).status_code == 204

    assert await app.state.redis.hlen(f"session:{sid}:conversations") == 0
    assert await app.state.redis.keys(f"session:{sid}:conv:*") == []


async def test_conversation_keys_inherit_the_session_deadline(client, connected, monkeypatch):
    """A conversation started on hour 23 must still die with the session."""
    monkeypatch.setattr("app.query.service.run_agent", _agent_returning("SELECT 1", []))
    conversation_id = (
        await client.post(
            f"/api/connections/{connected}/natural-query", json={"question": "anything"}
        )
    ).json()["conversation_id"]

    sid = (await client.get("/api/session")).json()["session_id"]
    session_deadline = await app.state.redis.expiretime(f"session:{sid}")
    for key in (
        f"session:{sid}:conversations",
        f"session:{sid}:conv:{conversation_id}:messages",
    ):
        assert await app.state.redis.expiretime(key) == session_deadline
