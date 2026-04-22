"""Live tests for the Google Tasks provider via the GenericAdapter.

Google Tasks supports a small subset of fields (title, notes, due_date,
completed). Everything else (priority, tags, reminders, sub-tasks beyond
flat list, recurrence) goes through the home_tasks overlay.

Setup:  HT_GOOGLE_TASKS_TEST_ENTITY=todo.<your_test_list>
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_google_tasks]

SETTLE = 0.6


async def _wipe(ws: HAWebSocketClient, entity_id: str) -> None:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(f"Refusing to wipe {entity_id}: {len(tasks)} > max")
    for t in tasks:
        try:
            await ws.call_service(
                "todo", "remove_item",
                {"entity_id": entity_id, "item": t["id"]},
            )
        except Exception as err:  # noqa: BLE001
            print(f"[google_tasks cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


@pytest.fixture
async def google_entity(ws_client: HAWebSocketClient):
    entity_id = CONFIG.google_tasks_entity
    assert entity_id
    await _wipe(ws_client, entity_id)
    yield entity_id
    # Best-effort teardown so leftover test tasks don't pile up at Google.
    try:
        await _wipe(ws_client, entity_id)
    except Exception as err:  # noqa: BLE001
        print(f"[google_tasks teardown] wipe failed: {err}")


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


def _find_provider_item(items: list[dict], uid: str) -> dict | None:
    return next((i for i in items if i.get("uid") == uid), None)


async def test_create_basic_task(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Title must reach Google itself, not only our merged view."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google smoke",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next((t for t in tasks if t["title"] == "Google smoke"), None)
    assert task is not None

    # provider-side truth
    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None, "Task not present on Google side"
    assert pi["summary"] == "Google smoke"


async def test_create_with_notes(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Notes must arrive at Google as the task description."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google notes",
        notes="A Google Tasks description",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google notes")
    assert task["notes"] == "A Google Tasks description"

    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi.get("description") == "A Google Tasks description"


async def test_create_with_due_date(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """due_date must be stored on Google, not only in our overlay."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Due Google",
        due_date="2027-12-10",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Due Google")
    assert task["due_date"] == "2027-12-10"

    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi.get("due") == "2027-12-10"


async def test_due_time_is_dropped_for_google_without_pollution(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Google Tasks has no time-of-day support — due_time is intentionally dropped.

    Google's Tasks API simply cannot store a time-of-day on a due date (open
    since 2013: https://issuetracker.google.com/issues/36759725).  Home Tasks'
    capability table therefore lists "Due Time = no" for Google, and the
    feature bit SET_DUE_DATETIME_ON_ITEM is not exposed by the entity
    (supported_features=95 lacks bit 32).

    What the test fixes in stone:
      - due_date still arrives at Google (date-only, as Google wants)
      - due_time is silently dropped (None in our merged view)
      - the time value must NEVER be smuggled into Google's summary or
        description as a workaround — that would corrupt the task in the
        Google Tasks app itself.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google due time",
        due_date="2027-12-10",
        due_time="16:45",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google due time")
    uid = task["id"]
    # Date survives; time is dropped (Google limitation, documented in README).
    assert task["due_date"] == "2027-12-10"
    assert task["due_time"] in (None, ""), (
        f"Home Tasks returned due_time={task['due_time']!r} for a Google task — "
        "expected dropped (None) because Google has no time-of-day support."
    )

    # Provider side: summary unchanged, date-only due, no 16:45 smuggled
    # anywhere in the Google task's user-visible fields.
    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Google due time", (
        f"Summary changed to {pi['summary']!r} — due_time leaked into the title"
    )
    due_raw = pi.get("due") or ""
    assert due_raw == "2027-12-10", (
        f"Google due={due_raw!r} contains more than date — "
        "the time leaked into the provider's due field"
    )
    desc = pi.get("description") or ""
    assert "16:45" not in desc, (
        f"Description contains {desc!r} — due_time smuggled into Google's description"
    )


