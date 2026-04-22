"""Live tests for the CalDAV/Nextcloud provider via the GenericAdapter.

CalDAV uses the GenericAdapter (HA's standard todo entity interface) to
talk to Nextcloud.  We verify every CRUD path both through our merged
home_tasks view and through ``todo.get_items`` directly against the
CalDAV entity — if Nextcloud never received the change, the second view
catches it.

For overlay-only fields (priority, tags) we also assert that the CalDAV
item's summary and description stay clean; an accidental "smuggle tags
into the description" would show up as actual garbage in the user's
Nextcloud tasks.

Timing note: the test server runs Nextcloud on SQLite, which is slow
and occasionally needs multiple seconds for a round-trip to settle.
All waits are deliberately generous, and reads retry briefly before
failing.

Setup:  HT_CALDAV_TEST_ENTITY=todo.<your_test_collection>
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_caldav]

# Nextcloud on SQLite is sluggish; be generous
SETTLE = 1.5


async def _wipe(ws: HAWebSocketClient, entity_id: str) -> None:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(
            f"Refusing to wipe {entity_id}: {len(tasks)} tasks > max"
        )
    for t in tasks:
        try:
            await ws.call_service(
                "todo", "remove_item",
                {"entity_id": entity_id, "item": t["id"]},
            )
        except Exception as err:  # noqa: BLE001
            print(f"[caldav cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


def _find_provider_item(items: list[dict], uid: str) -> dict | None:
    return next((i for i in items if i.get("uid") == uid), None)


async def _wait_for_provider_item(
    ws: HAWebSocketClient, entity_id: str, uid: str,
    *, predicate=lambda pi: True, status: str | None = None,
    attempts: int = 6, delay: float = 1.0,
) -> dict | None:
    """Poll todo.get_items until ``predicate`` matches or attempts run out.

    Nextcloud/SQLite can take a few extra round-trips before a write is
    observable — a single read often races against the server's flush.
    """
    last = None
    for _ in range(attempts):
        items = await ws.get_provider_items(entity_id, status=status)
        pi = _find_provider_item(items, uid)
        last = pi
        if pi is not None and predicate(pi):
            return pi
        await asyncio.sleep(delay)
    return last


@pytest.fixture
async def caldav_entity(ws_client: HAWebSocketClient):
    from .conftest import ensure_caldav_available

    entity_id = CONFIG.caldav_entity
    assert entity_id
    await ensure_caldav_available(ws_client, entity_id)
    await _wipe(ws_client, entity_id)
    yield entity_id
    # Best-effort teardown so leftover VTODOs don't pile up at Nextcloud.
    try:
        await _wipe(ws_client, entity_id)
    except Exception as err:  # noqa: BLE001
        print(f"[caldav teardown] wipe failed: {err}")


# ---------------------------------------------------------------------------
# Basic CRUD — dual-view against the CalDAV entity itself
# ---------------------------------------------------------------------------


async def test_create_basic_task(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Title must reach Nextcloud's CalDAV store, not only our merged view."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="CalDAV smoke",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next((t for t in tasks if t["title"] == "CalDAV smoke"), None)
    assert task is not None

    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, task["id"],
        predicate=lambda x: x.get("summary") == "CalDAV smoke",
    )
    assert pi is not None and pi["summary"] == "CalDAV smoke", (
        f"Task did not appear on CalDAV side: {pi!r}"
    )


async def test_create_with_notes(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Notes must arrive at Nextcloud as the VTODO DESCRIPTION property."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="With notes",
        notes="A CalDAV description",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "With notes")
    assert task["notes"] == "A CalDAV description"

    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, task["id"],
        predicate=lambda x: x.get("description") == "A CalDAV description",
    )
    assert pi is not None
    assert pi.get("description") == "A CalDAV description"


async def test_create_with_due_date(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """due_date must land in the CalDAV VTODO DUE field."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="Due CalDAV",
        due_date="2027-11-20",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "Due CalDAV")
    assert task["due_date"] == "2027-11-20"

    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, task["id"],
        predicate=lambda x: x.get("due") == "2027-11-20",
    )
    assert pi is not None
    assert pi.get("due") == "2027-11-20"


