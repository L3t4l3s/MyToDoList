"""Constants for the Home Tasks integration."""

DOMAIN = "home_tasks"
STORAGE_VERSION = 1

# --- Security limits ---
MAX_LISTS = 50
MAX_TASKS_PER_LIST = 500
MAX_SUB_ITEMS_PER_TASK = 50
MAX_TITLE_LENGTH = 255
MAX_LIST_NAME_LENGTH = 100
MAX_NOTES_LENGTH = 5000
MAX_REORDER_IDS = 500
MAX_TAGS_PER_TASK = 20
MAX_TAG_LENGTH = 50

# --- Recurrence ---
VALID_RECURRENCE_UNITS = ("hours", "days", "weeks", "months")
RECURRENCE_UNIT_SECONDS = {
    "hours": 3600,
    "days": 86400,
    "weeks": 604800,
    "months": 2592000,  # 30 days
}
MAX_RECURRENCE_VALUE = 365

# --- Reminders ---
MAX_REMINDERS_PER_TASK = 5
MAX_REMINDER_OFFSET_MINUTES = 43200  # 30 days