async def test_update_title(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Renaming must reach Google's summary field."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google original",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google original")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid,
        title="Google renamed",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    assert any(t["title"] == "Google renamed" for t in tasks)

    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Google renamed"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Check-off must flip the status at Google itself."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google to complete",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google to complete")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Provider side: task must now appear as completed — either in the
    # "completed" bucket or removed from the open bucket (depending on
    # how the HA integration filters).  Either outcome is correct as long
    # as it is NOT in the open list any more.
    open_items = await ws_client.get_provider_items(
        google_entity, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None, (
        "Completed task is still in the Google Tasks open list — "
        "the check-off never reached Google."
    )
    completed_items = await ws_client.get_provider_items(
        google_entity, status="completed",
    )
    pi = _find_provider_item(completed_items, uid)
    if pi is not None:
        # If the integration exposes the status field, it must say completed
        assert pi.get("status") == "completed"


# ---------------------------------------------------------------------------
# Overlay routing — these fields must NEVER leak into the provider state
# ---------------------------------------------------------------------------


async def test_priority_persists_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Priority is an overlay-only field — must not corrupt Google's task.

    Google Tasks has no priority concept.  We store it in our overlay.
    The test asserts two things:
      (1) Our merged view returns the overlay value.
      (2) The Google task's description and summary were NOT hijacked to
          carry the priority value — doing so would corrupt the user's
          task in the Google Tasks app.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google priority",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google priority")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid,
        priority=2,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google priority")
    assert task["priority"] == 2

    # Provider-side: summary unchanged, no priority value smuggled in
    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Google priority", (
        f"Summary changed to {pi['summary']!r} — priority leaked into Google"
    )
    assert not pi.get("description"), (
        f"Description now contains {pi.get('description')!r} — "
        "overlay priority leaked into Google's task description"
    )