async def test_create_with_due_date_and_time(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """due_date + due_time must be stored as a datetime on the VTODO, not a date.

    Nextcloud reports SET_DUE_DATETIME (feature bit 32 in supported_features 119)
    so the adapter sends due_datetime instead of due_date.  The CalDAV side
    must then expose a datetime (with a time component) in ``todo.get_items``.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="Due with time CalDAV",
        due_date="2027-11-20",
        due_time="09:15",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "Due with time CalDAV")
    uid = task["id"]
    assert task["due_date"] == "2027-11-20"
    assert task["due_time"] == "09:15"

    def has_time(pi):
        due = pi.get("due") or ""
        return due.startswith("2027-11-20") and "09:15" in due

    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, uid, predicate=has_time,
    )
    assert pi is not None
    # CalDAV returns due with a time component (e.g. "2027-11-20T09:15:00").
    due_str = pi.get("due") or ""
    assert due_str.startswith("2027-11-20"), (
        f"Nextcloud due={due_str!r}, expected start '2027-11-20'"
    )
    assert "09:15" in due_str, (
        f"Nextcloud due={due_str!r} is missing the '09:15' time — "
        "the time component didn't reach Nextcloud"
    )


async def test_update_title_and_notes(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Renaming + updating notes must both reach Nextcloud."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="Original",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "Original")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid,
        title="Renamed CalDAV",
        notes="Updated notes",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "Renamed CalDAV")
    assert task["notes"] == "Updated notes"

    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, uid,
        predicate=lambda x: (
            x.get("summary") == "Renamed CalDAV"
            and x.get("description") == "Updated notes"
        ),
    )
    assert pi is not None
    assert pi["summary"] == "Renamed CalDAV"
    assert pi.get("description") == "Updated notes"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Check-off must flip the VTODO STATUS to COMPLETED at Nextcloud."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="To complete CalDAV",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "To complete CalDAV")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    # On CalDAV the task either stays (with status=completed) or is moved
    # out of the "needs_action" bucket — both are correct.  The failure
    # we're guarding against is: still present AND still needs_action.
    for _ in range(6):
        open_items = await ws_client.get_provider_items(
            caldav_entity, status="needs_action",
        )
        pi_open = _find_provider_item(open_items, uid)
        if pi_open is None:
            break
        await asyncio.sleep(1.0)
    assert pi_open is None, (
        "Completed CalDAV task is still in the open list — "
        f"the check-off never reached Nextcloud: {pi_open!r}"
    )


# ---------------------------------------------------------------------------
# Overlay routing — these must NOT leak into the CalDAV task
# ---------------------------------------------------------------------------


async def test_priority_persists_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """priority is overlay-only for the generic CalDAV adapter.

    CalDAV *does* have a PRIORITY field in VTODO but our GenericAdapter
    doesn't wire it up (only Todoist's rich adapter does).  So the
    priority must live in our overlay only, and the CalDAV task body
    (summary, description) must stay unpolluted.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="With priority",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "With priority")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid,
        priority=3,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "With priority")
    assert task["priority"] == 3

    pi = await _wait_for_provider_item(ws_client, caldav_entity, uid)
    assert pi is not None
    assert pi["summary"] == "With priority"
    desc = pi.get("description") or ""
    assert "priority" not in desc.lower() and "3" not in desc, (
        f"CalDAV description now contains {desc!r} — priority leaked"
    )


async def test_delete_removes_task_from_caldav(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Deleting a CalDAV task must remove it from Nextcloud itself."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="CalDAV delete me",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "CalDAV delete me")
    uid = task["id"]

    # Sanity: task exists on provider
    pi = await _wait_for_provider_item(ws_client, caldav_entity, uid)
    assert pi is not None

    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": caldav_entity},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=caldav_entity, task_uid=uid,
    )
    await asyncio.sleep(SETTLE)

    tasks_after = await _refetch(ws_client, caldav_entity)
    assert not any(t["id"] == uid for t in tasks_after)

    # Poll-and-wait: Nextcloud/SQLite may take a few seconds to
    # reflect a delete on the server side.
    for _ in range(10):
        items = await ws_client.get_provider_items(caldav_entity)
        if _find_provider_item(items, uid) is None:
            break
        await asyncio.sleep(1.0)
    assert _find_provider_item(items, uid) is None, (
        "Nextcloud still holds the VTODO after delete"
    )


