# Home Tasks

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Validate](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml/badge.svg)](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml)

A feature-rich, highly customizable task management solution for Home Assistant — combining a native **integration** (sensors, calendar, events, services) with a versatile Lovelace **dashboard card**. Supports linking **external todo lists** from CalDAV, Google Tasks, Todoist, Bring, Local Todo, and other providers.

<p align="center">
  <img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/header-light.png" width="400" alt="Home Tasks in light mode">
  <img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/header-dark.png" width="400" alt="Home Tasks in dark mode">
</p>

## Features

### Per-Task Fields

Every task can carry up to 20 individual attributes:

- **Title** — inline rename with double-click
- **Notes** — free-text field per task
- **Due date** with overdue highlighting
- **Due time**
- **Priority** — Low / Medium / High with colored badges
- **Assigned person** — any HA person entity
- **Tags** — multiple tags for categorization
- **Sub-tasks** — nested checklist with progress bar
- **Reminders** — up to 5 per task, fire as HA events at a configurable offset before due time
- **Recurring** — fixed intervals: hours, days, weeks, months
- **Recurring** — specific weekdays (Mon – Sun, any combination)
- **Recurrence start date**
- **Recurrence end date**
- **Maximum repetitions**
- **Completion state** with timestamp
- **Task history / audit log** — every field change recorded with actor and timestamp

### External Todo Lists

Display tasks from **any HA todo integration** alongside native Home Tasks lists — on the same card, in the same UI.