async def test_reorder_external_tasks(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """reorder_external_tasks must push the new order to Google Tasks itself.

    This is the dual-view test that would have caught the original bug:
    we verify BOTH our merged get_external_tasks view AND the provider-native
    todo.get_items view.  If the Google Tasks API never received the change,
    todo.get_items still returns the old order — so if both views agree on
    the new order, the reorder really reached Google.

    Google Tasks reports MOVE_TODO_ITEM (feature bit 8), so the reorder must
    be marked provider_handled=True and go through the direct entity path
    (GenericAdapter calls TodoListEntity.async_move_todo_item).
    """
    # Create 3 tasks (GenericAdapter returns uid=None; fetch real UIDs afterwards)
    titles_in_order = ["Reorder A", "Reorder B", "Reorder C"]
    for title in titles_in_order:
        await ws_client.send_command(
            "home_tasks/create_external_task",
            entity_id=google_entity, title=title,
        )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    uid_by_title = {t["title"]: t["id"] for t in tasks if t["title"] in titles_in_order}
    assert len(uid_by_title) == 3, f"Expected 3 tasks, found: {list(uid_by_title)}"
    uids = [uid_by_title[t] for t in titles_in_order]  # [uid_A, uid_B, uid_C]

    # Reorder: C, A, B
    new_order = [uids[2], uids[0], uids[1]]
    expected_titles = ["Reorder C", "Reorder A", "Reorder B"]

    result = await ws_client.send_command(
        "home_tasks/reorder_external_tasks",
        entity_id=google_entity,
        task_uids=new_order,
    )
    # Provider MUST have handled the reorder natively.  If this asserts
    # False, our code fell back to overlay and Google Tasks does NOT have
    # the new order — exactly the silent bug we're guarding against.
    assert result["provider_handled"] is True, (
        "Google Tasks reorder was NOT pushed to the provider — "
        "home_tasks used its overlay fallback.  Google itself still has "
        "the old order.  Check provider_adapters.GenericAdapter.async_reorder_tasks."
    )
    await asyncio.sleep(SETTLE)

    # --- View 1: our merged view ---
    tasks = await _refetch(ws_client, google_entity)
    our_tasks = [t for t in tasks if t["id"] in uids]
    ordered = sorted(our_tasks, key=lambda t: t["sort_order"])
    assert [t["title"] for t in ordered] == expected_titles

    # --- View 2: provider's own view via todo.get_items ---
    # This bypasses our overlay entirely and returns what Google Tasks
    # itself told HA.  Must match the expected order too, otherwise the
    # reorder reached only our overlay and not Google.
    provider_items = await ws_client.get_provider_items(google_entity)
    provider_titles = [
        i["summary"] for i in provider_items if i["uid"] in uids
    ]
    assert provider_titles == expected_titles, (
        f"Google Tasks provider still reports order {provider_titles}, "
        f"expected {expected_titles}.  The reorder landed in our overlay "
        "but was NOT pushed to Google."
    )


async def test_reorder_with_completed_task_in_list(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Reorder over a list that contains a completed task.

    The card builds the reorder UID array from its own cached view, which
    includes completed tasks.  The adapter therefore gets asked to move a
    UID whose status is "completed".  If Google's
    async_move_todo_item raises on completed items, a single exception in
    GenericAdapter's loop would flip the whole batch to overlay fallback
    (provider_handled=False), so Google would never receive the reorder
    of the open tasks either.

    Real-world scenario: a user ticks a task off in the middle of a list,
    later drags another task to a new position.  Must still reach Google.
    """
    # Create 4 open tasks
    titles = ["MixA", "MixB", "MixC", "MixD"]
    for title in titles:
        await ws_client.send_command(
            "home_tasks/create_external_task",
            entity_id=google_entity, title=title,
        )
    await asyncio.sleep(SETTLE)

    all_items = await _refetch(ws_client, google_entity)
    uid_by_title = {t["title"]: t["id"] for t in all_items if t["title"] in titles}
    assert len(uid_by_title) == 4
    uids = {t: uid_by_title[t] for t in titles}

    # Mark MixC as completed — this is the task we drag together with open ones
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uids["MixC"],
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Reorder all four, putting the completed one in the middle — this is
    # exactly what the card sends when the user drags MixD from the end
    # to the front and leaves the (already completed) MixC where it sits
    # in the card's display.
    new_order = [uids["MixD"], uids["MixA"], uids["MixC"], uids["MixB"]]

    result = await ws_client.send_command(
        "home_tasks/reorder_external_tasks",
        entity_id=google_entity,
        task_uids=new_order,
    )
    assert result["provider_handled"] is True, (
        "Reorder with a completed task in the list was NOT handled by the "
        "provider — a single problematic UID broke the whole batch and "
        "triggered overlay fallback.  The open tasks' new order never "
        "reached Google."
    )
    await asyncio.sleep(SETTLE)

    # Provider-side verification.  We don't hard-assert MixC's position in
    # the "open" list (it isn't there), but the remaining open tasks must
    # appear in the reorder we asked for, skipping MixC.
    provider_open = await ws_client.get_provider_items(
        google_entity, status="needs_action",
    )
    open_titles = [
        i["summary"] for i in provider_open if i["uid"] in uid_by_title.values()
    ]
    expected_open = ["MixD", "MixA", "MixB"]  # MixC is completed, not in this list
    assert open_titles == expected_open, (
        f"Provider-side open-task order is {open_titles}, expected "
        f"{expected_open}.  The reorder did not fully reach Google."
    )

    # MixC is still present on the completed side.
    provider_completed = await ws_client.get_provider_items(
        google_entity, status="completed",
    )
    completed_uids = [i["uid"] for i in provider_completed]
    assert uids["MixC"] in completed_uids


async def test_sub_task_lifecycle_on_google(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Sub-tasks on Google Tasks: add, update, delete via home_tasks/*.

    Google Tasks supports hierarchy natively (parent/child).  Our adapter
    handles sub-tasks for Google through the overlay store because
    GenericAdapter.capabilities.can_sync_sub_items defaults to False.
    This test pins down the contract: sub-tasks appear in the merged
    view (from overlay), complete/rename work, delete works.
    """
    parent = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Sub parent G",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    parent_task = next(t for t in tasks if t["title"] == "Sub parent G")
    pid = parent_task["id"]

    sub = await ws_client.send_command(
        "home_tasks/add_external_sub_task",
        entity_id=google_entity,
        task_uid=pid,
        title="First sub G",
    )
    sub_id = sub["id"]
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    sub_items = parent_task.get("sub_items") or []
    assert any(s["id"] == sub_id and s["title"] == "First sub G" for s in sub_items), (
        f"Sub-task not visible in merged view: {sub_items!r}"
    )

    # Overlay-only contract: the sub-task must NOT exist on Google as a
    # standalone task.  GenericAdapter.capabilities.can_sync_sub_items is
    # False for Google, so sub-tasks live only in our overlay store — a
    # regression that starts pushing them to Google would silently create
    # orphan tasks there.
    all_items = await ws_client.get_provider_items(google_entity)
    smuggled = [
        i for i in all_items
        if i.get("summary") == "First sub G" or i.get("uid") == sub_id
    ]
    assert not smuggled, (
        f"Sub-task leaked into Google as a standalone task: {smuggled!r}. "
        "Google's sub-items should stay in the home_tasks overlay."
    )

    # Rename
    await ws_client.send_command(
        "home_tasks/update_external_sub_task",
        entity_id=google_entity, task_uid=pid, sub_task_id=sub_id,
        title="Renamed sub G",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    renamed = next(s for s in parent_task["sub_items"] if s["id"] == sub_id)
    assert renamed["title"] == "Renamed sub G"

    # Complete
    await ws_client.send_command(
        "home_tasks/update_external_sub_task",
        entity_id=google_entity, task_uid=pid, sub_task_id=sub_id,
        completed=True,
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    done = next(s for s in parent_task["sub_items"] if s["id"] == sub_id)
    assert done["completed"] is True

    # Delete
    await ws_client.send_command(
        "home_tasks/delete_external_sub_task",
        entity_id=google_entity, task_uid=pid, sub_task_id=sub_id,
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    assert not any(s["id"] == sub_id for s in parent_task.get("sub_items") or []), (
        "Sub-task still in merged view after delete"
    )


async def test_reopen_from_completed_restores_on_provider(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Marking a completed Google task as uncompleted must flip its status there."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Reopen test",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Reopen test")
    uid = task["id"]

    # Complete first
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid, completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Verify Google sees it as completed (not in open bucket)
    open_items = await ws_client.get_provider_items(
        google_entity, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None

    # Reopen
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid, completed=False,
    )
    await asyncio.sleep(SETTLE)

    # Merged view: completed=False
    tasks_after = await _refetch(ws_client, google_entity)
    task_after = next((t for t in tasks_after if t["id"] == uid), None)
    assert task_after is not None, "Task disappeared after reopen"
    assert task_after["completed"] is False

    # Provider-side: back in the open bucket, gone from completed
    open_after = await ws_client.get_provider_items(
        google_entity, status="needs_action",
    )
    completed_after = await ws_client.get_provider_items(
        google_entity, status="completed",
    )
    assert _find_provider_item(open_after, uid) is not None, (
        "Google did not move the task back to the open bucket on reopen"
    )
    assert _find_provider_item(completed_after, uid) is None, (
        "Google still lists the task as completed after reopen"
    )


async def test_delete_removes_task_from_google(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Deleting a task must remove it from Google Tasks itself."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Delete me",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Delete me")
    uid = task["id"]

    # Provider-side sanity: really there
    items = await ws_client.get_provider_items(google_entity)
    assert _find_provider_item(items, uid) is not None

    # Card's delete path
    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": google_entity},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=google_entity, task_uid=uid,
    )
    await asyncio.sleep(SETTLE)

    # Merged view
    tasks_after = await _refetch(ws_client, google_entity)
    assert not any(t["id"] == uid for t in tasks_after)

    # Provider-side: not in open OR completed bucket (really gone)
    open_items = await ws_client.get_provider_items(
        google_entity, status="needs_action",
    )
    completed_items = await ws_client.get_provider_items(
        google_entity, status="completed",
    )
    assert _find_provider_item(open_items, uid) is None
    assert _find_provider_item(completed_items, uid) is None, (
        "Google still has the task — delete only touched the open bucket"
    )


async def test_tags_persist_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    """Tags are overlay-only for Google — must not leak into its task data.

    Google Tasks has no label/tag concept.  Our adapter stores tags in the
    overlay store only.  This test also verifies that the Google task's
    summary and description stay clean — we must not try to work around
    Google's limitation by stuffing tags into the description.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google tags",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google tags")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=uid,
        tags=["google", "live"],
    )
    await asyncio.sleep(SETTLE)

    # Our overlay keeps the tags
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google tags")
    assert sorted(task["tags"]) == ["google", "live"]

    # Provider-side: summary unchanged, no tags smuggled into description
    items = await ws_client.get_provider_items(google_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Google tags", (
        f"Summary changed to {pi['summary']!r} — tags leaked into Google"
    )
    assert not pi.get("description"), (
        f"Description contains {pi.get('description')!r} — "
        "overlay tags leaked into Google's task description"
    )
