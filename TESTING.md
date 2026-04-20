# Testing

## Test types

| Type | Directory | Marker | Requirements | Speed |
|---|---|---|---|---|
| **Unit** | `tests/unit/` | `unit` | Python only, no HA needed | ~1s |
| **Integration** | `tests/integration/` | `integration` | in-memory HA (pytest-hacc) | ~5s |
| **E2E** | `tests/e2e/` | `e2e` | in-memory HA + WebSocket | ~10s |
| **Live** | `tests/live/` | `live` | Real HA instance + credentials | ~60s |

**Unit**: Test individual classes/functions with mocks. No `hass` fixture needed.

**Integration**: Test the full integration lifecycle within an in-memory HA instance (config entry setup, service registration, platform loading). Uses `pytest-homeassistant-custom-component`.

**E2E**: Drive complete WebSocket command chains end-to-end — the same sequence a browser card would issue. Catches multi-command interaction bugs that unit tests miss (e.g. `reorder_external_tasks` → `get_external_tasks` order consistency).

**Live**: Run against a real HA instance. Require a `.env` file with credentials. Not run by default — opt-in with `-m live` or `-m live_google_tasks` etc.

---

## Setup

### Prerequisites
- Python 3.12 (tested with 3.12.2)
- Windows: no Docker required

### Create the virtual environment

```bash
# From D:\projects\Home_Tasks
# Clear any global PYTHONHOME/PYTHONPATH that might interfere (e.g. Python 3.7 globally)
PYTHONHOME="" PYTHONPATH="" \
  "C:/Users/schim/AppData/Local/Programs/Python/Python312/python.exe" \
  -m venv .venv

PYTHONHOME="" PYTHONPATH="" \
  .venv/Scripts/python.exe -m pip install --upgrade pip
PYTHONHOME="" PYTHONPATH="" \
  .venv/Scripts/python.exe -m pip install -r requirements_test.txt
```

On first run, this downloads and installs Home Assistant core (~500 MB). Subsequent runs use the cache.

---

## Running tests

### Activate the venv (optional convenience)
```bash
source .venv/Scripts/activate   # Git Bash / WSL
.venv\Scripts\activate          # Windows cmd
```

All commands below assume the venv is active, or prefix with `PYTHONHOME="" PYTHONPATH="" .venv/Scripts/python.exe -m`.

### Run all offline tests (default)
```bash
pytest
```
Runs unit + integration + e2e. Live tests are excluded by default (`-m "not live"` in `pytest.ini`).

### Run by type
```bash
pytest tests/unit/          # unit only   (~1s)
pytest tests/integration/   # integration only (~5s)
pytest tests/e2e/           # e2e only (~10s)
```

### Run by marker
```bash
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m "unit or integration"
```

### Run a single file or test
```bash
pytest tests/unit/test_store.py -v
pytest tests/integration/test_websocket_api.py::test_ws_add_task -v
pytest tests/e2e/test_flows.py::test_reorder_external_tasks_move_failure_falls_back_to_overlay_flow -v
```

### With coverage
```bash
pytest --cov=custom_components/home_tasks --cov-report=term-missing
pytest tests/e2e/ --cov=custom_components/home_tasks --cov-report=term-missing
```

---

## Live tests

Live tests require a real HA instance and credentials. They are excluded by default.

### Setup

1. Copy the template and fill in your credentials:
   ```bash
   cp tests/live/.env.example tests/live/.env
   ```
2. Edit `tests/live/.env`:
   ```env
   HT_HA_URL=http://192.168.1.x:8123
   HT_HA_TOKEN=eyJ...          # long-lived access token
   HT_NATIVE_LIST_NAME=Home-Tasks E2E Test
   HT_NATIVE_LIST_NAME_2=Home-Tasks E2E Test 2
   HT_TODOIST_TEST_ENTITY=todo.ht_test_todoist
   HT_GOOGLE_TASKS_TEST_ENTITY=todo.ht_test_google
   HT_CALDAV_TEST_ENTITY=todo.ht_test_nextcloud
   HT_LOCAL_TODO_TEST_ENTITY=todo.ht_test_local
   HT_BRING_TEST_ENTITY=todo.ht_test_bring
   HT_MAX_EXISTING_ITEMS=50
   ```
   `tests/live/.env` is gitignored — never commit credentials.

3. Create dedicated test lists/entities in your HA instance. The tests wipe these lists on each run. **Do not point them at real data.**

### Run live tests
```bash
# All live tests (all configured providers)
pytest tests/live/ -m live -v

# Specific provider
pytest tests/live/ -m live_google_tasks -v
pytest tests/live/ -m live_todoist -v
pytest tests/live/ -m live_caldav -v
pytest tests/live/ -m live_local_todo -v
pytest tests/live/ -m live_bring -v
pytest tests/live/ -m live_websocket -v

# Native list E2E (create/update/move/complete flows)
pytest tests/live/test_e2e_websocket.py -m live -v
```

Missing env vars are auto-skipped — a partial setup (e.g. only Todoist configured) will skip unconfigured providers cleanly.

---

## Adding new tests

### Where to put them
- **New business logic / data model** → `tests/unit/`
- **New HA platform or service** → `tests/integration/`
- **New multi-command flow or cross-component interaction** → `tests/e2e/`
- **New provider or real-API behavior** → `tests/live/`

### Marking
Each file must have a module-level `pytestmark`:
```python
pytestmark = pytest.mark.unit        # or integration / e2e
```
Live tests use:
```python
pytestmark = [pytest.mark.live, pytest.mark.live_google_tasks]
```

### E2E test pattern
Use the `_cmd` / `_cmd_fail` helpers from `tests/e2e/test_flows.py` to issue WebSocket commands and assert responses. Always test the full cycle: command → subsequent read → assert state reflects the change.

---

## CI / CD notes

Only unit, integration, and e2e tests are suitable for CI. Live tests require external services and should be run manually before releases.

Suggested CI command:
```bash
PYTHONHOME="" PYTHONPATH="" .venv/Scripts/python.exe -m pytest \
  tests/unit/ tests/integration/ tests/e2e/ \
  --tb=short -q
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
