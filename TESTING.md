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

---

# Live tests (opt-in)

Beyond the in-memory unit tests, this repo has a **live test suite** under
`tests/live/` that runs against a real Home Assistant instance and real
provider APIs (Todoist, Google Tasks, CalDAV, Local Todo, Bring).

Live tests catch a class of bugs that mocks fundamentally cannot:

- Provider API contract drift (e.g. Todoist changing recurrence string format)
- Reminder / sub-task / recurrence sync edge cases against real backends
- WebSocket schema mismatches between the card and the integration
- Real-world timing and eventual-consistency issues

They are **opt-in** — `pytest` (default) does not collect them.  Run with:

```bash
pytest -m live
```

## Setup (one-time)

1. **Long-lived access token**
   - HA → Profile → Security → "Create Token" at the bottom
   - Copy the token (you only see it once)

2. **Native test lists** (via Settings → Devices & Services → Home Tasks)
   - Create one named **`Home-Tasks E2E Test`** (required for E2E tests)
   - Create another named **`Home-Tasks E2E Test 2`** (required for move_task tests)

3. **Per-provider test lists** — pick the providers you want to test.
   For each, create a NEW empty list/project in the provider's UI:
   - **Todoist**: new project named e.g. `ht-test`
   - **Google Tasks**: new task list named e.g. `ht-test`
   - **CalDAV**: new collection named e.g. `ht-test`
   - **Local Todo**: HA → Settings → Devices → Local Todo → new list `ht-test`
   - **Bring**: new shopping list named e.g. `ht-test`

   Then **link each one** through Home Tasks → Add list → Choose external,
   selecting the new entity.  Note the resulting `todo.<entity_id>` under
   Settings → Devices & Services → Entities.

4. **Create `tests/live/.env`** by copying `.env.example`:

   ```bash
   cp tests/live/.env.example tests/live/.env
   # Then edit tests/live/.env with your token and entity IDs
   ```

   Each variable is optional — tests for unset providers are auto-skipped.

## Running

```bash
# All live tests (skips any provider whose env var is missing)
pytest -m live

# Just the WebSocket E2E tests
pytest -m live tests/live/test_e2e_websocket.py

# Just one provider
pytest -m live tests/live/test_provider_todoist.py

# Verbose
pytest -m live -v
```

### Running from the Claude Code HA add-on container

The add-on container's AppArmor profile blocks `.so` loading from `/share`,
which prevents `pytest-homeassistant-custom-component` (and its transitive
dependency `bcrypt`) from initialising.  Since live tests only need network
access (no mock HA), disable the plugin and skip the root conftest:

```bash
cd /share/home-tasks
.venv/bin/python -m pytest tests/live/ \
  -p no:homeassistant \
  -p no:pytest_homeassistant_custom_component \
  --confcutdir=tests/live \
  -m live -v
```

**Important:** In `tests/live/.env`, set `HT_HA_URL` to the IP of the
**test** HA instance (e.g. `http://192.168.178.193:8123`), not `localhost`
or `http://supervisor/core` (which points to the production instance running
the add-on).

## Safety

Each test list is **wiped before every test** (the autouse fixture deletes
all items).  A safety guard aborts the wipe if a list contains more than
`HT_MAX_EXISTING_ITEMS` (default 50) items, so accidentally pointing tests
at a real list cannot destroy data.  Verify after a test run:

- The dedicated test list in each provider's UI should be empty (or contain
  only items left over from a failing test)
- All other lists must be unchanged

## What's covered

| File | Tests | What it exercises |
|------|------:|--------------------|
| `test_e2e_websocket.py` | 14 | Full WS API: lists, CRUD, sub-tasks, reorder, move, reminders, recurrence config |
| `test_e2e_cross_move.py` | 5 | `move_task_cross` native ↔ each provider |
| `test_provider_todoist.py` | 11+1xfail | Rich adapter: CRUD, sub-tasks, recurrence round-trip, reminders, reorder |
| `test_provider_google_tasks.py` | 7 | Generic adapter: CRUD + overlay routing |
| `test_provider_caldav.py` | 7 | Generic adapter: CRUD + overlay routing |
| `test_provider_local_todo.py` | 7 | Direct todo.* services (Local Todo not linked through home_tasks) |
| `test_provider_bring.py` | 5 | Shopping-list provider: CRUD + overlay-everything |
| **Total** | **56 + 1 xfail** | |