async def test_reopen_from_completed_restores_on_caldav(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """Uncompleting a CalDAV task flips its STATUS back to NEEDS-ACTION."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="CalDAV reopen test",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "CalDAV reopen test")
    uid = task["id"]

    # Complete
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid, completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Reopen
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid, completed=False,
    )
    await asyncio.sleep(SETTLE)

    # Merged view: reopened
    tasks_after = await _refetch(ws_client, caldav_entity)
    task_after = next((t for t in tasks_after if t["id"] == uid), None)
    assert task_after is not None and task_after["completed"] is False

    # Provider-side: back in open bucket
    pi = await _wait_for_provider_item(
        ws_client, caldav_entity, uid,
        predicate=lambda x: x.get("status") == "needs_action",
        status="needs_action",
    )
    assert pi is not None, (
        "Nextcloud did not restore the task to needs_action on reopen"
    )


async def test_reorder_external_tasks_overlay_only_on_caldav(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """CalDAV has no MOVE feature — reorder must land in our overlay only.

    Verifies:
      - home_tasks/reorder_external_tasks returns provider_handled=False
      - A subsequent get_external_tasks reflects the new order via overlay
      - Nextcloud's VTODO bodies are UNCHANGED (no ORDER or priority shift
        smuggled in as a workaround)
    """
    titles = ["CDA", "CDB", "CDC"]
    for t in titles:
        await ws_client.send_command(
            "home_tasks/create_external_task",
            entity_id=caldav_entity, title=t,
        )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    uid_by_title = {t["title"]: t["id"] for t in tasks if t["title"] in titles}
    assert len(uid_by_title) == 3, f"Expected 3 tasks, found {list(uid_by_title)}"
    uids = [uid_by_title[t] for t in titles]

    # Snapshot the VTODO summaries + descriptions we just created
    before_items = await ws_client.get_provider_items(caldav_entity)
    before_by_uid = {
        i["uid"]: {"summary": i.get("summary"), "description": i.get("description")}
        for i in before_items if i.get("uid") in uids
    }

    # Reorder: C, A, B
    new_order = [uids[2], uids[0], uids[1]]
    result = await ws_client.send_command(
        "home_tasks/reorder_external_tasks",
        entity_id=caldav_entity,
        task_uids=new_order,
    )
    assert result["provider_handled"] is False, (
        "CalDAV doesn't support MOVE_TODO_ITEM, so provider_handled must "
        "be False and the reorder falls back to overlay.  Got True."
    )
    await asyncio.sleep(SETTLE)

    # Merged view reflects new order via overlay sort_order
    tasks = await _refetch(ws_client, caldav_entity)
    our = [t for t in tasks if t["id"] in uids]
    ordered = sorted(our, key=lambda t: t["sort_order"])
    assert [t["title"] for t in ordered] == ["CDC", "CDA", "CDB"]

    # Provider side: VTODO bodies unchanged (no smuggling)
    after_items = await ws_client.get_provider_items(caldav_entity)
    after_by_uid = {
        i["uid"]: {"summary": i.get("summary"), "description": i.get("description")}
        for i in after_items if i.get("uid") in uids
    }
    assert after_by_uid == before_by_uid, (
        "CalDAV VTODO summary/description changed during overlay-only "
        f"reorder: before={before_by_uid}, after={after_by_uid}"
    )


async def test_tags_persist_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, caldav_entity: str
) -> None:
    """tags are overlay-only; CalDAV task body must stay clean."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=caldav_entity,
        title="With tags",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "With tags")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=caldav_entity, task_uid=uid,
        tags=["caldav-tag", "live-test"],
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, caldav_entity)
    task = next(t for t in tasks if t["title"] == "With tags")
    assert sorted(task["tags"]) == ["caldav-tag", "live-test"]

    pi = await _wait_for_provider_item(ws_client, caldav_entity, uid)
    assert pi is not None
    assert pi["summary"] == "With tags"
    desc = (pi.get("description") or "").lower()
    assert "caldav-tag" not in desc and "live-test" not in desc, (
        f"CalDAV description now contains {desc!r} — tags leaked"
    )
