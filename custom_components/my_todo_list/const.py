"""Constants for the My ToDo List integration."""

DOMAIN = "my_todo_list"
STORAGE_KEY = "my_todo_list_data"
STORAGE_VERSION = 1
DEFAULT_LIST_NAME = "Meine Aufgaben"

# --- Security limits ---
MAX_LISTS = 50
MAX_TASKS_PER_LIST = 500
MAX_SUB_ITEMS_PER_TASK = 50
MAX_TITLE_LENGTH = 255
MAX_LIST_NAME_LENGTH = 100
MAX_NOTES_LENGTH = 5000
MAX_REORDER_IDS = 500
