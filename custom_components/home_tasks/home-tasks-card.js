/**
 * Home Tasks Card for Home Assistant
 * A feature-rich todo list with drag & drop, sub-items, notes, and due dates.
 *
 * Security: All user-controlled content is set via textContent or DOM properties,
 * never via innerHTML with unsanitized data.
 */
console.info("%c HOME-TASKS-CARD %c v1.1.0 ", "color: white; background: #03a9f4; font-weight: bold;", "color: #03a9f4; background: white; font-weight: bold;");

const _TRANSLATIONS = {
  en: {
    my_tasks: "My Tasks",
    add_placeholder: "Add new task...",
    filter_all: "All",
    filter_open: "Open",
    filter_done: "Done",
    progress: "{0} of {1} done",
    empty: "No tasks",
    drag_handle: "Drag to reorder",
    due_date: "Due",
    notes: "Notes",
    notes_placeholder: "Add notes here",
    sub_items: "Sub-items",
    add_sub_item: "+ Add sub-item",
    recurrence: "Recurrence",
    recurrence_enabled: "Enabled",
    recurrence_every: "Every",
    rec_hours: "Hours", rec_days: "Days", rec_weeks: "Weeks", rec_months: "Months",
    rec_short_h: "h", rec_short_d: "d", rec_short_w: "w", rec_short_m: "mo",
    priority: "Priority",
    pri_high: "High", pri_medium: "Medium", pri_low: "Low",
    ed_show_priority: "Show priority",
    rec_hourly: "Hourly", rec_daily: "Daily", rec_weekly: "Weekly", rec_monthly: "Monthly",
    rec_type_interval: "Every \u2026", rec_type_weekdays: "On weekdays",
    rec_wd_0: "Mon", rec_wd_1: "Tue", rec_wd_2: "Wed", rec_wd_3: "Thu", rec_wd_4: "Fri", rec_wd_5: "Sat", rec_wd_6: "Sun",
    assigned_to: "Assigned to",
    nobody: "\u2013 Nobody \u2013",
    delete_task: "Delete task",
    delete_sub: "Delete",
    ed_default_filter: "Default filter",
    ed_list: "List",
    ed_title: "Title (optional)",
    ed_title_placeholder: "Default: List name",
    ed_display: "Display",
    ed_show_title: "Show title",
    ed_show_progress: "Show progress",
    ed_show_due_date: "Show due",
    ed_show_notes: "Show notes",
    ed_show_recurrence: "Show recurrence",
    ed_show_sub_items: "Show sub-items",
    ed_show_person: "Show assigned person",
    ed_auto_delete: "Delete completed tasks immediately",
    ed_compact: "Compact mode",
    ed_show_tags: "Show tags",
    ed_hint: "New lists can be created under Settings \u2192 Integrations \u2192 Home Tasks.",
    tags: "Tags",
    add_tag: "+ Add tag",
    tag_placeholder: "New tag...",
    remove_tag: "Remove",
    sort_label: "Sort",
    sort_manual: "Manual",
    sort_due: "Due date",
    sort_priority: "Priority",
    sort_title: "Title (A\u2013Z)",
    sort_person: "Assigned",
    ed_show_sort: "Show sort button",
    ed_default_sort: "Default sort",
    reminder: "Reminders",
    rem_add: "+ Add reminder",
    rem_none: "No reminder",
    rem_at_due: "At due time",
    rem_5m: "5 min before",
    rem_15m: "15 min before",
    rem_30m: "30 min before",
    rem_1h: "1 hour before",
    rem_2h: "2 hours before",
    rem_1d: "1 day before",
    rem_2d: "2 days before",
    ed_show_reminders: "Show reminders",
    ed_add_column: "Add column",
    ed_move_left: "Move left",
    ed_move_right: "Move right",
    ed_duplicate: "Duplicate column",
    ed_delete_column: "Delete column",
    ed_code_editor: "Code editor",
    ed_visual_editor: "Visual editor",
  },
  de: {
    my_tasks: "Meine Aufgaben",
    add_placeholder: "Neue Aufgabe hinzuf\u00fcgen...",
    filter_all: "Alle",
    filter_open: "Offen",
    filter_done: "Erledigt",
    progress: "{0} von {1} erledigt",
    empty: "Keine Aufgaben vorhanden",
    drag_handle: "Verschieben",
    due_date: "F\u00e4lligkeit",
    notes: "Notizen",
    notes_placeholder: "Hier kannst du Notizen hinzuf\u00fcgen",
    sub_items: "Unterpunkte",
    add_sub_item: "+ Unterpunkt hinzuf\u00fcgen",
    recurrence: "Wiederholung",
    recurrence_enabled: "Aktiviert",
    recurrence_every: "Alle",
    rec_hours: "Stunden", rec_days: "Tage", rec_weeks: "Wochen", rec_months: "Monate",
    rec_short_h: "Std.", rec_short_d: "T.", rec_short_w: "Wo.", rec_short_m: "Mon.",
    priority: "Priorit\u00e4t",
    pri_high: "Hoch", pri_medium: "Mittel", pri_low: "Niedrig",
    ed_show_priority: "Priorit\u00e4t anzeigen",
    rec_hourly: "St\u00fcndl.", rec_daily: "T\u00e4glich", rec_weekly: "W\u00f6chentl.", rec_monthly: "Monatl.",
    rec_type_interval: "Alle \u2026", rec_type_weekdays: "An Wochentagen",
    rec_wd_0: "Mo", rec_wd_1: "Di", rec_wd_2: "Mi", rec_wd_3: "Do", rec_wd_4: "Fr", rec_wd_5: "Sa", rec_wd_6: "So",
    assigned_to: "Zugewiesen an",
    nobody: "\u2013 Niemand \u2013",
    delete_task: "Aufgabe l\u00f6schen",
    delete_sub: "L\u00f6schen",
    ed_default_filter: "Standardfilter",
    ed_list: "Liste",
    ed_title: "Titel (optional)",
    ed_title_placeholder: "Standard: Listenname",
    ed_display: "Anzeige",
    ed_show_title: "Titel anzeigen",
    ed_show_progress: "Fortschritt anzeigen",
    ed_show_due_date: "F\u00e4lligkeit anzeigen",
    ed_show_notes: "Notizen anzeigen",
    ed_show_recurrence: "Wiederholung anzeigen",
    ed_show_sub_items: "Unterpunkte anzeigen",
    ed_show_person: "Zugewiesene Person anzeigen",
    ed_auto_delete: "Erledigte Aufgaben sofort l\u00f6schen",
    ed_compact: "Kompakte Ansicht",
    ed_show_tags: "Tags anzeigen",
    ed_hint: "Neue Listen k\u00f6nnen unter Einstellungen \u2192 Integrationen \u2192 Home Tasks erstellt werden.",
    tags: "Tags",
    add_tag: "+ Tag hinzuf\u00fcgen",
    tag_placeholder: "Neues Tag...",
    remove_tag: "Entfernen",
    sort_label: "Sortierung",
    sort_manual: "Manuell",
    sort_due: "F\u00e4lligkeit",
    sort_priority: "Priorit\u00e4t",
    sort_title: "Titel (A\u2013Z)",
    sort_person: "Zugewiesen",
    ed_show_sort: "Sortieren-Button anzeigen",
    ed_default_sort: "Standard-Sortierung",
    reminder: "Erinnerungen",
    rem_add: "+ Erinnerung hinzuf\u00fcgen",
    rem_none: "Keine Erinnerung",
    rem_at_due: "Zur F\u00e4lligkeit",
    rem_5m: "5 Min. vorher",
    rem_15m: "15 Min. vorher",
    rem_30m: "30 Min. vorher",
    rem_1h: "1 Std. vorher",
    rem_2h: "2 Std. vorher",
    rem_1d: "1 Tag vorher",
    rem_2d: "2 Tage vorher",
    ed_show_reminders: "Erinnerungen anzeigen",
    ed_add_column: "Spalte hinzuf\u00fcgen",
    ed_move_left: "Nach links",
    ed_move_right: "Nach rechts",
    ed_duplicate: "Spalte duplizieren",
    ed_delete_column: "Spalte l\u00f6schen",
    ed_code_editor: "Code-Editor",
    ed_visual_editor: "Visueller Editor",
  },
};

const REMINDER_OFFSETS = [
  [0, "rem_at_due"],
  [5, "rem_5m"],
  [15, "rem_15m"],
  [30, "rem_30m"],
  [60, "rem_1h"],
  [120, "rem_2h"],
  [1440, "rem_1d"],
  [2880, "rem_2d"],
];

class HomeTasksCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { columns: [{}] };
    this._hass = null;
    this._lists = [];
    // Per-column state: [{filter, sortBy, sortOpen, tagFilter, tasks, newTaskTitle}]
    this._columns = [];
    this._expandedTasks = new Set();
    this._editingTaskId = null;
    this._editingSubItemId = null;
    this._draggedTaskId = null;
    this._draggedColIdx = null;
    this._dragOverTaskId = null;
    this._touchClone = null;
    this._touchStartTimer = null;
    this._touchOffsetY = 0;
    this._touchBound = {};
    this._lastTitleClick = null;
    this._initialized = false;
  }

  _defaultColState() {
    return { filter: "all", sortBy: "manual", sortOpen: false, tagFilter: null, tasks: [], newTaskTitle: "" };
  }

  _t(key, ...args) {
    const lang = (this._hass && this._hass.language) || "en";
    const str = (_TRANSLATIONS[lang] || _TRANSLATIONS.en)[key] || _TRANSLATIONS.en[key] || key;
    return args.length ? str.replace(/\{(\d+)\}/g, (_, i) => args[i] ?? "") : str;
  }

  setConfig(config) {
    // Normalize old single-list format to columns format
    // Keep HA card-level keys (type, etc.) at root, not inside column objects
    if (config.list_id && !config.columns) {
      const { type, columns: _c, ...colConfig } = config;
      config = { ...(type ? { type } : {}), columns: [colConfig] };
    }
    if (!config.columns || !Array.isArray(config.columns) || config.columns.length === 0) {
      config = { ...config, columns: [{}] };
    }
    // Strip any stray type keys from column objects (e.g. from previously broken saves)
    config = {
      ...config,
      columns: config.columns.map(({ type: _t, ...col }) => col),
    };

    const prevConfig = this._config || { columns: [] };
    this._config = config;

    // Sync _columns array length
    while (this._columns.length < config.columns.length) {
      this._columns.push(this._defaultColState());
    }
    this._columns.length = config.columns.length;

    // Reset per-column filter/sort when list or defaults change
    for (let i = 0; i < config.columns.length; i++) {
      const col = config.columns[i];
      const prevCol = prevConfig.columns?.[i];
      if (col.list_id !== prevCol?.list_id || col.default_filter !== prevCol?.default_filter) {
        this._columns[i].filter = col.default_filter || "all";
        this._columns[i].tagFilter = null;
      }
      if (col.list_id !== prevCol?.list_id || col.default_sort !== prevCol?.default_sort) {
        this._columns[i].sortBy = col.default_sort || "manual";
      }
    }

    if (this._initialized) {
      this._loadAllTasks();
    } else {
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._loadLists();
    }
  }

  // --- Safe DOM helpers ---

  _el(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
      if (key === "className") {
        el.className = val;
      } else if (key === "textContent") {
        el.textContent = val;
      } else if (key.startsWith("on")) {
        el.addEventListener(key.slice(2).toLowerCase(), val);
      } else if (key === "checked") {
        el.checked = val;
      } else if (key === "draggable") {
        el.draggable = val;
      } else if (key === "value") {
        el.value = val;
      } else if (key === "disabled") {
        el.disabled = val;
      } else if (key === "rows") {
        el.rows = val;
      } else if (key === "type") {
        el.type = val;
      } else if (key === "placeholder") {
        el.placeholder = val;
      } else if (key === "title") {
        el.title = val;
      } else if (key === "htmlFor") {
        el.htmlFor = val;
      } else {
        el.setAttribute(key, val);
      }
    }
    for (const child of children) {
      if (typeof child === "string") {
        el.appendChild(document.createTextNode(child));
      } else if (child) {
        el.appendChild(child);
      }
    }
    return el;
  }

  _text(str) {
    return document.createTextNode(str);
  }

  // --- Data methods ---

  async _callWs(type, data = {}) {
    if (!this._hass) return null;
    try {
      const timeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("timeout")), 5000)
      );
      return await Promise.race([
        this._hass.callWS({ type, ...data }),
        timeout,
      ]);
    } catch (err) {
      console.warn(`WS call ${type} failed:`, err.message);
      return null;
    }
  }

  _showError(message) {
    const root = this.shadowRoot;
    if (!root) return;
    const existing = root.querySelector(".toast-error");
    if (existing) existing.remove();
    const toast = this._el("div", { className: "toast-error", textContent: message });
    root.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  async _loadLists() {
    const result = await this._callWs("home_tasks/get_lists");
    if (result && Array.isArray(result.lists)) {
      this._lists = result.lists;
      // Auto-select first list if no column has a list configured
      const hasAnyList = this._config.columns.some(c => c.list_id);
      if (!hasAnyList && this._lists.length > 0) {
        const newCols = [...this._config.columns];
        newCols[0] = { ...newCols[0], list_id: this._lists[0].id };
        this._config = { ...this._config, columns: newCols };
        this._columns[0].filter = newCols[0].default_filter || "all";
      }
    }
    await this._loadAllTasks();
  }

  async _loadAllTasks() {
    await Promise.all(this._config.columns.map(async (col, i) => {
      if (!col.list_id) { this._columns[i].tasks = []; return; }
      const r = await this._callWs("home_tasks/get_tasks", { list_id: col.list_id });
      this._columns[i].tasks = r?.tasks ?? [];
    }));
    this._render();
  }

  _colListId(colIdx) {
    return this._config.columns[colIdx]?.list_id;
  }

  async _addTask(colIdx) {
    const cs = this._columns[colIdx];
    const title = cs.newTaskTitle.trim();
    if (!title || !this._colListId(colIdx)) return;
    const result = await this._callWs("home_tasks/add_task", {
      list_id: this._colListId(colIdx),
      title,
    });
    if (result) {
      cs.newTaskTitle = "";
      await this._loadAllTasks();
    }
  }

  async _toggleTask(taskId, completed, colIdx) {
    const col = this._config.columns[colIdx];
    const cs = this._columns[colIdx];
    const newCompleted = !completed;
    const task = cs.tasks.find(t => t.id === taskId);
    const hasRecurrence = task && task.recurrence_enabled && task.recurrence_unit;
    if (newCompleted && col.auto_delete_completed && !hasRecurrence) {
      await this._callWs("home_tasks/delete_task", {
        list_id: this._colListId(colIdx),
        task_id: taskId,
      });
    } else {
      await this._callWs("home_tasks/update_task", {
        list_id: this._colListId(colIdx),
        task_id: taskId,
        completed: newCompleted,
      });
    }
    await this._loadAllTasks();
  }

  async _updateTaskTitle(taskId, title, colIdx) {
    if (!title.trim()) return;
    const result = await this._callWs("home_tasks/update_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      title: title.trim(),
    });
    if (result) {
      this._editingTaskId = null;
      await this._loadAllTasks();
    }
  }

  async _updateTaskNotes(taskId, notes, colIdx) {
    await this._callWs("home_tasks/update_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      notes,
    });
  }

  async _updateTaskDue(taskId, dueDate, dueTime, colIdx) {
    await this._callWs("home_tasks/update_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      due_date: dueDate || null,
      due_time: dueDate ? (dueTime || null) : null,
    });
    await this._loadAllTasks();
  }

  async _deleteTask(taskId, colIdx) {
    await this._callWs("home_tasks/delete_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
    });
    this._expandedTasks.delete(taskId);
    await this._loadAllTasks();
  }

  async _addSubItem(taskId, colIdx) {
    const result = await this._callWs("home_tasks/add_sub_item", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      title: "Neuer Unterpunkt",
    });
    if (result) {
      this._editingSubItemId = result.id;
    }
    await this._loadAllTasks();
  }

  async _toggleSubItem(taskId, subItemId, completed, colIdx) {
    await this._callWs("home_tasks/update_sub_item", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_item_id: subItemId,
      completed: !completed,
    });
    await this._loadAllTasks();
  }

  async _updateSubItemTitle(taskId, subItemId, title, colIdx) {
    if (!title.trim()) return;
    const result = await this._callWs("home_tasks/update_sub_item", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_item_id: subItemId,
      title: title.trim(),
    });
    if (result) {
      this._editingSubItemId = null;
      await this._loadAllTasks();
    }
  }

  async _deleteSubItem(taskId, subItemId, colIdx) {
    await this._callWs("home_tasks/delete_sub_item", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_item_id: subItemId,
    });
    await this._loadAllTasks();
  }

  async _reorderTasks(taskIds, colIdx) {
    const listId = this._colListId(colIdx);
    if (!listId) return;
    await this._callWs("home_tasks/reorder_tasks", {
      list_id: listId,
      task_ids: taskIds,
    });
    await this._loadAllTasks();
  }

  async _moveTask(srcColIdx, tgtColIdx, taskId, targetTaskIds) {
    const srcListId = this._colListId(srcColIdx);
    const tgtListId = this._colListId(tgtColIdx);
    if (!srcListId || !tgtListId) return;
    await this._callWs("home_tasks/move_task", {
      source_list_id: srcListId,
      target_list_id: tgtListId,
      task_id: taskId,
    });
    if (targetTaskIds.length > 0) {
      await this._callWs("home_tasks/reorder_tasks", {
        list_id: tgtListId,
        task_ids: targetTaskIds,
      });
    }
    await this._loadAllTasks();
  }

  // --- Filter & Sort ---

  _filteredTasks(colIdx) {
    const cs = this._columns[colIdx];
    let tasks;
    switch (cs.filter) {
      case "open":
        tasks = cs.tasks.filter((t) => !t.completed);
        break;
      case "done":
        tasks = cs.tasks.filter((t) => t.completed);
        break;
      default:
        tasks = cs.tasks;
    }
    if (cs.tagFilter) {
      tasks = tasks.filter((t) => t.tags && t.tags.includes(cs.tagFilter));
    }
    const cmp = this._buildSortComparator(colIdx);
    return tasks.slice().sort((a, b) => {
      if (a.completed !== b.completed) return a.completed ? 1 : -1;
      return cmp(a, b);
    });
  }

  _buildSortComparator(colIdx) {
    const sortBy = this._columns[colIdx].sortBy;
    switch (sortBy) {
      case "due": return (a, b) => {
        const da = a.due_date ? a.due_date + (a.due_time || "00:00") : null;
        const db = b.due_date ? b.due_date + (b.due_time || "00:00") : null;
        if (da && db) return da < db ? -1 : da > db ? 1 : 0;
        return da ? -1 : db ? 1 : 0;
      };
      case "priority": return (a, b) => {
        const pa = a.priority ?? 0;
        const pb = b.priority ?? 0;
        return pb - pa;
      };
      case "title": return (a, b) =>
        (a.title || "").localeCompare(b.title || "", undefined, { sensitivity: "base" });
      case "person": return (a, b) => {
        const pa = a.assigned_person || "\uffff";
        const pb = b.assigned_person || "\uffff";
        return pa.localeCompare(pb);
      };
      default: return (a, b) => a.sort_order - b.sort_order;
    }
  }

  // --- Helpers ---

  _getCompletedCount(colIdx) {
    return this._columns[colIdx].tasks.filter((t) => t.completed).length;
  }

  _getSubItemProgress(task) {
    if (!task.sub_items || task.sub_items.length === 0) return null;
    const done = task.sub_items.filter((s) => s.completed).length;
    return `${done}/${task.sub_items.length}`;
  }

  _isDueDateOverdue(dueDate) {
    if (!dueDate) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return new Date(dueDate) < today;
  }

  _isDueDateToday(dueDate) {
    if (!dueDate) return false;
    const today = new Date().toISOString().split("T")[0];
    return dueDate === today;
  }

  _formatDueDate(dueDate, dueTime) {
    if (!dueDate) return "";
    const date = new Date(dueDate + "T00:00:00");
    const lang = (this._hass && this._hass.language) || "en";
    let formatted = date.toLocaleDateString(lang, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
    if (dueTime) formatted += " " + dueTime;
    return formatted;
  }

  _getListName(colIdx) {
    const col = this._config.columns[colIdx];
    if (col.title) return col.title;
    const list = this._lists.find((l) => l.id === col.list_id);
    return list ? list.name : this._t("my_tasks");
  }

  // --- Render ---

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = this._getStyles();
    root.appendChild(style);

    const card = this._el("ha-card", {}, [
      this._buildCardContent(),
    ]);
    root.appendChild(card);

    // Close any open sort dropdowns on next outside click
    if (this._columns.some(c => c.sortOpen)) {
      setTimeout(() => document.addEventListener("click", () => {
        this._columns.forEach(c => { c.sortOpen = false; });
        this._render();
      }, { once: true }), 0);
    }
  }

  _buildCardContent() {
    const cols = this._config.columns;
    if (cols.length === 1) {
      return this._buildColumn(0);
    }
    const colEls = cols.map((_, i) => this._buildColumn(i));
    return this._el("div", { className: "multi-columns" }, colEls);
  }

  _buildColumn(colIdx) {
    const col = this._config.columns[colIdx];
    const cs = this._columns[colIdx];
    const compact = col.compact === true;
    const filteredTasks = this._filteredTasks(colIdx);
    const completedCount = this._getCompletedCount(colIdx);
    const totalCount = cs.tasks.length;

    // Header
    const showTitle = col.show_title !== false;
    const showProgress = col.show_progress !== false;
    const headerChildren = [];
    if (showTitle) {
      headerChildren.push(this._el("h1", { className: "title", textContent: this._getListName(colIdx) }));
    }
    if (showProgress) {
      headerChildren.push(this._el("span", {
        className: "progress",
        textContent: this._t("progress", completedCount, totalCount),
      }));
    }
    const header = headerChildren.length > 0
      ? this._el("div", { className: "header" }, headerChildren)
      : null;

    // Add task input
    const addInput = this._el("input", {
      type: "text",
      className: "add-input",
      placeholder: this._t("add_placeholder"),
      value: cs.newTaskTitle,
    });
    addInput.addEventListener("input", (e) => {
      cs.newTaskTitle = e.target.value;
    });
    addInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._addTask(colIdx);
    });

    const addBtn = this._el("button", {
      className: "add-btn",
      textContent: "+",
    });
    addBtn.addEventListener("click", () => this._addTask(colIdx));

    const addTask = this._el("div", { className: "add-task" }, [addInput, addBtn]);

    // Sort button
    const sortLabels = {
      manual: this._t("sort_manual"), due: this._t("sort_due"),
      priority: this._t("sort_priority"), title: this._t("sort_title"),
      person: this._t("sort_person"),
    };
    const sortKeys = ["manual"];
    if (col.show_due_date !== false) sortKeys.push("due");
    if (col.show_priority !== false) sortKeys.push("priority");
    sortKeys.push("title");
    if (col.show_assigned_person !== false) sortKeys.push("person");
    if (!sortKeys.includes(cs.sortBy)) cs.sortBy = "manual";

    const sortDropdown = this._el("div", { className: "sort-dropdown" + (cs.sortOpen ? "" : " hidden") });
    for (const key of sortKeys) {
      const opt = this._el("div", {
        className: "sort-option" + (cs.sortBy === key ? " active" : ""),
        textContent: sortLabels[key],
      });
      opt.addEventListener("click", (e) => {
        e.stopPropagation();
        cs.sortBy = key;
        cs.sortOpen = false;
        this._render();
      });
      sortDropdown.appendChild(opt);
    }
    const sortBtnWrapper = this._el("div", { className: "sort-btn-wrapper" });
    const sortBtn = this._el("button", {
      className: "sort-btn" + (cs.sortBy !== "manual" ? " active" : ""),
      textContent: "\u21C5",
      title: sortLabels[cs.sortBy],
    });
    sortBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const wasOpen = cs.sortOpen;
      this._columns.forEach(c => { c.sortOpen = false; });
      cs.sortOpen = !wasOpen;
      this._render();
    });
    sortBtnWrapper.appendChild(sortBtn);
    sortBtnWrapper.appendChild(sortDropdown);

    // Filter row
    const hideFilters = col.auto_delete_completed === true;
    const filterRowChildren = [];
    if (!hideFilters) {
      filterRowChildren.push(
        this._buildFilterBtn(this._t("filter_all"), "all", colIdx),
        this._buildFilterBtn(this._t("filter_open"), "open", colIdx),
        this._buildFilterBtn(this._t("filter_done"), "done", colIdx),
      );
    }
    filterRowChildren.push(this._el("div", { className: "filter-spacer" }));
    if (col.show_sort !== false) filterRowChildren.push(sortBtnWrapper);
    const filters = this._el("div", { className: "filters" }, filterRowChildren);

    // Tag chips
    let tagChips = null;
    if (col.show_tags !== false) {
      const allTags = new Set();
      for (const t of cs.tasks) {
        for (const tag of (t.tags || [])) allTags.add(tag);
      }
      if (allTags.size > 0) {
        const chipChildren = [];
        for (const tag of [...allTags].sort()) {
          const isActive = cs.tagFilter === tag;
          const chip = this._el("button", {
            className: "tag-chip" + (isActive ? " active" : ""),
            textContent: "#" + tag,
          });
          chip.addEventListener("click", () => {
            cs.tagFilter = isActive ? null : tag;
            this._render();
          });
          chipChildren.push(chip);
        }
        tagChips = this._el("div", { className: "tag-chips" }, chipChildren);
      }
    }

    // Task list
    const taskListChildren = [];
    if (filteredTasks.length === 0) {
      taskListChildren.push(
        this._el("div", { className: "empty-state", textContent: this._t("empty") })
      );
    }
    for (const task of filteredTasks) {
      taskListChildren.push(this._buildTask(task, colIdx));
    }
    const taskList = this._el("div", {
      className: "task-list",
      "data-col-idx": String(colIdx),
    }, taskListChildren);

    // Allow dropping on empty column
    taskList.addEventListener("dragover", (e) => {
      e.preventDefault();
      if (!this._draggedTaskId) return;
      const tgtColIdx = parseInt(taskList.dataset.colIdx);
      if (tgtColIdx !== this._draggedColIdx) {
        const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${this._draggedTaskId}"]`);
        if (draggedEl && draggedEl.parentNode !== taskList) {
          taskList.appendChild(draggedEl);
        }
        taskList.closest(".card-column")?.classList.add("drag-target");
      }
    });
    taskList.addEventListener("drop", (e) => {
      e.preventDefault();
      this._finishDrag();
    });

    const children = [];
    if (header) children.push(header);
    children.push(addTask);
    children.push(filters);
    if (tagChips) children.push(tagChips);
    children.push(taskList);

    const className = "card-column" + (compact ? " compact" : "");
    return this._el("div", { className }, children);
  }

  _buildFilterBtn(label, value, colIdx) {
    const cs = this._columns[colIdx];
    const btn = this._el("button", {
      className: `filter-btn${cs.filter === value ? " active" : ""}`,
      textContent: label,
    });
    btn.addEventListener("click", () => {
      cs.filter = value;
      this._render();
    });
    return btn;
  }

  _buildTask(task, colIdx) {
    const cs = this._columns[colIdx];
    const isExpanded = this._expandedTasks.has(task.id);
    const isEditing = this._editingTaskId === task.id;

    let className = "task";
    if (task.completed) className += " completed";

    const taskEl = this._el("div", { className, draggable: true });
    taskEl.dataset.taskId = task.id;

    const mainChildren = [];

    const dragHandle = this._el("span", {
      className: "drag-handle" + (cs.sortBy !== "manual" ? " hidden" : ""),
      title: this._t("drag_handle"),
      textContent: "\u2237",
    });
    mainChildren.push(dragHandle);

    const checkbox = this._el("input", { type: "checkbox", checked: task.completed });
    checkbox.addEventListener("change", () => this._toggleTask(task.id, task.completed, colIdx));
    const checkmark = this._el("span", { className: "checkmark" });
    const label = this._el("label", { className: "checkbox-container" }, [checkbox, checkmark]);
    mainChildren.push(label);

    const contentChildren = [];

    if (isEditing) {
      const editInput = this._el("input", {
        type: "text",
        className: "edit-title-input",
        value: task.title,
      });
      editInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this._updateTaskTitle(task.id, editInput.value, colIdx);
        else if (e.key === "Escape") { this._editingTaskId = null; this._render(); }
      });
      editInput.addEventListener("blur", () => this._updateTaskTitle(task.id, editInput.value, colIdx));
      contentChildren.push(editInput);
      setTimeout(() => { editInput.focus(); editInput.select(); }, 0);
    } else {
      const col = this._config.columns[colIdx];
      const titleSpan = this._el("span", { className: "task-title", textContent: task.title });
      titleSpan.addEventListener("click", () => {
        const now = Date.now();
        if (this._lastTitleClick?.id === task.id && now - this._lastTitleClick.time < 300) {
          this._lastTitleClick = null;
          if (this._expandedTasks.has(task.id)) this._expandedTasks.delete(task.id);
          else this._expandedTasks.add(task.id);
          this._editingTaskId = task.id;
          this._render();
          return;
        }
        this._lastTitleClick = { id: task.id, time: now };
        if (this._expandedTasks.has(task.id)) this._expandedTasks.delete(task.id);
        else this._expandedTasks.add(task.id);
        this._render();
      });
      contentChildren.push(titleSpan);
    }

    const col = this._config.columns[colIdx];
    const metaChildren = [];
    if (task.priority && col.show_priority !== false) {
      const priLabels = { 1: this._t("pri_low"), 2: this._t("pri_medium"), 3: this._t("pri_high") };
      const priClass = { 1: "pri-low", 2: "pri-medium", 3: "pri-high" };
      metaChildren.push(this._el("span", {
        className: `priority-badge ${priClass[task.priority] || ""}`,
        textContent: priLabels[task.priority],
      }));
    }
    const subProgress = this._getSubItemProgress(task);
    if (subProgress && col.show_sub_items !== false) {
      metaChildren.push(this._el("span", { className: "sub-badge", textContent: subProgress }));
    }
    if (task.due_date && col.show_due_date !== false) {
      let dueCls = "due-date";
      if (this._isDueDateOverdue(task.due_date)) dueCls += " overdue";
      else if (this._isDueDateToday(task.due_date)) dueCls += " today";
      metaChildren.push(this._el("span", {
        className: dueCls,
        textContent: this._formatDueDate(task.due_date, task.due_time),
      }));
    }
    if (task.recurrence_enabled && col.show_recurrence !== false) {
      let recLabel = null;
      if (task.recurrence_type === "weekdays" && task.recurrence_weekdays && task.recurrence_weekdays.length) {
        recLabel = task.recurrence_weekdays.map(d => this._t(`rec_wd_${d}`)).join(" ");
      } else if (task.recurrence_unit) {
        const unitLabels = { hours: this._t("rec_short_h"), days: this._t("rec_short_d"), weeks: this._t("rec_short_w"), months: this._t("rec_short_m") };
        const val = task.recurrence_value || 1;
        const singleLabels = { hours: this._t("rec_hourly"), days: this._t("rec_daily"), weeks: this._t("rec_weekly"), months: this._t("rec_monthly") };
        recLabel = val === 1 ? singleLabels[task.recurrence_unit] : `${val} ${unitLabels[task.recurrence_unit] || task.recurrence_unit}`;
      }
      if (recLabel) {
        metaChildren.push(this._el("span", {
          className: "recurrence-badge",
          textContent: "\u21BB " + recLabel,
        }));
      }
    }
    if (task.assigned_person && col.show_assigned_person !== false) {
      let personName = task.assigned_person;
      if (this._hass && this._hass.states && this._hass.states[task.assigned_person]) {
        const attrs = this._hass.states[task.assigned_person].attributes;
        personName = (attrs && attrs.friendly_name) || task.assigned_person;
      }
      metaChildren.push(this._el("span", {
        className: "assigned-badge",
        textContent: "\uD83D\uDC64 " + personName,
      }));
    }
    if (task.tags && task.tags.length > 0 && col.show_tags !== false) {
      for (const tag of task.tags) {
        const isActive = cs.tagFilter === tag;
        const tagBadge = this._el("span", {
          className: "tag-badge" + (isActive ? " active" : ""),
          textContent: "#" + tag,
        });
        tagBadge.addEventListener("click", (e) => {
          e.stopPropagation();
          cs.tagFilter = isActive ? null : tag;
          this._render();
        });
        metaChildren.push(tagBadge);
      }
    }
    if (task.reminders && task.reminders.length > 0 && col.show_reminders !== false) {
      let remText;
      if (task.reminders.length === 1) {
        const entry = REMINDER_OFFSETS.find(([v]) => v === task.reminders[0]);
        remText = "\u23F0 " + (entry ? this._t(entry[1]) : task.reminders[0] + " min");
      } else {
        remText = "\u23F0 " + task.reminders.length;
      }
      metaChildren.push(this._el("span", { className: "reminder-badge", textContent: remText }));
    }
    if (metaChildren.length > 0) {
      contentChildren.push(this._el("div", { className: "task-meta" }, metaChildren));
    }

    mainChildren.push(this._el("div", { className: "task-content" }, contentChildren));

    const expandBtn = this._el("button", {
      className: "expand-btn",
      textContent: isExpanded ? "\u25BC" : "\u25B6",
    });
    expandBtn.addEventListener("click", () => {
      if (this._expandedTasks.has(task.id)) this._expandedTasks.delete(task.id);
      else this._expandedTasks.add(task.id);
      this._render();
    });
    mainChildren.push(expandBtn);

    const mainRow = this._el("div", { className: "task-main" }, mainChildren);
    taskEl.appendChild(mainRow);

    if (isExpanded) {
      taskEl.appendChild(this._buildTaskDetails(task, colIdx));
    }

    this._attachDragToTask(taskEl, task.id, dragHandle, colIdx);

    return taskEl;
  }

  _buildTaskDetails(task, colIdx) {
    const col = this._config.columns[colIdx];
    const listId = this._colListId(colIdx);

    // Due section
    const dateInput = this._el("input", {
      type: "date",
      className: "date-input",
      value: task.due_date || "",
    });
    const timeInput = this._el("input", {
      type: "time",
      className: "time-input",
      value: task.due_time || "",
    });
    if (!task.due_date) timeInput.disabled = true;

    dateInput.addEventListener("change", () => {
      if (!dateInput.value) timeInput.value = "";
      timeInput.disabled = !dateInput.value;
      this._updateTaskDue(task.id, dateInput.value, timeInput.value, colIdx);
    });
    timeInput.addEventListener("change", () =>
      this._updateTaskDue(task.id, dateInput.value, timeInput.value, colIdx)
    );

    const dateSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("due_date") }),
      this._el("div", { className: "due-input-row" }, [dateInput, timeInput]),
    ]);

    // Notes section
    const notesInput = this._el("textarea", {
      className: "notes-input",
      placeholder: this._t("notes_placeholder"),
      rows: 2,
      value: task.notes || "",
    });
    notesInput.textContent = task.notes || "";
    let debounceTimer;
    notesInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this._updateTaskNotes(task.id, notesInput.value, colIdx);
      }, 500);
    });
    const notesSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("notes") }),
      notesInput,
    ]);

    // Sub-items section
    const subChildren = [
      this._el("label", { className: "detail-label", textContent: this._t("sub_items") }),
    ];
    for (const sub of task.sub_items) {
      subChildren.push(this._buildSubItem(task.id, sub, colIdx));
    }
    const addSubBtn = this._el("button", {
      className: "add-sub-btn",
      textContent: this._t("add_sub_item"),
    });
    addSubBtn.addEventListener("click", () => this._addSubItem(task.id, colIdx));
    subChildren.push(addSubBtn);
    const subSection = this._el("div", { className: "detail-section" }, subChildren);

    // Priority section
    const currentPriority = task.priority || null;
    const priorityBtnRow = this._el("div", { className: "priority-btn-row" });
    for (const [val, key] of [[1, "pri_low"], [2, "pri_medium"], [3, "pri_high"]]) {
      const btn = this._el("button", {
        className: `priority-btn pri-${val}${currentPriority === val ? " active" : ""}`,
        textContent: this._t(key),
      });
      btn.addEventListener("click", () => {
        this._callWs("home_tasks/update_task", {
          list_id: listId,
          task_id: task.id,
          priority: currentPriority === val ? null : val,
        }).then(() => this._loadAllTasks());
      });
      priorityBtnRow.appendChild(btn);
    }
    const prioritySection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("priority") }),
      priorityBtnRow,
    ]);

    // Recurrence section
    const recurrenceEnabled = task.recurrence_enabled || false;
    const recurrenceValue = task.recurrence_value || 1;
    const recurrenceUnit = task.recurrence_unit || "days";
    const recurrenceType = task.recurrence_type || "interval";
    const recurrenceWeekdays = task.recurrence_weekdays || [];

    const recurrenceToggle = this._el("input", { type: "checkbox", checked: recurrenceEnabled });
    const recurrenceCheckmark = this._el("span", { className: "checkmark" });
    const recurrenceLabel = this._el("label", { className: "checkbox-container small" }, [
      recurrenceToggle, recurrenceCheckmark,
    ]);
    const recurrenceToggleRow = this._el("div", { className: "recurrence-toggle-row" }, [
      recurrenceLabel,
      this._el("span", { textContent: this._t("recurrence_enabled") }),
    ]);

    const recurrenceModeSelect = this._el("select", { className: "recurrence-select recurrence-mode-select" });
    for (const [val, key] of [["interval", "rec_type_interval"], ["weekdays", "rec_type_weekdays"]]) {
      const opt = this._el("option", { value: val, textContent: this._t(key) });
      if (val === recurrenceType) opt.selected = true;
      recurrenceModeSelect.appendChild(opt);
    }

    const recurrenceValueInput = this._el("input", {
      type: "number",
      className: "recurrence-value",
      value: recurrenceValue,
    });
    recurrenceValueInput.min = 1;
    recurrenceValueInput.max = 365;

    const recurrenceUnitSelect = this._el("select", { className: "recurrence-select" });
    for (const opt of [
      { value: "hours", label: this._t("rec_hours") },
      { value: "days", label: this._t("rec_days") },
      { value: "weeks", label: this._t("rec_weeks") },
      { value: "months", label: this._t("rec_months") },
    ]) {
      const optEl = this._el("option", { value: opt.value, textContent: opt.label });
      if (opt.value === recurrenceUnit) optEl.selected = true;
      recurrenceUnitSelect.appendChild(optEl);
    }

    const recurrenceIntervalRow = this._el("div", { className: "recurrence-input-row" }, [
      this._el("span", { textContent: this._t("recurrence_every"), className: "recurrence-prefix" }),
      recurrenceValueInput,
      recurrenceUnitSelect,
    ]);

    const weekdayCheckboxes = [];
    const recurrenceWeekdayRow = this._el("div", { className: "recurrence-weekday-row" });
    for (let d = 0; d < 7; d++) {
      const cb = this._el("input", { type: "checkbox", checked: recurrenceWeekdays.includes(d) });
      const lbl = this._el("label", { className: "weekday-label" }, [
        cb,
        this._el("span", { textContent: this._t(`rec_wd_${d}`) }),
      ]);
      weekdayCheckboxes.push(cb);
      recurrenceWeekdayRow.appendChild(lbl);
    }

    const applyModeVisibility = (type) => {
      recurrenceIntervalRow.style.display = type === "interval" ? "" : "none";
      recurrenceWeekdayRow.style.display = type === "weekdays" ? "" : "none";
    };
    applyModeVisibility(recurrenceType);

    const applyEnabledState = (enabled) => {
      recurrenceModeSelect.disabled = !enabled;
      recurrenceValueInput.disabled = !enabled;
      recurrenceUnitSelect.disabled = !enabled;
      weekdayCheckboxes.forEach(cb => { cb.disabled = !enabled; });
    };
    applyEnabledState(recurrenceEnabled);

    const saveWeekdays = () => {
      const selected = weekdayCheckboxes.map((cb, i) => cb.checked ? i : -1).filter(i => i >= 0);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_weekdays: selected,
      }).then(() => this._loadAllTasks());
    };

    const saveInterval = () => {
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      recurrenceValueInput.value = val;
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
      }).then(() => this._loadAllTasks());
    };

    recurrenceToggle.addEventListener("change", () => {
      const enabled = recurrenceToggle.checked;
      applyEnabledState(enabled);
      const mode = recurrenceModeSelect.value;
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      const selected = weekdayCheckboxes.map((cb, i) => cb.checked ? i : -1).filter(i => i >= 0);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_enabled: enabled,
        recurrence_type: mode,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
        recurrence_weekdays: selected,
      }).then(() => this._loadAllTasks());
    });

    recurrenceModeSelect.addEventListener("change", () => {
      const mode = recurrenceModeSelect.value;
      applyModeVisibility(mode);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_type: mode,
      }).then(() => this._loadAllTasks());
    });

    recurrenceValueInput.addEventListener("change", saveInterval);
    recurrenceUnitSelect.addEventListener("change", saveInterval);
    weekdayCheckboxes.forEach(cb => cb.addEventListener("change", saveWeekdays));

    const recurrenceSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("recurrence") }),
      recurrenceToggleRow,
      recurrenceModeSelect,
      recurrenceIntervalRow,
      recurrenceWeekdayRow,
    ]);

    // Assigned person section
    const personSelect = this._el("select", { className: "person-select" });
    const noneOpt = this._el("option", { value: "", textContent: this._t("nobody") });
    if (!task.assigned_person) noneOpt.selected = true;
    personSelect.appendChild(noneOpt);
    if (this._hass && this._hass.states) {
      const persons = Object.keys(this._hass.states)
        .filter(eid => eid.startsWith("person."))
        .sort();
      for (const eid of persons) {
        const state = this._hass.states[eid];
        const name = (state && state.attributes && state.attributes.friendly_name) || eid;
        const opt = this._el("option", { value: eid, textContent: name });
        if (eid === task.assigned_person) opt.selected = true;
        personSelect.appendChild(opt);
      }
    }
    personSelect.addEventListener("change", () => {
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        assigned_person: personSelect.value || null,
      }).then(() => this._loadAllTasks());
    });
    const personSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("assigned_to") }),
      personSelect,
    ]);

    // Tags section
    const tagSectionChildren = [
      this._el("label", { className: "detail-label", textContent: this._t("tags") }),
    ];
    const taskTags = task.tags || [];
    if (taskTags.length > 0) {
      const tagListEl = this._el("div", { className: "tag-list" });
      for (const tag of taskTags) {
        const removeBtn = this._el("button", {
          className: "remove-tag-btn",
          title: this._t("remove_tag"),
          textContent: "\u00D7",
        });
        removeBtn.addEventListener("click", () => {
          const newTags = taskTags.filter((t) => t !== tag);
          this._callWs("home_tasks/update_task", {
            list_id: listId,
            task_id: task.id,
            tags: newTags,
          }).then(() => this._loadAllTasks());
        });
        tagListEl.appendChild(
          this._el("span", { className: "tag-item" }, [
            this._el("span", { textContent: "#" + tag }),
            removeBtn,
          ])
        );
      }
      tagSectionChildren.push(tagListEl);
    }
    const tagInput = this._el("input", {
      type: "text",
      className: "tag-input",
      placeholder: this._t("tag_placeholder"),
    });
    tagInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const val = tagInput.value.trim().toLowerCase();
        if (val && !taskTags.includes(val)) {
          this._callWs("home_tasks/update_task", {
            list_id: listId,
            task_id: task.id,
            tags: [...taskTags, val],
          }).then(() => this._loadAllTasks());
        }
        tagInput.value = "";
      }
    });
    tagSectionChildren.push(tagInput);
    const tagSection = this._el("div", { className: "detail-section" }, tagSectionChildren);

    // Reminders section
    const taskReminders = task.reminders || [];
    const reminderSectionChildren = [
      this._el("label", { className: "detail-label", textContent: this._t("reminder") }),
    ];
    const _rebuildReminders = (newReminders) => {
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        reminders: newReminders,
      }).then(() => this._loadAllTasks());
    };
    for (let ri = 0; ri < taskReminders.length; ri++) {
      const offset = taskReminders[ri];
      const sel = this._el("select", { className: "reminder-select" });
      for (const [val, key] of REMINDER_OFFSETS) {
        const opt = this._el("option", { value: String(val), textContent: this._t(key) });
        if (val === offset) opt.selected = true;
        sel.appendChild(opt);
      }
      sel.addEventListener("change", () => {
        const updated = [...taskReminders];
        updated[ri] = parseInt(sel.value, 10);
        _rebuildReminders(updated);
      });
      const removeBtn = this._el("button", {
        className: "reminder-remove",
        textContent: "\u00D7",
        title: this._t("remove_tag"),
      });
      removeBtn.addEventListener("click", () => {
        const updated = taskReminders.filter((_, i) => i !== ri);
        _rebuildReminders(updated);
      });
      reminderSectionChildren.push(this._el("div", { className: "reminder-row" }, [sel, removeBtn]));
    }
    if (taskReminders.length < 5) {
      const addReminderBtn = this._el("button", {
        className: "add-reminder-btn",
        textContent: this._t("rem_add"),
      });
      addReminderBtn.addEventListener("click", () => {
        const used = new Set(taskReminders);
        const defaultOffset = (REMINDER_OFFSETS.find(([v]) => !used.has(v)) || REMINDER_OFFSETS[3])[0];
        _rebuildReminders([...taskReminders, defaultOffset]);
      });
      reminderSectionChildren.push(addReminderBtn);
    }
    const reminderSection = this._el("div", { className: "detail-section" }, reminderSectionChildren);

    // Delete button
    const deleteBtn = this._el("button", {
      className: "delete-task-btn",
      textContent: this._t("delete_task"),
    });
    deleteBtn.addEventListener("click", () => this._deleteTask(task.id, colIdx));
    const actions = this._el("div", { className: "detail-actions" }, [deleteBtn]);

    const details = [];
    if (col.show_notes !== false) details.push(notesSection);
    if (col.show_sub_items !== false) details.push(subSection);
    if (col.show_assigned_person !== false) details.push(personSection);
    if (col.show_priority !== false) details.push(prioritySection);
    if (col.show_tags !== false) details.push(tagSection);
    if (col.show_due_date !== false) details.push(dateSection);
    if (col.show_reminders !== false) details.push(reminderSection);
    if (col.show_recurrence !== false) details.push(recurrenceSection);
    details.push(actions);
    return this._el("div", { className: "task-details" }, details);
  }

  _buildSubItem(taskId, sub, colIdx) {
    const isEditing = this._editingSubItemId === sub.id;

    const checkbox = this._el("input", { type: "checkbox", checked: sub.completed });
    checkbox.addEventListener("change", () =>
      this._toggleSubItem(taskId, sub.id, sub.completed, colIdx)
    );
    const checkmark = this._el("span", { className: "checkmark" });
    const label = this._el("label", { className: "checkbox-container small" }, [
      checkbox, checkmark,
    ]);

    let titleEl;
    if (isEditing) {
      titleEl = this._el("input", {
        type: "text",
        className: "edit-sub-input",
        value: sub.title,
      });
      titleEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this._updateSubItemTitle(taskId, sub.id, titleEl.value, colIdx);
        else if (e.key === "Escape") { this._editingSubItemId = null; this._render(); }
      });
      titleEl.addEventListener("blur", () =>
        this._updateSubItemTitle(taskId, sub.id, titleEl.value, colIdx)
      );
      setTimeout(() => { titleEl.focus(); titleEl.select(); }, 0);
    } else {
      let subCls = "sub-title";
      if (sub.completed) subCls += " completed";
      titleEl = this._el("span", { className: subCls, textContent: sub.title });
      titleEl.addEventListener("dblclick", () => {
        this._editingSubItemId = sub.id;
        this._render();
      });
    }

    const deleteBtn = this._el("button", {
      className: "delete-sub-btn",
      title: this._t("delete_sub"),
      textContent: "\u00D7",
    });
    deleteBtn.addEventListener("click", () => this._deleteSubItem(taskId, sub.id, colIdx));

    return this._el("div", { className: "sub-item" }, [label, titleEl, deleteBtn]);
  }

  // --- Drag & Drop ---

  _getOrderFromDom(colIdx) {
    const taskList = this.shadowRoot.querySelector(`.task-list[data-col-idx="${colIdx}"]`);
    if (!taskList) return [];
    return Array.from(taskList.querySelectorAll(".task")).map((el) => el.dataset.taskId);
  }

  _mergeHiddenTasks(colIdx, visibleOrder) {
    const cs = this._columns[colIdx];
    const filteredIds = new Set(visibleOrder);
    const hiddenIds = cs.tasks.map((t) => t.id).filter((id) => !filteredIds.has(id));
    const fullOrder = [...visibleOrder];
    const origOrder = cs.tasks.map((t) => t.id);
    for (const hid of hiddenIds) {
      const origIdx = origOrder.indexOf(hid);
      let insertIdx = fullOrder.length;
      for (let i = origIdx - 1; i >= 0; i--) {
        const prevId = origOrder[i];
        const posInNew = fullOrder.indexOf(prevId);
        if (posInNew !== -1) { insertIdx = posInNew + 1; break; }
      }
      fullOrder.splice(insertIdx, 0, hid);
    }
    return fullOrder;
  }

  _liveMoveTask(draggedEl, targetEl) {
    if (!draggedEl || !targetEl || draggedEl === targetEl) return;
    const targetList = targetEl.parentNode;
    if (!targetList) return;
    const draggedRect = draggedEl.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    if (draggedRect.top < targetRect.top) {
      targetList.insertBefore(draggedEl, targetEl.nextSibling);
    } else {
      targetList.insertBefore(draggedEl, targetEl);
    }
  }

  _finishDrag() {
    const draggedId = this._draggedTaskId;
    const srcColIdx = this._draggedColIdx;

    // Determine which column the dragged element ended up in
    const draggedEl = draggedId
      ? this.shadowRoot.querySelector(`[data-task-id="${draggedId}"]`)
      : null;
    const currentTaskList = draggedEl?.closest(".task-list");
    const tgtColIdx = currentTaskList !== null && currentTaskList !== undefined
      ? parseInt(currentTaskList.dataset.colIdx ?? srcColIdx)
      : srcColIdx;

    // Clean up
    this._draggedTaskId = null;
    this._draggedColIdx = null;
    this._dragOverTaskId = null;
    this.shadowRoot.querySelectorAll(".task").forEach((el) => {
      el.classList.remove("dragging", "drag-over");
    });
    this.shadowRoot.querySelectorAll(".card-column").forEach((el) => {
      el.classList.remove("drag-target");
    });
    if (this._touchClone) { this._touchClone.remove(); this._touchClone = null; }
    if (this._touchStartTimer) { clearTimeout(this._touchStartTimer); this._touchStartTimer = null; }

    if (!draggedId || srcColIdx === null) return;

    if (!isNaN(tgtColIdx) && tgtColIdx !== srcColIdx) {
      // Cross-column move
      const targetTaskIds = this._getOrderFromDom(tgtColIdx);
      this._moveTask(srcColIdx, tgtColIdx, draggedId, targetTaskIds);
    } else {
      // Same-column reorder
      const visibleOrder = this._getOrderFromDom(srcColIdx ?? 0);
      if (visibleOrder.length > 0) {
        const fullOrder = this._mergeHiddenTasks(srcColIdx ?? 0, visibleOrder);
        this._reorderTasks(fullOrder, srcColIdx ?? 0);
      }
    }
  }

  _attachDragToTask(taskEl, taskId, dragHandle, colIdx) {
    // HTML5 Drag & Drop (Desktop)
    taskEl.addEventListener("dragstart", (e) => {
      this._draggedTaskId = taskId;
      this._draggedColIdx = colIdx;
      e.dataTransfer.effectAllowed = "move";
      taskEl.classList.add("dragging");
    });

    taskEl.addEventListener("dragend", () => {
      this._finishDrag();
    });

    taskEl.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (!this._draggedTaskId || this._draggedTaskId === taskId) return;
      const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${this._draggedTaskId}"]`);
      this._liveMoveTask(draggedEl, taskEl);
      // Visual feedback for cross-column target
      const tgtList = taskEl.closest(".task-list");
      const tgtColIdx = tgtList ? parseInt(tgtList.dataset.colIdx) : colIdx;
      if (tgtColIdx !== this._draggedColIdx) {
        this.shadowRoot.querySelectorAll(".card-column").forEach(el => el.classList.remove("drag-target"));
        taskEl.closest(".card-column")?.classList.add("drag-target");
      }
    });

    taskEl.addEventListener("drop", (e) => {
      e.preventDefault();
      this._finishDrag();
    });

    // Touch Events (Mobile)
    if (!dragHandle) return;

    dragHandle.addEventListener("touchstart", (e) => {
      if (e.touches.length !== 1) return;
      const touch = e.touches[0];
      this._touchStartTimer = setTimeout(() => {
        this._draggedTaskId = taskId;
        this._draggedColIdx = colIdx;
        taskEl.classList.add("dragging");

        const rect = taskEl.getBoundingClientRect();
        const clone = taskEl.cloneNode(true);
        clone.className = "task drag-clone";
        clone.style.cssText = `
          position: fixed; top: ${rect.top}px; left: ${rect.left}px;
          width: ${rect.width}px; z-index: 1000; opacity: 0.85;
          pointer-events: none;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          background: var(--todo-bg, #fff);
          border-radius: var(--todo-radius, 8px);
          border: 1px solid var(--todo-primary, #03a9f4);
        `;
        this.shadowRoot.appendChild(clone);
        this._touchClone = clone;
        this._touchOffsetY = touch.clientY - rect.top;
      }, 150);
    }, { passive: true });

    const onTouchMove = (e) => {
      if (!this._draggedTaskId) {
        if (this._touchStartTimer) {
          clearTimeout(this._touchStartTimer);
          this._touchStartTimer = null;
        }
        return;
      }
      e.preventDefault();
      const touch = e.touches[0];

      if (this._touchClone) {
        this._touchClone.style.top = `${touch.clientY - this._touchOffsetY}px`;
      }

      if (this._touchClone) this._touchClone.style.display = "none";
      const shadowEl = this.shadowRoot.elementFromPoint(touch.clientX, touch.clientY);
      if (this._touchClone) this._touchClone.style.display = "";

      const target = shadowEl ? shadowEl.closest(".task") : null;
      if (target && target.dataset.taskId && target.dataset.taskId !== this._draggedTaskId && !target.classList.contains("drag-clone")) {
        const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${this._draggedTaskId}"]`);
        this._liveMoveTask(draggedEl, target);
      }
    };

    const onTouchEnd = () => {
      if (this._touchStartTimer) {
        clearTimeout(this._touchStartTimer);
        this._touchStartTimer = null;
      }
      if (this._draggedTaskId) {
        this._finishDrag();
      }
    };

    dragHandle.addEventListener("touchmove", onTouchMove, { passive: false });
    dragHandle.addEventListener("touchend", onTouchEnd);
    dragHandle.addEventListener("touchcancel", onTouchEnd);
  }

  // --- Styles ---

  _getStyles() {
    return `
      :host {
        --todo-primary: var(--primary-color, #03a9f4);
        --todo-bg: var(--card-background-color, #fff);
        --todo-text: var(--primary-text-color, #212121);
        --todo-secondary-text: var(--secondary-text-color, #727272);
        --todo-divider: var(--divider-color, #e0e0e0);
        --todo-surface: var(--secondary-background-color, #f5f5f5);
        --todo-disabled: var(--disabled-text-color, #bdbdbd);
        --todo-error: var(--error-color, #db4437);
        --todo-success: var(--success-color, #43a047);
        --todo-radius: 8px;
      }
      ha-card { overflow: hidden; }
      .multi-columns { display: flex; gap: 0; align-items: flex-start; }
      .multi-columns .card-column { flex: 1; min-width: 240px; border-right: 1px solid var(--todo-divider); }
      .multi-columns .card-column:last-child { border-right: none; }
      @media (max-width: 600px) { .multi-columns { flex-direction: column; } .multi-columns .card-column { border-right: none; border-bottom: 1px solid var(--todo-divider); } .multi-columns .card-column:last-child { border-bottom: none; } }
      .card-column.drag-target { outline: 2px dashed var(--todo-primary); outline-offset: -2px; border-radius: var(--todo-radius); }
      .card-column { padding: 16px; }
      .header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; }
      .title { font-size: 24px; font-weight: 700; color: var(--todo-text); margin: 0; }
      .progress { font-size: 14px; color: var(--todo-secondary-text); }
      .add-task { display: flex; gap: 8px; margin-bottom: 16px; }
      .add-input {
        flex: 1; padding: 10px 14px; border: 1px solid var(--todo-divider);
        border-radius: var(--todo-radius); background: var(--todo-bg);
        color: var(--todo-text); font-size: 14px; outline: none; font-family: inherit;
      }
      .add-input:focus { border-color: var(--todo-primary); }
      .add-input::placeholder { color: var(--todo-disabled); }
      .add-btn {
        padding: 10px 20px; background: var(--todo-primary); color: #fff;
        border: none; border-radius: var(--todo-radius); font-size: 14px;
        font-weight: 500; cursor: pointer; white-space: nowrap; font-family: inherit;
      }
      .add-btn:hover { opacity: 0.9; }
      .filters { display: flex; gap: 4px; margin-bottom: 12px; align-items: center; }
      .filter-spacer { flex: 1; }
      .filter-btn {
        padding: 6px 16px; border: none; border-radius: 20px; background: transparent;
        color: var(--todo-secondary-text); font-size: 13px; cursor: pointer;
        font-family: inherit; transition: all 0.2s;
      }
      .filter-btn.active { background: var(--todo-primary); color: #fff; }
      .filter-btn:not(.active):hover { background: var(--todo-surface); }
      .sort-btn-wrapper { position: relative; }
      .sort-btn {
        padding: 5px 10px; border: 1px solid var(--todo-divider); border-radius: 20px;
        background: transparent; color: var(--todo-secondary-text); font-size: 12px;
        cursor: pointer; font-family: inherit; transition: all 0.2s; white-space: nowrap;
      }
      .sort-btn.active { border-color: var(--todo-primary); color: var(--todo-primary); }
      .sort-btn:hover { background: var(--todo-surface); }
      .sort-dropdown {
        position: absolute; right: 0; top: calc(100% + 4px); z-index: 20;
        background: var(--card-background-color, var(--todo-bg)); border: 1px solid var(--todo-divider);
        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); min-width: 150px; overflow: hidden;
      }
      .sort-dropdown.hidden { display: none; }
      .sort-option {
        padding: 9px 14px; cursor: pointer; font-size: 13px;
        color: var(--todo-text); transition: background 0.15s;
      }
      .sort-option:hover { background: var(--todo-surface); }
      .sort-option.active { color: var(--todo-primary); font-weight: 500; }
      .task-list { display: flex; flex-direction: column; gap: 6px; min-height: 40px; }
      .empty-state { text-align: center; padding: 24px; color: var(--todo-disabled); font-size: 14px; }
      .task {
        border: 1px solid var(--todo-divider); border-radius: var(--todo-radius);
        background: var(--todo-bg); transition: box-shadow 0.2s, border-color 0.2s;
      }
      .task.dragging { opacity: 0.4; }
      .task-main { display: flex; align-items: center; padding: 10px 12px; gap: 8px; min-height: 44px; }
      .task-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
      .drag-handle {
        cursor: grab; color: var(--todo-disabled); font-size: 16px;
        user-select: none; padding: 4px 2px; line-height: 1;
        touch-action: none;
      }
      .drag-handle.hidden { visibility: hidden; }
      .drag-handle:active { cursor: grabbing; }
      @media (pointer: coarse) {
        .drag-handle { padding: 8px 6px; font-size: 18px; }
      }
      .checkbox-container {
        position: relative; display: inline-flex; align-items: center;
        cursor: pointer; flex-shrink: 0;
      }
      .checkbox-container input { position: absolute; opacity: 0; cursor: pointer; height: 0; width: 0; }
      .checkmark {
        height: 20px; width: 20px; border: 2px solid var(--todo-divider);
        border-radius: 4px; transition: all 0.2s; display: flex;
        align-items: center; justify-content: center;
      }
      .checkbox-container:hover .checkmark { border-color: var(--todo-primary); }
      .checkbox-container input:checked ~ .checkmark { background: var(--todo-primary); border-color: var(--todo-primary); }
      .checkbox-container input:checked ~ .checkmark::after {
        content: ""; display: block; width: 5px; height: 9px;
        border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg); margin-top: -1px;
      }
      .checkbox-container.small .checkmark { height: 16px; width: 16px; }
      .checkbox-container.small input:checked ~ .checkmark::after { width: 4px; height: 7px; }
      .task-title {
        font-size: 14px; color: var(--todo-text); cursor: pointer;
        line-height: 1.3; word-break: break-word;
      }
      .task.completed .task-title { text-decoration: line-through; color: var(--todo-disabled); }
      .edit-title-input, .edit-sub-input {
        flex: 1; padding: 4px 8px; border: 1px solid var(--todo-primary);
        border-radius: 4px; font-size: 14px; background: var(--todo-bg);
        color: var(--todo-text); outline: none; font-family: inherit; min-width: 0;
      }
      .task-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
      .sub-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: var(--todo-surface); color: var(--todo-secondary-text); font-weight: 500;
      }
      .due-date {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: var(--todo-surface); color: var(--todo-secondary-text);
      }
      .due-date.today { background: rgba(255, 152, 0, 0.15); color: var(--warning-color, #ff9800); }
      .due-date.overdue { background: rgba(244, 67, 54, 0.15); color: var(--todo-error); font-weight: 500; }
      .priority-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
      }
      .priority-badge.pri-high { background: rgba(244, 67, 54, 0.15); color: var(--todo-error, #f44336); }
      .priority-badge.pri-medium { background: rgba(255, 152, 0, 0.15); color: var(--warning-color, #ff9800); }
      .priority-badge.pri-low { background: rgba(3, 169, 244, 0.15); color: var(--info-color, #03a9f4); }
      .priority-btn-row { display: flex; gap: 6px; }
      .priority-btn {
        flex: 1; padding: 5px 8px; border-radius: 4px; font-size: 12px; font-family: inherit;
        border: 1px solid var(--todo-divider); background: var(--todo-bg);
        color: var(--todo-secondary-text); cursor: pointer; transition: background 0.15s, color 0.15s, border-color 0.15s;
      }
      .priority-btn.pri-3.active { background: rgba(244, 67, 54, 0.2); color: var(--todo-error, #f44336); border-color: var(--todo-error, #f44336); }
      .priority-btn.pri-2.active { background: rgba(255, 152, 0, 0.2); color: var(--warning-color, #ff9800); border-color: var(--warning-color, #ff9800); }
      .priority-btn.pri-1.active { background: rgba(3, 169, 244, 0.2); color: var(--info-color, #03a9f4); border-color: var(--info-color, #03a9f4); }
      .recurrence-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: rgba(3, 169, 244, 0.15); color: var(--info-color, #03a9f4);
      }
      .assigned-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: rgba(156, 39, 176, 0.15); color: var(--accent-color, #9c27b0);
      }
      .tag-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: rgba(76, 175, 80, 0.15); color: var(--success-color, #4caf50);
        cursor: pointer; transition: all 0.2s;
      }
      .tag-badge:hover { opacity: 0.8; }
      .tag-badge.active { background: var(--success-color, #4caf50); color: #fff; }
      .reminder-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: rgba(255, 152, 0, 0.15); color: var(--warning-color, #ff9800);
      }
      .tag-chips { display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap; }
      .tag-chip {
        padding: 4px 12px; border: 1px solid rgba(76, 175, 80, 0.3); border-radius: 16px;
        background: transparent; color: var(--success-color, #4caf50); font-size: 12px;
        cursor: pointer; font-family: inherit; transition: all 0.2s;
      }
      .tag-chip:hover { background: rgba(76, 175, 80, 0.1); }
      .tag-chip.active { background: var(--success-color, #4caf50); color: #fff; border-color: var(--success-color, #4caf50); }
      .tag-list { display: flex; gap: 6px; flex-wrap: wrap; }
      .tag-item {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 2px 8px; border-radius: 10px;
        background: rgba(76, 175, 80, 0.15); color: var(--success-color, #4caf50);
        font-size: 12px;
      }
      .remove-tag-btn {
        background: none; border: none; color: var(--success-color, #4caf50);
        cursor: pointer; font-size: 14px; padding: 0 2px; line-height: 1; opacity: 0.7;
      }
      .remove-tag-btn:hover { opacity: 1; }
      .tag-input {
        padding: 6px 10px; border: 1px solid var(--todo-divider); border-radius: 4px;
        font-size: 13px; background: var(--todo-bg); color: var(--todo-text);
        font-family: inherit; outline: none; max-width: 200px;
      }
      .tag-input:focus { border-color: var(--success-color, #4caf50); }
      .person-select {
        width: 100%; padding: 6px 8px; border: 1px solid var(--todo-divider);
        border-radius: 4px; font-size: 13px; background: var(--todo-bg);
        color: var(--todo-text); font-family: inherit;
      }
      .recurrence-toggle-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
      .recurrence-mode-select { margin-bottom: 6px; }
      .recurrence-input-row { display: flex; align-items: center; gap: 8px; }
      .recurrence-prefix { font-size: 13px; color: var(--todo-secondary-text); white-space: nowrap; }
      .recurrence-value {
        width: 60px; padding: 6px 8px; border: 1px solid var(--todo-divider);
        border-radius: 4px; font-size: 13px; background: var(--todo-bg);
        color: var(--todo-text); font-family: inherit; text-align: center;
      }
      .recurrence-select {
        flex: 1; padding: 6px 8px; border: 1px solid var(--todo-divider);
        border-radius: 4px; font-size: 13px; background: var(--todo-bg);
        color: var(--todo-text); font-family: inherit;
      }
      .recurrence-value:disabled, .recurrence-select:disabled { opacity: 0.5; }
      .recurrence-weekday-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
      .weekday-label {
        display: flex; flex-direction: column; align-items: center; gap: 3px;
        font-size: 12px; color: var(--todo-secondary-text); cursor: pointer; user-select: none;
      }
      .weekday-label input[type="checkbox"] { display: none; }
      .weekday-label span {
        padding: 4px 7px; border-radius: 4px; border: 1px solid var(--todo-divider);
        background: var(--todo-bg); transition: background 0.15s, color 0.15s;
      }
      .weekday-label input[type="checkbox"]:checked + span {
        background: var(--primary-color, #03a9f4); color: #fff; border-color: var(--primary-color, #03a9f4);
      }
      .weekday-label input[type="checkbox"]:disabled + span { opacity: 0.5; cursor: default; }
      .reminder-row { display: flex; gap: 6px; align-items: center; }
      .reminder-select {
        flex: 1; padding: 6px 8px; border: 1px solid var(--todo-divider);
        border-radius: 4px; font-size: 13px; background: var(--todo-bg);
        color: var(--todo-text); font-family: inherit;
      }
      .reminder-remove {
        background: none; border: none; color: var(--todo-secondary-text);
        cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 4px; line-height: 1;
      }
      .reminder-remove:hover { color: var(--todo-error); background: rgba(244, 67, 54, 0.15); }
      .add-reminder-btn {
        background: none; border: none; color: var(--warning-color, #ff9800); cursor: pointer;
        font-size: 13px; padding: 6px 0; text-align: left; font-family: inherit;
      }
      .add-reminder-btn:hover { text-decoration: underline; }
      .expand-btn {
        background: none; border: none; color: var(--todo-secondary-text);
        cursor: pointer; font-size: 10px; padding: 6px; border-radius: 4px;
        line-height: 1; flex-shrink: 0;
      }
      .expand-btn:hover { background: var(--todo-surface); }
      .task-details {
        padding: 8px 12px 12px 44px; border-top: 1px solid var(--todo-divider);
        display: flex; flex-direction: column; gap: 12px;
      }
      .detail-section { display: flex; flex-direction: column; gap: 6px; }
      .detail-label {
        font-size: 11px; font-weight: 600; text-transform: uppercase;
        color: var(--todo-secondary-text); letter-spacing: 0.5px;
      }
      .due-input-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
      .date-input {
        padding: 6px 10px; border: 1px solid var(--todo-divider); border-radius: 4px;
        font-size: 13px; background: var(--todo-bg); color: var(--todo-text);
        font-family: inherit; flex: 1; min-width: 130px;
      }
      .time-input {
        padding: 6px 10px; border: 1px solid var(--todo-divider); border-radius: 4px;
        font-size: 13px; background: var(--todo-bg); color: var(--todo-text);
        font-family: inherit; width: 100px;
      }
      .time-input:disabled { opacity: 0.4; }
      .notes-input {
        padding: 8px 10px; border: 1px solid var(--todo-divider); border-radius: 4px;
        font-size: 13px; background: var(--todo-surface); color: var(--todo-text);
        resize: vertical; min-height: 40px; font-family: inherit; outline: none;
      }
      .notes-input:focus { border-color: var(--todo-primary); background: var(--todo-bg); }
      .sub-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
      .sub-title {
        flex: 1; font-size: 13px; color: var(--todo-text); cursor: default;
        min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
      }
      .sub-title.completed { text-decoration: line-through; color: var(--todo-disabled); }
      .delete-sub-btn {
        background: none; border: none; color: var(--todo-disabled); cursor: pointer;
        font-size: 16px; padding: 2px 6px; border-radius: 4px; line-height: 1; flex-shrink: 0;
      }
      .delete-sub-btn:hover { color: var(--todo-error); background: rgba(244, 67, 54, 0.15); }
      .add-sub-btn {
        background: none; border: none; color: var(--todo-primary); cursor: pointer;
        font-size: 13px; padding: 6px 0; text-align: left; font-family: inherit;
      }
      .add-sub-btn:hover { text-decoration: underline; }
      .detail-actions { display: flex; justify-content: flex-end; padding-top: 4px; }
      .delete-task-btn {
        background: none; border: 1px solid var(--todo-error); color: var(--todo-error);
        padding: 6px 14px; border-radius: 4px; font-size: 12px; cursor: pointer; font-family: inherit;
      }
      .delete-task-btn:hover { background: rgba(244, 67, 54, 0.15); }
      .toast-error {
        position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
        background: var(--todo-error, #db4437); color: #fff; padding: 10px 20px;
        border-radius: 8px; font-size: 13px; z-index: 999; animation: fadeIn 0.3s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      }
      @keyframes fadeIn { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

      /* Compact mode overrides */
      .compact { padding: 10px; }
      .compact .header { margin-bottom: 10px; }
      .compact .title { font-size: 18px; }
      .compact .progress { font-size: 12px; }
      .compact .add-task { margin-bottom: 10px; }
      .compact .add-input { padding: 6px 10px; font-size: 13px; }
      .compact .add-btn { padding: 6px 14px; font-size: 13px; }
      .compact .filters { margin-bottom: 8px; }
      .compact .filter-btn { padding: 4px 12px; font-size: 12px; }
      .compact .tag-chips { margin-bottom: 8px; gap: 3px; }
      .compact .tag-chip { padding: 2px 8px; font-size: 11px; }
      .compact .task-list { gap: 3px; }
      .compact .task-main { padding: 6px 8px; gap: 6px; min-height: 32px; }
      .compact .task-title { font-size: 13px; }
      .compact .task-meta { gap: 4px; }
      .compact .sub-badge, .compact .due-date, .compact .priority-badge, .compact .recurrence-badge,
      .compact .assigned-badge, .compact .tag-badge, .compact .reminder-badge { font-size: 10px; padding: 1px 6px; }
      .compact .checkmark { height: 16px; width: 16px; }
      .compact .checkbox-container input:checked ~ .checkmark::after { width: 4px; height: 7px; }
      .compact .expand-btn { padding: 4px; font-size: 9px; }
      .compact .drag-handle { font-size: 14px; padding: 2px 1px; }
      .compact .empty-state { padding: 16px; font-size: 13px; }
      .compact .task-details { padding: 8px 10px; }
    `;
  }

  // --- Card config ---

  static getConfigElement() {
    return document.createElement("home-tasks-card-editor");
  }

  static getStubConfig() {
    return { columns: [{}] };
  }

  getCardSize() {
    return 3 + this._columns.reduce((sum, cs) => sum + cs.tasks.length, 0);
  }
}

