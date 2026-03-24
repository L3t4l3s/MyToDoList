# Home Tasks

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml/badge.svg)](https://github.com/L3t4l3s/home-tasks/actions/workflows/validate.yaml)

A feature-rich task management integration for [Home Assistant](https://www.home-assistant.io/) with a custom Lovelace card.

## Screenshots

<p align="center">
  <img src="docs/Household-collapsed.png" width="400" alt="Household list with badges">
  <img src="docs/Household-weekly.png" width="400" alt="Expanded task with sub-items, notes, and recurrence">
</p>
<p align="center">
  <img src="docs/Quick-notes-minimal.png" width="400" alt="Minimal card without title or extras">
  <img src="docs/Shopping-list.png" width="400" alt="Shopping list with auto-delete">
</p>
<p align="center">
  <img src="docs/Card-editor.png" width="600" alt="Card editor with all display options">
</p>

## Features

- **Drag & drop** reordering (desktop and mobile)
- **Sub-items** with progress tracking
- **Notes** per task
- **Due dates** with overdue highlighting
- **Recurring tasks** with flexible intervals (e.g. every 3 days, every 2 weeks)
- **Person assignment** using HA person entities
- **Filters**: All / Open / Done
- **Multiple lists** via integration config entries
- **Events** for automations (task created, completed, due, overdue, assigned, reopened)
- **Sensors**: Open task count and overdue binary sensor per list
- **Services**: Create, complete, and assign tasks via automations
- **Auto-delete** completed tasks (optional)
- **i18n**: Supports English and German, follows HA language setting
- Follows Home Assistant design language

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **three dots** menu (top right) and select **Custom repositories**
4. Add `https://github.com/L3t4l3s/home-tasks` with category **Integration**
5. Install **Home Tasks**
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/home_tasks` folder into your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Home Tasks**
3. Enter a name for your list
4. Repeat for additional lists

The Lovelace card is automatically registered — just add it to your dashboard.

### Card Configuration

All options are available in the visual card editor. You can also use YAML:

| Option | Default | Description |
|--------|---------|-------------|
| `list_id` | (required) | The list to display (selectable in the visual editor) |
| `title` | List name | Custom card title |
| `show_title` | `true` | Show/hide the card title |
| `show_progress` | `true` | Show/hide the task progress counter |
| `show_due_date` | `true` | Show/hide due date fields |
| `show_recurrence` | `true` | Show/hide recurrence settings |
| `show_sub_items` | `true` | Show/hide sub-items |
| `show_assigned_person` | `true` | Show/hide person assignment |
| `show_notes` | `true` | Show/hide the notes field |
| `auto_delete_completed` | `false` | Automatically delete completed tasks |

## Automations

### Events

| Event | Description |
|-------|-------------|
| `home_tasks_task_created` | Fired when a task is created |
| `home_tasks_task_completed` | Fired when a task is marked as done |
| `home_tasks_task_due` | Fired when a task's due date is today (once per day) |
| `home_tasks_task_overdue` | Fired when a task is past its due date (once per day) |
| `home_tasks_task_assigned` | Fired when a person is assigned to a task |
| `home_tasks_task_reopened` | Fired when a recurring task is automatically reopened |

All events include: `entry_id`, `task_id`, `task_title`, and (if set) `assigned_person` and `due_date`.

### Services

#### `home_tasks.add_task`

Create a new task via automation.

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID (alternative to `list_name`) |
| `title` | yes | Task title |
| `assigned_person` | no | Person entity ID (e.g. `person.ben`) |
| `due_date` | no | Due date (`YYYY-MM-DD`) |

*Either `list_name` or `entry_id` is required.*

#### `home_tasks.complete_task`

Mark a task as completed.

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID |
| `task_title` | ** | Title of the task |
| `task_id` | ** | UUID of the task |

*\* Either `list_name` or `entry_id`. \*\* Either `task_title` or `task_id`.*

#### `home_tasks.assign_task`

Assign a person to a task.

| Field | Required | Description |
|-------|----------|-------------|
| `list_name` | * | Name of the list |
| `entry_id` | * | Config entry ID |
| `task_title` | ** | Title of the task |
| `task_id` | ** | UUID of the task |
| `person` | yes | Person entity ID |

### Sensors

For each list, the integration creates:

- **Sensor** (`sensor.{list_name}_open_tasks`): Number of open tasks. Attributes: `open_task_titles`, `overdue_count`.
- **Binary Sensor** (`binary_sensor.{list_name}_overdue`): `on` if any task is past its due date.

### Example Automation

Send a notification when a task is due:

```yaml
automation:
  - alias: "Home Tasks: Notify on due task"
    trigger:
      - platform: event
        event_type: home_tasks_task_due
    action:
      - service: notify.mobile_app
        data:
          title: "Task due today"
          message: "{{ trigger.event.data.task_title }}"
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
