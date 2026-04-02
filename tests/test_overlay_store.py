"""Unit tests for ExternalTaskOverlayStore."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
async def overlay_store(hass: HomeAssistant):
    """Create a standalone ExternalTaskOverlayStore for testing."""
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    store = ExternalTaskOverlayStore(hass, "todo.test_external")
    await store.async_load()
    return store


async def test_empty_overlay_returned_for_unknown_uid(hass: HomeAssistant, overlay_store) -> None:
    """get_overlay returns defaults for a UID that hasn't been set."""
    overlay = overlay_store.get_overlay("unknown-uid")
    assert overlay["priority"] is None
    assert overlay["tags"] == []
    assert overlay["sub_items"] == []
    assert overlay["recurrence_enabled"] is False


async def test_set_and_get_overlay(hass: HomeAssistant, overlay_store) -> None:
    """Setting an overlay field persists it."""
    await overlay_store.async_set_overlay("uid-1", priority=2, tags=["urgent"])
    overlay = overlay_store.get_overlay("uid-1")
    assert overlay["priority"] == 2
    assert overlay["tags"] == ["urgent"]


async def test_overlay_tags_deduplicated(hass: HomeAssistant, overlay_store) -> None:
    """Duplicate tags in overlay are de-duplicated and lowercased."""
    await overlay_store.async_set_overlay("uid-2", tags=["A", "a", "B"])
    overlay = overlay_store.get_overlay("uid-2")
    assert overlay["tags"] == ["a", "b"]


async def test_delete_overlay(hass: HomeAssistant, overlay_store) -> None:
    """Deleted overlays revert to defaults."""
    await overlay_store.async_set_overlay("uid-3", priority=3)
    await overlay_store.async_delete_overlay("uid-3")
    overlay = overlay_store.get_overlay("uid-3")
    assert overlay["priority"] is None


async def test_sub_task_add_update_delete(hass: HomeAssistant, overlay_store) -> None:
    """Sub-tasks can be added, updated, and deleted in the overlay."""
    sub = await overlay_store.async_add_sub_task("uid-4", "Sub-task title")
    assert sub["title"] == "Sub-task title"
    assert sub["completed"] is False

    updated = await overlay_store.async_update_sub_task("uid-4", sub["id"], completed=True)
    assert updated["completed"] is True

    await overlay_store.async_delete_sub_task("uid-4", sub["id"])
    overlay = overlay_store.get_overlay("uid-4")
    assert overlay["sub_items"] == []


async def test_sub_task_update_nonexistent_overlay_raises(hass: HomeAssistant, overlay_store) -> None:
    """Updating a sub-task on a UID with no overlay raises ValueError."""
    with pytest.raises(ValueError, match="Overlay not found"):
        await overlay_store.async_update_sub_task("no-overlay", "sub-id", completed=True)


async def test_sub_task_delete_nonexistent_raises(hass: HomeAssistant, overlay_store) -> None:
    """Deleting a sub-task that doesn't exist raises ValueError."""
    await overlay_store.async_add_sub_task("uid-5", "Exists")
    with pytest.raises(ValueError):
        await overlay_store.async_delete_sub_task("uid-5", "wrong-sub-id")


async def test_invalid_priority_raises(hass: HomeAssistant, overlay_store) -> None:
    """Setting an invalid priority raises ValueError."""
    with pytest.raises(ValueError, match="priority"):
        await overlay_store.async_set_overlay("uid-6", priority=99)


async def test_invalid_recurrence_unit_raises(hass: HomeAssistant, overlay_store) -> None:
    """Setting an invalid recurrence_unit raises ValueError."""
    with pytest.raises(ValueError, match="recurrence_unit"):
        await overlay_store.async_set_overlay("uid-7", recurrence_unit="fortnightly")


async def test_get_all_overlays(hass: HomeAssistant, overlay_store) -> None:
    """get_all_overlays returns all stored overlays with defaults filled in."""
    await overlay_store.async_set_overlay("uid-a", priority=1)
    await overlay_store.async_set_overlay("uid-b", priority=2)
    overlays = overlay_store.get_all_overlays()
    assert "uid-a" in overlays
    assert "uid-b" in overlays
    assert overlays["uid-a"]["priority"] == 1
    assert overlays["uid-b"]["tags"] == []  # default filled in


async def test_reorder_sub_tasks(hass: HomeAssistant, overlay_store) -> None:
    """Sub-tasks can be reordered within the overlay."""
    s1 = await overlay_store.async_add_sub_task("uid-c", "First")
    s2 = await overlay_store.async_add_sub_task("uid-c", "Second")
    await overlay_store.async_reorder_sub_tasks("uid-c", [s2["id"], s1["id"]])
    overlay = overlay_store.get_overlay("uid-c")
    assert overlay["sub_items"][0]["id"] == s2["id"]
    assert overlay["sub_items"][1]["id"] == s1["id"]