/**
 * Card Editor — uses safe DOM construction
 */
class HomeTasksCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { columns: [{}] };
    this._hass = null;
    this._lists = [];
    this._listsLoaded = false;
    this._editorTab = 0;
    this._editorCodeMode = {};  // { tabIdx: bool }
    this._editorCodeText = {};  // { tabIdx: string }
    this._editorCodeError = {}; // { tabIdx: string }
  }

  _t(key, ...args) {
    const lang = (this._hass && this._hass.language) || "en";
    const str = (_TRANSLATIONS[lang] || _TRANSLATIONS.en)[key] || _TRANSLATIONS.en[key] || key;
    return args.length ? str.replace(/\{(\d+)\}/g, (_, i) => args[i] ?? "") : str;
  }

  _el(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
      if (key === "className") el.className = val;
      else if (key === "textContent") el.textContent = val;
      else if (key === "value") el.value = val;
      else if (key === "selected") { if (val) el.selected = true; }
      else if (key === "placeholder") el.placeholder = val;
      else if (key === "type") el.type = val;
      else if (key === "id") el.id = val;
      else if (key === "checked") el.checked = val;
      else el.setAttribute(key, val);
    }
    for (const child of children) {
      if (typeof child === "string") el.appendChild(document.createTextNode(child));
      else if (child) el.appendChild(child);
    }
    return el;
  }

  setConfig(config) {
    // Normalize old single-list format
    // Keep HA card-level keys (type, etc.) at root, not inside column objects
    if (config.list_id && !config.columns) {
      const { type, columns: _c, ...colConfig } = config;
      config = { ...(type ? { type } : {}), columns: [colConfig] };
    }
    if (!config.columns || !Array.isArray(config.columns) || config.columns.length === 0) {
      config = { ...config, columns: [{}] };
    }
    // Strip any stray type keys from column objects
    config = {
      ...config,
      columns: config.columns.map(({ type: _t, ...col }) => col),
    };
    }
    this._config = { ...config };

    // Clamp active tab
    if (this._editorTab >= this._config.columns.length) {
      this._editorTab = this._config.columns.length - 1;
    }

    if (this._listsLoaded) {
      const active = this.shadowRoot?.activeElement;
      if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA")) return;
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._listsLoaded) {
      this._loadLists();
    }
  }

  async _loadLists() {
    try {
      const result = await this._hass.callWS({ type: "home_tasks/get_lists" });
      if (result && Array.isArray(result.lists)) {
        this._lists = result.lists;
        this._listsLoaded = true;
        // Auto-select first list for first column if none set
        if (!this._config.columns[0]?.list_id && this._lists.length > 0) {
          const newCols = [...this._config.columns];
          newCols[0] = { ...newCols[0], list_id: this._lists[0].id };
          this._config = { ...this._config, columns: newCols };
          this._fireChanged();
        }
        this._render();
      }
    } catch (e) {
      // Integration might not be loaded yet
    }
  }

  _clearCodeState() {
    this._editorCodeMode = {};
    this._editorCodeText = {};
    this._editorCodeError = {};
  }

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; }
      .editor { display: flex; flex-direction: column; gap: 0; padding: 16px 0; }
      .editor-tabs { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
      .editor-tab {
        min-width: 32px; padding: 4px 12px; border: 1px solid var(--divider-color);
        border-radius: 4px; background: transparent; cursor: pointer; font-size: 13px;
        font-family: inherit; color: var(--primary-text-color);
      }
      .editor-tab.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }
      .editor-tab:hover:not(.active) { background: var(--secondary-background-color); }
      .editor-col-controls { display: flex; gap: 6px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
      .editor-col-btn {
        padding: 4px 10px; border: 1px solid var(--divider-color);
        border-radius: 4px; background: transparent; cursor: pointer; font-size: 13px;
        font-family: inherit; color: var(--primary-text-color);
      }
      .editor-col-btn:hover { background: var(--secondary-background-color); }
      .editor-col-btn.active { background: var(--secondary-background-color); border-color: var(--primary-color); color: var(--primary-color); }
      .editor-col-btn-del { color: var(--error-color, #db4437); border-color: rgba(219,68,55,0.4); }
      .editor-col-btn-del:hover { background: rgba(219, 68, 55, 0.1); }
      .visual-editor { display: flex; flex-direction: column; gap: 16px; }
      .field { display: flex; flex-direction: column; gap: 4px; }
      label { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: 0.5px; }
      select, input[type="text"] { padding: 8px 12px; border: 1px solid var(--divider-color); border-radius: 4px; font-size: 14px; background: var(--card-background-color); color: var(--primary-text-color); font-family: inherit; }
      .hint { font-size: 12px; color: var(--secondary-text-color); font-style: italic; }
      .toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; }
      .toggle-label { font-size: 14px; color: var(--primary-text-color); }
      .toggle-row input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; accent-color: var(--primary-color); }
      .code-editor-wrapper { display: flex; flex-direction: column; gap: 6px; }
      .code-editor-textarea {
        width: 100%; min-height: 320px; padding: 10px; border: 1px solid var(--divider-color);
        border-radius: 4px; font-family: monospace; font-size: 12px;
        background: var(--secondary-background-color); color: var(--primary-text-color);
        box-sizing: border-box; resize: vertical; outline: none;
      }
      .code-editor-textarea:focus { border-color: var(--primary-color); }
      .code-editor-error { color: var(--error-color, #db4437); font-size: 12px; }
    `;
    root.appendChild(style);

    const cols = this._config.columns;
    const activeTab = Math.min(this._editorTab, cols.length - 1);

    // Tab bar
    const tabBar = this._el("div", { className: "editor-tabs" });
    for (let i = 0; i < cols.length; i++) {
      const colName = cols[i].title ||
        this._lists.find(l => l.id === cols[i].list_id)?.name ||
        String(i + 1);
      const tab = this._el("button", {
        className: "editor-tab" + (i === activeTab ? " active" : ""),
        textContent: String(i + 1),
        title: colName,
      });
      tab.addEventListener("click", () => {
        this._editorTab = i;
        this._render();
      });
      tabBar.appendChild(tab);
    }
    const addTabBtn = this._el("button", {
      className: "editor-tab",
      textContent: "+",
      title: this._t("ed_add_column"),
    });
    addTabBtn.addEventListener("click", () => {
      this._clearCodeState();
      const newCols = [...cols, {}];
      this._config = { ...this._config, columns: newCols };
      this._editorTab = newCols.length - 1;
      this._fireChanged();
      this._render();
    });
    tabBar.appendChild(addTabBtn);

    // Column controls
    const isCodeMode = this._editorCodeMode[activeTab] === true;
    const controls = this._el("div", { className: "editor-col-controls" });

    // Code/visual toggle
    const codeBtn = this._el("button", {
      className: "editor-col-btn" + (isCodeMode ? " active" : ""),
      textContent: "{}",
      title: isCodeMode ? this._t("ed_visual_editor") : this._t("ed_code_editor"),
    });
    codeBtn.addEventListener("click", () => {
      if (!isCodeMode) {
        this._editorCodeText[activeTab] = JSON.stringify(cols[activeTab], null, 2);
      }
      this._editorCodeMode[activeTab] = !isCodeMode;
      this._render();
    });
    controls.appendChild(codeBtn);

    if (cols.length > 1) {
      if (activeTab > 0) {
        const leftBtn = this._el("button", { className: "editor-col-btn", textContent: "\u2190", title: this._t("ed_move_left") });
        leftBtn.addEventListener("click", () => {
          this._clearCodeState();
          const newCols = [...cols];
          [newCols[activeTab - 1], newCols[activeTab]] = [newCols[activeTab], newCols[activeTab - 1]];
          this._config = { ...this._config, columns: newCols };
          this._editorTab = activeTab - 1;
          this._fireChanged();
          this._render();
        });
        controls.appendChild(leftBtn);
      }
      if (activeTab < cols.length - 1) {
        const rightBtn = this._el("button", { className: "editor-col-btn", textContent: "\u2192", title: this._t("ed_move_right") });
        rightBtn.addEventListener("click", () => {
          this._clearCodeState();
          const newCols = [...cols];
          [newCols[activeTab], newCols[activeTab + 1]] = [newCols[activeTab + 1], newCols[activeTab]];
          this._config = { ...this._config, columns: newCols };
          this._editorTab = activeTab + 1;
          this._fireChanged();
          this._render();
        });
        controls.appendChild(rightBtn);
      }
      const dupBtn = this._el("button", { className: "editor-col-btn", textContent: "\u29C8", title: this._t("ed_duplicate") });
      dupBtn.addEventListener("click", () => {
        this._clearCodeState();
        const newCols = [...cols];
        newCols.splice(activeTab + 1, 0, { ...cols[activeTab] });
        this._config = { ...this._config, columns: newCols };
        this._editorTab = activeTab + 1;
        this._fireChanged();
        this._render();
      });
      controls.appendChild(dupBtn);

      const delBtn = this._el("button", { className: "editor-col-btn editor-col-btn-del", textContent: "\uD83D\uDDD1", title: this._t("ed_delete_column") });
      delBtn.addEventListener("click", () => {
        this._clearCodeState();
        const newCols = cols.filter((_, i) => i !== activeTab);
        this._config = { ...this._config, columns: newCols };
        this._editorTab = Math.min(activeTab, newCols.length - 1);
        this._fireChanged();
        this._render();
      });
      controls.appendChild(delBtn);
    }

    // Tab content
    const tabContent = isCodeMode
      ? this._buildCodeEditor(activeTab)
      : this._buildVisualEditor(activeTab);

    const editor = this._el("div", { className: "editor" }, [tabBar, controls, tabContent]);
    root.appendChild(editor);
  }

  _buildCodeEditor(tabIdx) {
    const col = this._config.columns[tabIdx];
    const text = this._editorCodeText[tabIdx] !== undefined
      ? this._editorCodeText[tabIdx]
      : JSON.stringify(col, null, 2);

    const textarea = this._el("textarea", { className: "code-editor-textarea" });
    textarea.value = text;

    textarea.addEventListener("input", () => {
      this._editorCodeText[tabIdx] = textarea.value;
      this._editorCodeError[tabIdx] = "";
    });

    textarea.addEventListener("blur", () => {
      try {
        const parsed = JSON.parse(textarea.value);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          throw new Error("Must be a JSON object");
        }
        const newCols = [...this._config.columns];
        newCols[tabIdx] = parsed;
        this._config = { ...this._config, columns: newCols };
        this._editorCodeText[tabIdx] = textarea.value;
        this._editorCodeError[tabIdx] = "";
        this._fireChanged();
      } catch (e) {
        this._editorCodeError[tabIdx] = e.message;
      }
      this._render();
    });

    const children = [textarea];
    const errMsg = this._editorCodeError[tabIdx];
    if (errMsg) {
      children.push(this._el("span", { className: "code-editor-error", textContent: errMsg }));
    }
    return this._el("div", { className: "code-editor-wrapper" }, children);
  }

  _buildVisualEditor(tabIdx) {
    const col = this._config.columns[tabIdx] || {};

    const updateCol = (updates) => {
      const newCols = [...this._config.columns];
      newCols[tabIdx] = { ...newCols[tabIdx], ...updates };
      this._config = { ...this._config, columns: newCols };
      this._fireChanged();
    };

    // List select
    const listSelect = this._el("select", { id: `list-select-${tabIdx}` });
    for (const l of this._lists) {
      const option = this._el("option", {
        value: l.id,
        selected: l.id === col.list_id,
        textContent: l.name,
      });
      listSelect.appendChild(option);
    }
    listSelect.addEventListener("change", () => updateCol({ list_id: listSelect.value }));

    // Title input
    const titleInput = this._el("input", {
      type: "text",
      id: `title-input-${tabIdx}`,
      value: col.title || "",
      placeholder: this._t("ed_title_placeholder"),
    });
    titleInput.addEventListener("input", () => updateCol({ title: titleInput.value }));

    // Default filter select
    const defaultFilterSelect = this._el("select");
    for (const [val, key] of [["all", "filter_all"], ["open", "filter_open"], ["done", "filter_done"]]) {
      const opt = this._el("option", { value: val, textContent: this._t(key) });
      if ((col.default_filter || "all") === val) opt.selected = true;
      defaultFilterSelect.appendChild(opt);
    }
    defaultFilterSelect.addEventListener("change", () => updateCol({ default_filter: defaultFilterSelect.value }));

    // Default sort select
    const defaultSortSelect = this._el("select");
    for (const [val, key] of [
      ["manual", "sort_manual"], ["due", "sort_due"], ["priority", "sort_priority"],
      ["title", "sort_title"], ["person", "sort_person"],
    ]) {
      const opt = this._el("option", { value: val, textContent: this._t(key) });
      if ((col.default_sort || "manual") === val) opt.selected = true;
      defaultSortSelect.appendChild(opt);
    }
    defaultSortSelect.addEventListener("change", () => updateCol({ default_sort: defaultSortSelect.value }));

    // Toggle helper
    const makeToggle = (id, labelKey, configKey, defaultOn = true) => {
      const cb = this._el("input", {
        type: "checkbox",
        id: `${id}-${tabIdx}`,
        checked: col[configKey] !== false ? defaultOn : !defaultOn,
      });
      // More precise: default true means checked when undefined
      cb.checked = defaultOn ? col[configKey] !== false : col[configKey] === true;
      cb.addEventListener("change", () => updateCol({ [configKey]: cb.checked }));
      return this._el("div", { className: "toggle-row" }, [
        this._el("span", { className: "toggle-label", textContent: this._t(labelKey) }),
        cb,
      ]);
    };

    const hint = this._el("span", { className: "hint", textContent: this._t("ed_hint") });

    return this._el("div", { className: "visual-editor" }, [
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: this._t("ed_list") }),
        listSelect,
        hint,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: this._t("ed_title") }),
        titleInput,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: this._t("ed_default_filter") }),
        defaultFilterSelect,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: this._t("ed_default_sort") }),
        defaultSortSelect,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: this._t("ed_display") }),
        makeToggle("compact", "ed_compact", "compact", false),
        makeToggle("show-title", "ed_show_title", "show_title", true),
        makeToggle("show-progress", "ed_show_progress", "show_progress", true),
        makeToggle("show-sort", "ed_show_sort", "show_sort", true),
        makeToggle("show-notes", "ed_show_notes", "show_notes", true),
        makeToggle("show-sub-items", "ed_show_sub_items", "show_sub_items", true),
        makeToggle("show-person", "ed_show_person", "show_assigned_person", true),
        makeToggle("show-priority", "ed_show_priority", "show_priority", true),
        makeToggle("show-tags", "ed_show_tags", "show_tags", true),
        makeToggle("show-due-date", "ed_show_due_date", "show_due_date", true),
        makeToggle("show-reminders", "ed_show_reminders", "show_reminders", true),
        makeToggle("show-recurrence", "ed_show_recurrence", "show_recurrence", true),
        makeToggle("auto-delete", "ed_auto_delete", "auto_delete_completed", false),
      ]),
    ]);
  }

  _fireChanged() {
    const event = new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

// Register elements — wait for HA's scoped custom element registry polyfill
// before calling customElements.define. The polyfill replaces the native
// define() with a JS wrapper; we detect this to avoid registering too early
// (which puts the element in the native registry where the polyfill can't
// find it, causing "Custom element not found" in Firefox/Safari/iPad).
const _htRegister = () => {
  try { customElements.define("home-tasks-card", HomeTasksCard); } catch(_) {}
  try { customElements.define("home-tasks-card-editor", HomeTasksCardEditor); } catch(_) {}
};

const _htIsPolyfillReady = () =>
  !customElements.define.toString().includes("[native code]");

if (_htIsPolyfillReady()) {
  _htRegister();
} else {
  let _htAttempts = 0;
  const _htPoll = setInterval(() => {
    _htAttempts++;
    if (_htIsPolyfillReady() || _htAttempts > 200) {
      clearInterval(_htPoll);
      _htRegister();
    }
  }, 50);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "home-tasks-card",
  name: "Home Tasks",
  description: "A feature-rich todo list with drag & drop, sub-items, notes, and due dates.",
  preview: true,
});
