"""Live test configuration loaded from environment variables.

Live tests are opt-in and require credentials + dedicated test lists.
Each variable is optional; tests that need a variable are skipped if it's
missing.  Set them in your shell or in tests/live/.env (auto-loaded here).

See tests/live/.env.example for the full list and TESTING.md for setup.
"""
from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass


def _load_env_file() -> None:
    """Auto-load tests/live/.env into os.environ if present.

    Tiny dotenv parser — does not depend on python-dotenv.  Handles:
    - KEY=value
    - KEY="value with spaces"
    - blank lines and # comments
    Values already set in the real environment win.
    """
    env_path = pathlib.Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


@dataclass(frozen=True)
class LiveConfig:
    # WebSocket auth
    ha_url: str | None
    ha_token: str | None

    # Native list (E2E WebSocket tests)
    native_list_name: str | None
    native_list_name_secondary: str | None  # for move_task tests

    # External provider entity_ids
    todoist_entity: str | None
    google_tasks_entity: str | None
    caldav_entity: str | None
    local_todo_entity: str | None
    # Entity that's linked as an *external* list in home_tasks, so the
    # home_tasks/* adapter path can be exercised against Local Todo.
    # Distinct from local_todo_entity (which may be a home_tasks-native
    # list used for direct todo.* service tests).
    local_todo_external_entity: str | None
    bring_entity: str | None
    shopping_list_entity: str | None

    # Provider-side API credentials (for dual-view verification against the
    # real provider, bypassing HA's integration entity).  Extracted from the
    # HA config entries — see scripts/extract_provider_tokens.py if needed.
    todoist_api_token: str | None

    # Safety: maximum number of pre-existing items in a test list before
    # we abort with "you probably configured the wrong list" error.
    max_existing_items: int = 50


def load() -> LiveConfig:
    """Load live test config from environment variables (each optional)."""
    return LiveConfig(
        ha_url=os.environ.get("HT_HA_URL"),
        ha_token=os.environ.get("HT_HA_TOKEN"),
        native_list_name=os.environ.get("HT_NATIVE_LIST_NAME"),
        native_list_name_secondary=os.environ.get("HT_NATIVE_LIST_NAME_2"),
        todoist_entity=os.environ.get("HT_TODOIST_TEST_ENTITY"),
        google_tasks_entity=os.environ.get("HT_GOOGLE_TASKS_TEST_ENTITY"),
        caldav_entity=os.environ.get("HT_CALDAV_TEST_ENTITY"),
        local_todo_entity=os.environ.get("HT_LOCAL_TODO_TEST_ENTITY"),
        local_todo_external_entity=os.environ.get("HT_LOCAL_TODO_EXTERNAL_TEST_ENTITY"),
        bring_entity=os.environ.get("HT_BRING_TEST_ENTITY"),
        shopping_list_entity=os.environ.get("HT_SHOPPING_LIST_TEST_ENTITY"),
        todoist_api_token=os.environ.get("HT_TODOIST_API_TOKEN"),
        max_existing_items=int(os.environ.get("HT_MAX_EXISTING_ITEMS", "50")),
    )


# Singleton — read once per pytest session
CONFIG = load()