- Link external todo entities via **Settings > Integrations > Home Tasks > Link external todo list**
- Provider type is **auto-detected** (Todoist, CalDAV, Google Tasks, etc.) — no extra configuration needed
- For **generic providers** (CalDAV, Google Tasks, etc.): base fields (title, status, due date/time, description) are synced bidirectionally via HA's standard todo entity interface. Extra fields (priority, tags, sub-tasks, etc.) are stored locally in an overlay.
- For **Todoist**: full bidirectional sync via direct API access — see [Todoist Deep Integration](#todoist-deep-integration) below
- The card editor **auto-configures visibility** based on the provider's capabilities when you select an external list
- You can manually enable overlay fields for external lists if you want them locally

#### Verified Providers

| Provider | HA Integration | Due Date | Due Time | Description | Reorder | Priority | Labels | Sub-tasks | Assignee | Recurrence | Reminders | Notes |
|----------|---------------|----------|----------|-------------|---------|----------|--------|-----------|----------|------------|-----------|-------|
| **CalDAV** (Nextcloud, etc.) | [CalDAV](https://www.home-assistant.io/integrations/caldav/) (Core) | yes | yes | yes | no | no | no | no | no | no | no | |
| **Google Tasks** | [Google Tasks](https://www.home-assistant.io/integrations/google_tasks/) (Core) | yes | no | yes | yes | no | no | no | no | no | no | Google's API does not expose due times or recurrence ([open issue](https://issuetracker.google.com/issues/36759725)) |
| **Todoist** | [Todoist](https://www.home-assistant.io/integrations/todoist/) (Core) | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | Full bidirectional sync via direct Todoist API |
| **Local Todo** | [Local Todo](https://www.home-assistant.io/integrations/local_todo/) (Core) | yes | no | yes | no | no | no | no | no | no | no | Simple file-based lists built into HA |
| **Bring** | [Bring](https://www.home-assistant.io/integrations/bring/) (Core) | no | no | no | no | no | no | no | no | no | no | Shopping list provider — all extra fields via overlay |

Any other integration that creates `todo.*` entities following HA's standard `TodoListEntity` should also work. Fields marked "no" are available locally in Home Tasks but not synced to the provider.

Tasks can be **moved between native and external lists** via drag & drop on multi-column cards. Fields that the target provider cannot sync are preserved in the local overlay.

#### Todoist Deep Integration

When you link a Todoist list, Home Tasks automatically detects the Todoist provider and uses the **Todoist REST API directly** (via the existing Todoist integration's API token — no extra configuration required). This enables full bidirectional sync for nearly all fields including title, status, description, due date/time, priority, labels/tags, sort order, sub-tasks, assigned person, recurrence, and reminders.

Home Tasks uses its **own lightweight REST API client** (no dependency on `todoist-api-python`) to communicate directly with the Todoist API. The only requirement is the existing HA Todoist integration being configured — the API token is read from its config entry automatically.

**Unsupported Todoist features** (not synchronized):

- **Comments** — Todoist has a threaded comment system with timestamps and multiple authors; Home Tasks uses a single notes/description field
- **Attachments** — file attachments on tasks or comments
- **Sections** — task grouping within Todoist projects
- **Task duration** — how long a task takes (e.g. 30 minutes)
- **Label colors** — Todoist labels have their own colors and ordering
- **Deadline vs. due date** — Todoist separates planned work date (due) from deadline
- **Favorites** — marking tasks or projects as favorites
- **Saved filters** — Todoist's own filter query language

### Dashboard Card

- **Multi-column layout** — display multiple lists side-by-side on a single card
- **Per-column configuration** — title, icon, default filter, default sort, show/hide every field individually
- **Drag & drop** reordering on desktop and mobile
- **Cross-list drag & drop** — move tasks between columns (multi-column cards only)
- **Click anywhere** to expand / collapse task details
- **Double-click title** to rename inline
- **Filter** per column — All / Open / Done, plus optional **Due Soon** filter (shows tasks due within a configurable number of days)
- **Sort** per column — manual, due date, priority, title, assigned person
- **Tag & person filter chips** in the column header
- **Compact mode** for denser task rows
- **Auto-delete** completed tasks (optional, per column)
- **Smooth animations** — FLIP transitions for sort, filter, create, delete, complete, and reopen
- **Visual card editor** — fully configurable without writing YAML

### Home Assistant Integration

- **7 automation events**: created, completed, reopened, due, overdue, assigned, reminder
- **Services**: add, complete, reopen, and assign tasks from automations
- **Sensors**: open task count + overdue binary sensor per list
- **Calendar**: each native list gets a `calendar.*` entity — tasks with due dates appear as all-day or timed events, usable in any HA calendar card or automation
- **Todo entity**: each native list is exposed as a standard `todo.*` entity with full HA todo platform support (Companion App, Apple Watch, etc.)
- **Multiple lists** via separate integration config entries

### Languages

Available in 15 languages — follows your HA language setting automatically:

English · German · French · Spanish · Portuguese · Italian · Dutch · Polish · Swedish · Danish · Norwegian · Finnish · Czech · Russian · Hungarian

---

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the **three dots** menu (top right) → **Custom repositories**
3. Paste `https://github.com/L3t4l3s/home-tasks` and select category **Integration**
4. Click **Add**
5. Search for **Home Tasks** in HACS Integrations and click **Download**
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/home_tasks` folder into your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

### Native Lists

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Home Tasks**
3. Click **Add Device**
4. Choose **Create a new task list**
5. Enter a name for your list
6. Repeat for additional lists

### External Lists

1. Set up the external provider's HA integration first (e.g. CalDAV, Google Tasks, Todoist)
2. Go to **Settings** → **Devices & Services** → **Add Integration**
3. Search for **Home Tasks**
4. Click **Add Device**
5. Choose **Link an external todo list**
6. Select the todo entity from the dropdown
7. The external list is now available in the card editor

The Lovelace card is automatically registered — just add it to your dashboard.

---

## Card Configuration

All options are available in the visual card editor. The examples below cover the most common setups.

### Column option reference

| Option | Default | Description |
|--------|---------|-------------|
| `list_id` | — | The native list to display (use this **or** `entity_id`) |
| `entity_id` | — | An external todo entity to display (use this **or** `list_id`) |
| `title` | List name | Custom column title |
| `icon` | — | MDI icon shown next to the column title (e.g. `mdi:home`) |
| `default_filter` | `all` | Initial filter: `all`, `open`, `done`, or `due_soon` |
| `default_sort` | `manual` | Initial sort: `manual`, `due`, `priority`, `title`, or `person` |
| `show_title` | `true` | Show/hide the column title |
| `show_progress` | `true` | Show/hide the task progress counter |
| `show_sort` | `true` | Show/hide the sort button |
| `show_notes` | `true` | Show/hide the notes field |
| `show_sub_tasks` | `true` | Show/hide sub-tasks |
| `show_assigned_person` | `true` | Show/hide person assignment |
| `show_priority` | `true` | Show/hide priority field and badge |
| `show_tags` | `true` | Show/hide tags, badges, and filter chips |
| `show_due_date` | `true` | Show/hide due date and time |
| `show_reminders` | `true` | Show/hide reminders |
| `show_recurrence` | `true` | Show/hide recurrence settings |
| `compact` | `false` | Compact mode for denser task rows |
| `auto_delete_completed` | `false` | Automatically delete completed tasks |
| `show_history` | `false` | Show/hide the task change history |
| `show_due_soon_filter` | `false` | Enable the "Due Soon" filter button |
| `due_soon_days` | `7` | Number of days ahead for the "Due Soon" filter (1–90) |

The old flat format (`list_id` at root level) is still supported and migrated automatically.

---

### Use Cases

<table>
<tr>
<td width="50%" valign="top">

#### 🏠 Household

<img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/Household-full.png" alt="Household list">

Full-featured list for shared household tasks — priorities, due dates, person assignment, and recurrence keep everything organized. Default filter `open` keeps the view focused.

```yaml
type: custom:home-tasks-card
columns:
  - list_id: "your-list-id"
    default_filter: open
```

</td>
<td width="50%" valign="top">

#### 🛒 Shopping List

<img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/Shopping-list.png" alt="Shopping list">

Minimal and fast — just items and checkboxes. Completed entries disappear immediately. All metadata fields hidden to reduce clutter.

```yaml
type: custom:home-tasks-card
columns:
  - list_id: "your-list-id"
    auto_delete_completed: true
    show_notes: false
    show_sub_tasks: false
    show_assigned_person: false
    show_priority: false
    show_tags: false
    show_due_date: false
    show_reminders: false
    show_recurrence: false
    show_sort: false
```

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### 💼 Work / Projects

<img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/usecase-work.png" alt="Work and projects list">

Focused on deadlines — priorities, due dates, reminders, and sub-tasks. Person assignment and recurrence hidden to reduce noise.

```yaml
type: custom:home-tasks-card
columns:
  - list_id: "your-list-id"
    default_filter: open
    default_sort: due
    show_assigned_person: false
    show_tags: false
    show_recurrence: false
```

</td>
<td width="50%" valign="top">

#### 🎒 Kids Chores

<img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/usecase-chores.png" alt="Kids chores list">

Who does what and when — person assignment, weekday recurrence, and tags for time-of-day filtering. No deadlines, notes, or sub-tasks needed.

```yaml
type: custom:home-tasks-card
columns:
  - list_id: "your-list-id"
    title: Kids Chores
    icon: mdi:school
    show_priority: false
    show_due_date: false
    show_reminders: false
    show_notes: false
    show_sub_tasks: false
```

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### External: Nextcloud CalDAV

Display a Nextcloud todo list in the Home Tasks card. The external provider handles title, status, due date, and description. Local overlay adds priority and tags.

```yaml
type: custom:home-tasks-card
columns:
  - entity_id: "todo.nextcloud_tasks"
    title: Nextcloud Tasks
    icon: mdi:cloud-sync
    show_priority: true
    show_tags: true
    show_sub_tasks: false
    show_assigned_person: false
    show_reminders: false
    show_recurrence: false
```

</td>
<td width="50%" valign="top">

#### Mixed: Native + External

Combine a native Home Tasks list with a synced Google Tasks list on the same card. Each column is independently configured.

```yaml
type: custom:home-tasks-card
columns:
  - list_id: "your-native-list-id"
    title: Home
    icon: mdi:home
  - entity_id: "todo.google_tasks_my_tasks"
    title: Google
    icon: mdi:google
```

</td>
</tr>
</table>

---

### Multi-Column Example: Kanban Board

<p align="center">
  <img src="https://raw.githubusercontent.com/L3t4l3s/home-tasks/main/docs/Multi-column-kanban.png" width="820" alt="Multi-column Kanban board">
</p>

Multiple lists displayed side-by-side on a single card. Tasks can be dragged between columns. Extend `grid_options` to give the card more horizontal space.

```yaml
type: custom:home-tasks-card
title: Kanban Board
columns:
  - list_id: "your-list-id1"
    auto_delete_completed: true
    show_recurrence: false
  - list_id: "your-list-id2"
    show_recurrence: false
  - list_id: "your-list-id3"
    show_recurrence: false
grid_options:
  columns: 36
  rows: auto
```

---

## Automations

### Events

| Event | Description |
|-------|-------------|
| `home_tasks_task_created` | Fired when a task is created |
| `home_tasks_task_completed` | Fired when a task is marked as done |
| `home_tasks_task_due` | Fired when a task's due date is today (once per day) |
| `home_tasks_task_overdue` | Fired when a task is past its due date (once per day) |
| `home_tasks_task_assigned` | Fired when a person is assigned to a task |
| `home_tasks_task_reopened` | Fired when a task is reopened (manually or by recurrence) |
| `home_tasks_task_reminder` | Fired at the configured offset before a task's due time |

All events include: `entry_id`, `task_id`, `task_title`, and (if set) `assigned_person`, `due_date`, `tags`.
Events for external lists additionally include `entity_id` (the external todo entity).
The `home_tasks_task_reminder` event additionally includes `reminder_offset_minutes`.

### Services

#### `home_tasks.add_task`

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID (alternative to `list_name`) |
| `title` | yes | Task title |
| `assigned_person` | no | Person entity ID (e.g. `person.ben`) |
| `due_date` | no | Due date (`YYYY-MM-DD`) |
| `tags` | no | Comma-separated tags (e.g. `"kitchen,daily"`) |

#### `home_tasks.complete_task`

Provide `task_title`/`task_id` for a single task, or `tag` to complete all open tasks with that tag.

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID |
| `task_title` | ** | Title of the task |
| `task_id` | ** | UUID of the task |
| `tag` | ** | Complete all open tasks with this tag |

#### `home_tasks.reopen_task`

Target by single task, person, tag, or a combination.

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID |
| `task_title` | ** | Title of the task |
| `task_id` | ** | UUID of the task |
| `assigned_person` | ** | Reopen all completed tasks for this person |
| `tag` | ** | Reopen all completed tasks with this tag |

#### `home_tasks.assign_task`

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID |
| `task_title` | ** | Title of the task |
| `task_id` | ** | UUID of the task |
| `person` | yes | Person entity ID |

*\* Either `list_name` or `entry_id`. \*\* See individual service descriptions for required combinations.*

### Entities

For each native list, the integration creates:

- **Todo** (`todo.{list_name}`): Standard HA todo entity — works with the Companion App, Apple Watch, Google Home, and any HA automation that targets `todo.*` entities.
- **Calendar** (`calendar.{list_name}_calendar`): Tasks with a due date appear as calendar events. Tasks with only a due date show as all-day events; tasks with both due date and due time show as 1-hour timed events with a rich description (notes, priority, assignee, tags, sub-task progress, reminders).
- **Sensor** (`sensor.{list_name}_open_tasks`): Number of open tasks. Attributes: `open_task_titles`, `overdue_count`.
- **Binary Sensor** (`binary_sensor.{list_name}_overdue`): `on` if any task is past its due date.

### Example Automations

Send a notification when a reminder fires:

```yaml
automation:
  - alias: "Home Tasks: Reminder notification"
    trigger:
      - platform: event
        event_type: home_tasks_task_reminder
    action:
      - service: notify.mobile_app
        data:
          title: "Task reminder"
          message: "{{ trigger.event.data.task_title }} is due soon"
```

Reopen morning chores when a child arrives home:

```yaml
automation:
  - alias: "Reopen morning tasks for Ben"
    trigger:
      - platform: state
        entity_id: person.ben
        to: "home"
    action:
      - service: home_tasks.reopen_task
        data:
          list_name: "Kids Chores"
          assigned_person: person.ben
          tag: "morning"
```

Complete all weekend tasks on Monday morning:

```yaml
automation:
  - alias: "Complete weekend tasks"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: time
        weekday: [mon]
    action:
      - service: home_tasks.complete_task
        data:
          list_name: "Household"
          tag: "weekend"
```

## Support

If Home Tasks is useful to you, consider supporting the project — it keeps the motivation going and helps fund future development. 🙏

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-%23EA4AAA?logo=github)](https://github.com/sponsors/L3t4l3s)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-%23FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/l3t4l3s)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-%2300457C?logo=paypal&logoColor=white)](https://paypal.me/kevinschimnick)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
