# Testing the Home Tasks Integration

Tests use **[pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)** (pytest-hacc), which installs HA core as a Python package and provides real in-memory HA instances per test — no Docker, no running HA server needed.

---

## Prerequisites

- **Python 3.12** (exactly; HA 2025.1.x requires 3.12)
- The repo checked out at `D:\projects\Home_Tasks` (or any path — paths are derived at runtime)
- Internet access for initial venv setup

---

## First-time setup

```bash
# From the repo root
cd D:\projects\Home_Tasks

# Create a Python 3.12 venv (adjust path to your Python 3.12 installation)
PYTHONHOME="" PYTHONPATH="" \
  "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" \
  -m venv .venv

# Install test dependencies (HA core is pulled in automatically by pytest-hacc)
PYTHONHOME="" PYTHONPATH="" \
  .venv/Scripts/python.exe -m pip install --upgrade pip
PYTHONHOME="" PYTHONPATH="" \
  .venv/Scripts/python.exe -m pip install -r requirements_test.txt

# winloop is required on Windows so aiohttp's DNS resolver works with
# ProactorEventLoop (HA's event loop policy on Windows)
PYTHONHOME="" PYTHONPATH="" \
  .venv/Scripts/python.exe -m pip install winloop
```

> **Why `PYTHONHOME="" PYTHONPATH=""`?**
> A global Python 3.7 installation on this machine sets these env vars, which
> breaks venv activation. Clearing them is only needed on this specific machine.

---

## Running the tests

```bash
# Activate the venv first (optional — explicit path also works)
source .venv/Scripts/activate

# Run all tests
pytest

# Run a single file
pytest tests/test_store.py -v

# Run a single test
pytest tests/test_store.py::test_complete_task -v

# Without venv activation (explicit interpreter)
PYTHONHOME="" PYTHONPATH="" .venv/Scripts/python.exe -m pytest

# With coverage report
PYTHONHOME="" PYTHONPATH="" .venv/Scripts/python.exe -m pytest \
  --cov=custom_components/home_tasks --cov-report=term-missing
```

Expected output: **182 passed** (all green, no errors).

---

## Test file overview

| File | What it tests |
|------|--------------|
| `tests/test_store.py` | `HomeTasksStore` — add/update/delete tasks, all validation, migration, callbacks, history tracking, sub-tasks, recurrence, reorder, move between lists, listeners (52 tests) |
| `tests/test_overlay_store.py` | `ExternalTaskOverlayStore` — overlays for external tasks, all validation branches, sub-task CRUD, limits, overlay-not-found errors, persistence, listeners (29 tests) |
| `tests/test_config_flow.py` | Config flow — native list creation, duplicate detection, name_too_long, external abort/form/create (9 tests) |
| `tests/test_init.py` | Integration setup — services (add/complete/assign/reopen + tag/person filters), event firing, due/overdue events, recurrence timer, external entry lifecycle (19 tests) |
| `tests/test_websocket_api.py` | WebSocket commands — native CRUD, sub-task commands, move task, external overlay commands, error paths (26 tests) |
| `tests/test_todo.py` | `TodoListEntity` — HA todo platform, create/update/delete via services, due dates, descriptions, completed status, external entry skip (13 tests) |
| `tests/test_sensor.py` | `OpenTasksSensor` — open count, titles, overdue count with `@freeze_time` (5 tests) |
| `tests/test_binary_sensor.py` | `OverdueBinarySensor` — on/off with `@freeze_time`, overdue_tasks attribute (6 tests) |

---

## Adding new tests

1. Add a function to an existing file, or create a new `tests/test_<topic>.py`
2. Use the shared fixtures from `tests/conftest.py`:
   - `hass` — fresh HA instance (from pytest-hacc, autouse)
   - `mock_config_entry` — loads the integration and returns the config entry
   - `store` — returns the `HomeTasksStore` for the test entry
3. Use `@freeze_time("YYYY-MM-DD")` for tests that depend on `date.today()`
4. Use `async_fire_time_changed(hass, utcnow() + timedelta(...))` for timer callbacks

### Minimal example

```python
async def test_my_new_feature(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Test task")
    updated = await store.async_update_task(task["id"], priority=2)
    assert updated["priority"] == 2
```

### WebSocket test example

```python
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_ws_my_command(hass, hass_ws_client, mock_config_entry) -> None:
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "home_tasks/my_command", ...})
    result = await client.receive_json()
    assert result["success"] is True
```

---

## Fixture architecture

```
hass (pytest-hacc)
 └── auto_enable_custom_integrations  [autouse] — pops DATA_CUSTOM_COMPONENTS cache
      └── enable_custom_integrations  (pytest-hacc) — allows our integration to load

 └── patch_add_extra_js_url           [autouse] — prevents frontend KeyError

mock_config_entry(hass)
 └── loads the integration via hass.config_entries.async_setup()
 └── depends on patch_add_extra_js_url

store(hass, mock_config_entry)
 └── returns hass.data["home_tasks"][entry.entry_id]
```

---

## Windows-specific workarounds (already in conftest.py)

These are solved once and committed — no manual action needed:

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| `SocketBlockedError` on event loop creation | pytest-hacc blocks all sockets; asyncio needs `socketpair()` internally | Save real `socket.socket` before guarding; restore it during `socketpair()` calls |
| `ModuleNotFoundError: hass_frontend` | `frontend.async_setup` imports the compiled bundle (not in test venv) | Replace `frontend.async_setup` with a lightweight mock |
| `custom_components.__path__` points to testing_config | pytest-hacc's `_async_mount_config_dir` imports `custom_components` as a regular package from its own testing_config dir | Import `custom_components` at conftest module level (before any fixtures run) so the namespace package from our project root is cached first |
| `RuntimeError: aiodns needs SelectorEventLoop` | aiohttp's `AsyncResolver` uses `aiodns` which requires `SelectorEventLoop`; pytest-hacc forces `ProactorEventLoop` on Windows | Patch `aiohttp.connector.DefaultResolver = ThreadedResolver` at import time; also install `winloop` |
| Lingering IOCP accept tasks | Windows `ProactorEventLoop` accept coroutines don't cancel cleanly when HTTP server stops | Override `expected_lingering_tasks = True` for Windows in conftest |
| Lingering timers (`_schedule_startup_due_check`, `_async_register_due_checker`) | Timers weren't marked `cancel_on_shutdown=True` | Fixed in `__init__.py`: wrap in `HassJob(..., cancel_on_shutdown=True)` / pass `cancel_on_shutdown=True` to `async_track_time_interval` |

---

## Dependency notes

`requirements_test.txt` pins only the top-level test deps:

```
pytest-homeassistant-custom-component==0.13.205   # pulls homeassistant==2025.1.4
freezegun==1.5.1
```

`winloop` is installed separately (not in requirements_test.txt) because it is only needed on Windows and has no conflict risk.

Do **not** add `homeassistant` or `pytest-asyncio` or `pytest-cov` separately — they are pinned by pytest-hacc and adding them causes version conflicts.
