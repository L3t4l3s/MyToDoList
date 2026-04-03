# Home Tasks

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml/badge.svg)](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml)

A feature-rich, highly customizable task management solution for Home Assistant — combining a native **integration** (sensors, events, services) with a versatile Lovelace **dashboard card**. Supports linking **external todo lists** from CalDAV, Google Tasks, Todoist, and other providers.

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
- Base fields (title, status, due date, description) are **synced** to the external provider via HA's standard todo services
- Home Tasks extra fields (priority, tags, sub-tasks, etc.) are stored **locally** in an overlay — they work in HA but are not synced to the provider
- The card editor **auto-configures visibility** based on the provider's capabilities when you select an external list
- You can manually enable overlay fields (e.g. priority, tags) for external lists if you want them locally

#### Verified Providers

| Provider | HA Integration | Due Date | Due Time | Description | Reorder | Notes |
|----------|---------------|----------|----------|-------------|---------|-------|
| **CalDAV** (Nextcloud, etc.) | [CalDAV](https://www.home-assistant.io/integrations/caldav/) (Core) | yes | yes | yes | no | |
| **Google Tasks** | [Google Tasks](https://www.home-assistant.io/integrations/google_tasks/) (Core) | yes | no | yes | yes | API does not support due times or recurrence |
| **Todoist** | [Todoist](https://www.home-assistant.io/integrations/todoist/) (Core) | yes | yes | yes | no | |
| **Microsoft ToDo** | [MS365-ToDo](https://github.com/RogerSelwyn/MS365-ToDo) (HACS) | yes | yes | yes | no | Custom integration, not HA Core |

Any other integration that creates `todo.*` entities following HA's standard `TodoListEntity` should also work. The extra fields (priority, tags, sub-tasks, assigned person, reminders, recurrence) are always available via the local overlay, regardless of what the provider supports.

### Dashboard Card

- **Multi-column layout** — display multiple lists side-by-side on a single card
- **Per-column configuration** — title, icon, default filter, default sort, show/hide every field individually
- **Drag & drop** reordering on desktop and mobile
- **Cross-list drag & drop** — move tasks between columns (multi-column cards only)
- **Click anywhere** to expand / collapse task details
- **Double-click title** to rename inline
- **Filter** per column — All / Open / Done
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
- **Multiple lists** via separate integration config entries

### Languages

Available in 15 languages — follows your HA language setting automatically:

English · German · French · Spanish · Portuguese · Italian · Dutch · Polish · Swedish · Danish · Norwegian · Finnish · Czech · Russian · Hungarian

---

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **three dots** menu (top right) → **Custom repositories**
4. Add `https://github.com/L3t4l3s/home-tasks` with category **Integration**
5. Install **Home Tasks**
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/home_tasks` folder into your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

### Native Lists

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Home Tasks**
3. Choose **Create a new task list**
4. Enter a name for your list
5. Repeat for additional lists

### External Lists

1. Set up the external provider's HA integration first (e.g. CalDAV, Google Tasks, Todoist)
2. Go to **Settings** → **Devices & Services** → **Add Integration**
3. Search for **Home Tasks**
4. Choose **Link an external todo list**
5. Select the todo entity from the dropdown
6. The external list is now available in the card editor

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
| `default_filter` | `all` | Initial filter: `all`, `open`, or `done` |
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

### Sensors

For each list, the integration creates:

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