---

# JavaScript card tests

The Lovelace card (`custom_components/home_tasks/home-tasks-card.js`) is a
~4600 line vanilla custom element with extensive DOM manipulation. It is
tested with **Node's built-in `node:test` runner + jsdom**, no bundler or
browser required.

## Setup

Requires Node.js 20+ (uses `node:test --experimental-test-coverage`).

```bash
# From the repo root
npm install
```

This installs only `jsdom` as a dev dependency. No esbuild, no Vitest, no
Playwright — keeping the toolchain minimal so it runs in any sandboxed
environment (the addon container, GitHub Actions, etc.).

## Running

```bash
# Run all JS tests with coverage
npm test

# Run without coverage (faster)
npm run test:nocov

# Run a single test file
node --test tests-js/test_card_helpers.mjs
```

## Architecture

`tests-js/setup.mjs` builds a fresh jsdom realm, installs the necessary
browser globals (`window`, `document`, `customElements`, `HTMLElement`,
etc.), and loads `home-tasks-card.js` into that realm via
`new dom.window.Function(src)`. The result is a fully usable
`HomeTasksCard` class that can be instantiated, configured with a mock
`hass`, and rendered into a shadow DOM that tests can query.

For tests that depend on dates ("today", "tomorrow", date arithmetic),
`loadCard({ frozenNow: '2027-06-15T12:00:00Z' })` replaces the realm's
`window.Date` with a stub that returns the fixed moment.

## Test files

| File | Tests | What it exercises |
|------|------:|--------------------|
| `test_card_loads.mjs` | 2 | Smoke: card source loads, custom element registers |
| `test_card_helpers.mjs` | 25 | Pure helpers: `_isDueDateOverdue`, `_isDueDateToday`, `_getSubTaskProgress`, `_buildSortComparator` (manual/priority/title/due/person), `_formatDueDate` (today/tomorrow/yesterday/+2/-2/far) |
| `test_card_render.mjs` | 14 | Full lifecycle (`setConfig` → `set hass` → `_loadLists` → render), task list rendering, optimistic updates (notes/title/sub-task delete), `_render` background-update guard (editing, dragging), `_filteredTasks` integration, column-type helpers |
| **Total** | **41** | |

## Mocking pattern for render tests

Tests that need a populated card use `makeRecordingHass()` from
`test_card_render.mjs`:

```javascript
const hass = makeRecordingHass({
  'home_tasks/get_lists': { lists: [{ id: 'L1', name: 'Test' }] },
  'home_tasks/get_tasks': {
    tasks: [{ id: 'T1', title: 'Task A', sort_order: 0, sub_items: [] }],
  },
});
const card = new HomeTasksCard();
card.setConfig({ columns: [{ list_id: 'L1' }] });
card.hass = hass;
await flush(card);  // wait for async _loadLists to complete

// Now assert against card.shadowRoot or card._columns[i].tasks
```

The mock returns canned responses per WS command type and records every
call in `hass.calls` for verification.

## Coverage

`node:test --experimental-test-coverage` reports coverage of the test
files themselves, not of `home-tasks-card.js` (which is loaded as a
runtime-synthesized function rather than from disk, so V8 cannot track
it). Functional coverage is measured by what behaviors we assert.

## Known findings (live-test discoveries)

All Live-Test findings have been fixed and are now regression-tested.

- **Todoist reminder sync data loss on Free accounts** (fixed in 9db4096):
  Free Todoist users cannot create reminders with non-zero offsets
  (`PREMIUM_ONLY`). The old `_sync_reminders` deleted existing reminders
  before attempting adds, so any reminder edit silently destroyed the
  implicit "at due time" reminder that Todoist auto-creates for tasks
  with due_datetime. Now `_sync_reminders` adds first, aborts on
  `PREMIUM_ONLY`, and rolls back any partial creates.

