/**
 * Home Tasks Card for Home Assistant
 * A feature-rich todo list with drag & drop, sub-items, notes, and due dates.
 *
 * Security: All user-controlled content is set via textContent or DOM properties,
 * never via innerHTML with unsanitized data.
 */
console.info("%c HOME-TASKS-CARD %c v3.0.0 ", "color: white; background: #03a9f4; font-weight: bold;", "color: #03a9f4; background: white; font-weight: bold;");

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
    due_date: "Due date",
    notes: "Notes",
    notes_placeholder: "Add notes here",
    sub_items: "Sub-items",
    add_sub_item: "+ Add sub-item",
    recurrence: "Recurrence",
    recurrence_enabled: "Enabled",
    recurrence_every: "Every",
    rec_hours: "Hours", rec_days: "Days", rec_weeks: "Weeks", rec_months: "Months",
    rec_short_h: "h", rec_short_d: "d", rec_short_w: "w", rec_short_m: "mo",
    rec_hourly: "Hourly", rec_daily: "Daily", rec_weekly: "Weekly", rec_monthly: "Monthly",
    assigned_to: "Assigned to",
    nobody: "\u2013 Nobody \u2013",
    delete_task: "Delete task",
    delete_sub: "Delete",
    ed_list: "List",
    ed_title: "Title (optional)",
    ed_title_placeholder: "Default: List name",
    ed_display: "Display",
    ed_show_title: "Show title",
    ed_show_progress: "Show progress",
    ed_show_due_date: "Show due date",
    ed_show_notes: "Show notes",
    ed_show_recurrence: "Show recurrence",
    ed_show_sub_items: "Show sub-items",
    ed_show_person: "Show assigned person",
    ed_auto_delete: "Delete completed tasks immediately",
    ed_show_tags: "Show tags",
    ed_hint: "New lists can be created under Settings \u2192 Integrations \u2192 Home Tasks.",
    tags: "Tags",
    add_tag: "+ Add tag",
    tag_placeholder: "New tag...",
    remove_tag: "Remove",
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
    due_date: "F\u00e4lligkeitsdatum",
    notes: "Notizen",
    notes_placeholder: "Hier kannst du Notizen hinzuf\u00fcgen",
    sub_items: "Unterpunkte",
    add_sub_item: "+ Unterpunkt hinzuf\u00fcgen",
    recurrence: "Wiederholung",
    recurrence_enabled: "Aktiviert",
    recurrence_every: "Alle",
    rec_hours: "Stunden", rec_days: "Tage", rec_weeks: "Wochen", rec_months: "Monate",
    rec_short_h: "Std.", rec_short_d: "T.", rec_short_w: "Wo.", rec_short_m: "Mon.",
    rec_hourly: "St\u00fcndl.", rec_daily: "T\u00e4glich", rec_weekly: "W\u00f6chentl.", rec_monthly: "Monatl.",
    assigned_to: "Zugewiesen an",
    nobody: "\u2013 Niemand \u2013",
    delete_task: "Aufgabe l\u00f6schen",
    delete_sub: "L\u00f6schen",
    ed_list: "Liste",
    ed_title: "Titel (optional)",
    ed_title_placeholder: "Standard: Listenname",
    ed_display: "Anzeige",
    ed_show_title: "Titel anzeigen",
    ed_show_progress: "Fortschritt anzeigen",
    ed_show_due_date: "F\u00e4lligkeitsdatum anzeigen",
    ed_show_notes: "Notizen anzeigen",
    ed_show_recurrence: "Wiederholung anzeigen",
    ed_show_sub_items: "Unterpunkte anzeigen",
    ed_show_person: "Zugewiesene Person anzeigen",
    ed_auto_delete: "Erledigte Aufgaben sofort l\u00f6schen",
    ed_show_tags: "Tags anzeigen",
    ed_hint: "Neue Listen k\u00f6nnen unter Einstellungen \u2192 Integrationen \u2192 Home Tasks erstellt werden.",
    tags: "Tags",
    add_tag: "+ Tag hinzuf\u00fcgen",
    tag_placeholder: "Neues Tag...",
    remove_tag: "Entfernen",
  },
};

class HomeTasksCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._tasks = [];
    this._lists = [];
    this._filter = "all"; // all, open, done
    this._expandedTasks = new Set();
    this._editingTaskId = null;
    this._editingSubItemId = null;
    this._draggedTaskId = null;
    this._dragOverTaskId = null;
    this._touchClone = null;
    this._touchStartTimer = null;
    this._touchBound = {};
    this._newTaskTitle = "";
    this._tagFilter = null;
    this._initialized = false;
  }

  _t(key, ...args) {
    const lang = (this._hass && this._hass.language) || "en";
    const str = (_TRANSLATIONS[lang] || _TRANSLATIONS.en)[key] || _TRANSLATIONS.en[key] || key;
    return args.length ? str.replace(/\{(\d+)\}/g, (_, i) => args[i] ?? "") : str;
  }

  setConfig(config) {
    this._config = config;
    if (this._initialized) {
      this._loadTasks();
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
      } else if (key.startsWith("data-")) {
        el.setAttribute(key, val);
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
      if (!this._config.list_id && this._lists.length > 0) {
        this._config = { ...this._config, list_id: this._lists[0].id };
      }
    }
    await this._loadTasks();
  }

  async _loadTasks() {
    if (!this._config.list_id) {
      this._tasks = [];
      this._render();
      return;
    }
    const result = await this._callWs("home_tasks/get_tasks", {
      list_id: this._config.list_id,
    });
    if (result && Array.isArray(result.tasks)) {
      this._tasks = result.tasks;
    }
    this._render();
  }

  async _addTask() {
    const title = this._newTaskTitle.trim();
    if (!title || !this._config.list_id) return;
    const result = await this._callWs("home_tasks/add_task", {
      list_id: this._config.list_id,
      title,
    });
    if (result) {
      this._newTaskTitle = "";
      await this._loadTasks();
    }
  }

  async _toggleTask(taskId, completed) {
    const newCompleted = !completed;
    const task = this._tasks.find(t => t.id === taskId);
    const hasRecurrence = task && task.recurrence_enabled && task.recurrence_unit;
    if (newCompleted && this._config.auto_delete_completed && !hasRecurrence) {
      await this._callWs("home_tasks/delete_task", {
        list_id: this._config.list_id,
        task_id: taskId,
      });
    } else {
      await this._callWs("home_tasks/update_task", {
        list_id: this._config.list_id,
        task_id: taskId,
        completed: newCompleted,
      });
    }
    await this._loadTasks();
  }

  async _updateTaskTitle(taskId, title) {
    if (!title.trim()) return;
    const result = await this._callWs("home_tasks/update_task", {
      list_id: this._config.list_id,
      task_id: taskId,
      title: title.trim(),
    });
    if (result) {
      this._editingTaskId = null;
      await this._loadTasks();
    }
  }

  async _updateTaskNotes(taskId, notes) {
    await this._callWs("home_tasks/update_task", {
      list_id: this._config.list_id,
      task_id: taskId,
      notes,
    });
  }

  async _updateTaskDueDate(taskId, dueDate) {
    await this._callWs("home_tasks/update_task", {
      list_id: this._config.list_id,
      task_id: taskId,
      due_date: dueDate || null,
    });
    await this._loadTasks();
  }

  async _deleteTask(taskId) {
    await this._callWs("home_tasks/delete_task", {
      list_id: this._config.list_id,
      task_id: taskId,
    });
    this._expandedTasks.delete(taskId);
    await this._loadTasks();
  }

  async _addSubItem(taskId) {
    const result = await this._callWs("home_tasks/add_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      title: "Neuer Unterpunkt",
    });
    if (result) {
      this._editingSubItemId = result.id;
    }
    await this._loadTasks();
  }

  async _toggleSubItem(taskId, subItemId, completed) {
    await this._callWs("home_tasks/update_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      sub_item_id: subItemId,
      completed: !completed,
    });
    await this._loadTasks();
  }

  async _updateSubItemTitle(taskId, subItemId, title) {
    if (!title.trim()) return;
    const result = await this._callWs("home_tasks/update_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      sub_item_id: subItemId,
      title: title.trim(),
    });
    if (result) {
      this._editingSubItemId = null;
      await this._loadTasks();
    }
  }

  async _deleteSubItem(taskId, subItemId) {
    await this._callWs("home_tasks/delete_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      sub_item_id: subItemId,
    });
    await this._loadTasks();
  }

  async _reorderTasks(taskIds) {
    await this._callWs("home_tasks/reorder_tasks", {
      list_id: this._config.list_id,
      task_ids: taskIds,
    });
    await this._loadTasks();
  }

  // --- Filter ---

  get _filteredTasks() {
    let tasks;
    switch (this._filter) {
      case "open":
        tasks = this._tasks.filter((t) => !t.completed);
        break;
      case "done":
        tasks = this._tasks.filter((t) => t.completed);
        break;
      default:
        tasks = this._tasks;
    }
    if (this._tagFilter) {
      tasks = tasks.filter((t) => t.tags && t.tags.includes(this._tagFilter));
    }
    return tasks;
  }

  // --- Helpers ---

  _getCompletedCount() {
    return this._tasks.filter((t) => t.completed).length;
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

  _formatDueDate(dueDate) {
    if (!dueDate) return "";
    const date = new Date(dueDate + "T00:00:00");
    const lang = (this._hass && this._hass.language) || "en";
    return date.toLocaleDateString(lang, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  _getListName() {
    if (this._config.title) return this._config.title;
    const list = this._lists.find((l) => l.id === this._config.list_id);
    return list ? list.name : this._t("my_tasks");
  }

  // --- Render (DOM-based, no innerHTML with user data) ---

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    // Styles (static, no user data)
    const style = document.createElement("style");
    style.textContent = this._getStyles();
    root.appendChild(style);

    const card = this._el("ha-card", {}, [
      this._buildCardContent(),
    ]);
    root.appendChild(card);
  }

  _buildCardContent() {
    const completedCount = this._getCompletedCount();
    const totalCount = this._tasks.length;
    const filteredTasks = this._filteredTasks;

    // Header
    const showTitle = this._config.show_title !== false;
    const showProgress = this._config.show_progress !== false;
    const headerChildren = [];
    if (showTitle) {
      headerChildren.push(this._el("h1", { className: "title", textContent: this._getListName() }));
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
      value: this._newTaskTitle,
    });
    addInput.addEventListener("input", (e) => {
      this._newTaskTitle = e.target.value;
    });
    addInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._addTask();
    });

    const addBtn = this._el("button", {
      className: "add-btn",
      textContent: "+",
    });
    addBtn.addEventListener("click", () => this._addTask());

    const addTask = this._el("div", { className: "add-task" }, [addInput, addBtn]);

    // Filters (hidden when auto-delete is on)
    const hideFilters = this._config.auto_delete_completed === true;
    const filters = hideFilters ? null : this._el("div", { className: "filters" }, [
      this._buildFilterBtn(this._t("filter_all"), "all"),
      this._buildFilterBtn(this._t("filter_open"), "open"),
      this._buildFilterBtn(this._t("filter_done"), "done"),
    ]);

    // Task list
    const taskListChildren = [];
    if (filteredTasks.length === 0) {
      taskListChildren.push(
        this._el("div", { className: "empty-state", textContent: this._t("empty") })
      );
    }
    for (const task of filteredTasks) {
      taskListChildren.push(this._buildTask(task));
    }
    const taskList = this._el("div", { className: "task-list" }, taskListChildren);

    // Tag chips (filter by tag)
    let tagChips = null;
    if (this._config.show_tags !== false) {
      const allTags = new Set();
      for (const t of this._tasks) {
        for (const tag of (t.tags || [])) allTags.add(tag);
      }
      if (allTags.size > 0) {
        const chipChildren = [];
        for (const tag of [...allTags].sort()) {
          const isActive = this._tagFilter === tag;
          const chip = this._el("button", {
            className: "tag-chip" + (isActive ? " active" : ""),
            textContent: "#" + tag,
          });
          chip.addEventListener("click", () => {
            this._tagFilter = isActive ? null : tag;
            this._render();
          });
          chipChildren.push(chip);
        }
        tagChips = this._el("div", { className: "tag-chips" }, chipChildren);
      }
    }

    const children = [];
    if (header) children.push(header);
    children.push(addTask);
    if (filters) children.push(filters);
    if (tagChips) children.push(tagChips);
    children.push(taskList);
    return this._el("div", { className: "card-content" }, children);
  }

  _buildFilterBtn(label, value) {
    const btn = this._el("button", {
      className: `filter-btn${this._filter === value ? " active" : ""}`,
      textContent: label,
    });
    btn.addEventListener("click", () => {
      this._filter = value;
      this._render();
    });
    return btn;
  }

  _buildTask(task) {
    const isExpanded = this._expandedTasks.has(task.id);
    const isEditing = this._editingTaskId === task.id;

    let className = "task";
    if (task.completed) className += " completed";

    const taskEl = this._el("div", { className, draggable: true });
    taskEl.dataset.taskId = task.id;

    // Main row
    const mainChildren = [];

    // Drag handle
    const dragHandle = this._el("span", { className: "drag-handle", title: this._t("drag_handle"), textContent: "\u2237" });
    mainChildren.push(dragHandle);

    // Checkbox
    const checkbox = this._el("input", { type: "checkbox", checked: task.completed });
    checkbox.addEventListener("change", () => this._toggleTask(task.id, task.completed));
    const checkmark = this._el("span", { className: "checkmark" });
    const label = this._el("label", { className: "checkbox-container" }, [checkbox, checkmark]);
    mainChildren.push(label);

    // Content wrapper (title + meta in column layout)
    const contentChildren = [];

    // Title (editable or display)
    if (isEditing) {
      const editInput = this._el("input", {
        type: "text",
        className: "edit-title-input",
        value: task.title,
      });
      editInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this._updateTaskTitle(task.id, editInput.value);
        else if (e.key === "Escape") { this._editingTaskId = null; this._render(); }
      });
      editInput.addEventListener("blur", () => this._updateTaskTitle(task.id, editInput.value));
      contentChildren.push(editInput);
      setTimeout(() => { editInput.focus(); editInput.select(); }, 0);
    } else {
      const titleSpan = this._el("span", { className: "task-title", textContent: task.title });
      titleSpan.addEventListener("click", () => {
        if (this._expandedTasks.has(task.id)) this._expandedTasks.delete(task.id);
        else this._expandedTasks.add(task.id);
        this._render();
      });
      titleSpan.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        this._editingTaskId = task.id;
        this._render();
      });
      contentChildren.push(titleSpan);
    }

    // Meta (sub-item count + due date) — second line below title
    const metaChildren = [];
    const subProgress = this._getSubItemProgress(task);
    if (subProgress && this._config.show_sub_items !== false) {
      metaChildren.push(this._el("span", { className: "sub-badge", textContent: subProgress }));
    }
    if (task.due_date && this._config.show_due_date !== false) {
      let dueCls = "due-date";
      if (this._isDueDateOverdue(task.due_date)) dueCls += " overdue";
      else if (this._isDueDateToday(task.due_date)) dueCls += " today";
      metaChildren.push(this._el("span", {
        className: dueCls,
        textContent: this._formatDueDate(task.due_date),
      }));
    }
    if (task.recurrence_enabled && task.recurrence_unit && this._config.show_recurrence !== false) {
      const unitLabels = { hours: this._t("rec_short_h"), days: this._t("rec_short_d"), weeks: this._t("rec_short_w"), months: this._t("rec_short_m") };
      const val = task.recurrence_value || 1;
      const singleLabels = { hours: this._t("rec_hourly"), days: this._t("rec_daily"), weeks: this._t("rec_weekly"), months: this._t("rec_monthly") };
      const label = val === 1
        ? singleLabels[task.recurrence_unit]
        : `${val} ${unitLabels[task.recurrence_unit] || task.recurrence_unit}`;
      metaChildren.push(this._el("span", {
        className: "recurrence-badge",
        textContent: "\u21BB " + label,
      }));
    }
    if (task.assigned_person && this._config.show_assigned_person !== false) {
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
    if (task.tags && task.tags.length > 0 && this._config.show_tags !== false) {
      for (const tag of task.tags) {
        const isActive = this._tagFilter === tag;
        const tagBadge = this._el("span", {
          className: "tag-badge" + (isActive ? " active" : ""),
          textContent: "#" + tag,
        });
        tagBadge.addEventListener("click", (e) => {
          e.stopPropagation();
          this._tagFilter = isActive ? null : tag;
          this._render();
        });
        metaChildren.push(tagBadge);
      }
    }
    if (metaChildren.length > 0) {
      contentChildren.push(this._el("div", { className: "task-meta" }, metaChildren));
    }

    mainChildren.push(this._el("div", { className: "task-content" }, contentChildren));

    // Expand button
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

    // Details (expanded)
    if (isExpanded) {
      taskEl.appendChild(this._buildTaskDetails(task));
    }

    // Drag & drop
    this._attachDragToTask(taskEl, task.id, dragHandle);

    return taskEl;
  }

  _buildTaskDetails(task) {
    // Due date section
    const dateInput = this._el("input", {
      type: "date",
      className: "date-input",
      value: task.due_date || "",
    });
    dateInput.addEventListener("change", () =>
      this._updateTaskDueDate(task.id, dateInput.value)
    );
    const dateSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("due_date") }),
      dateInput,
    ]);

    // Notes section
    const notesInput = this._el("textarea", {
      className: "notes-input",
      placeholder: this._t("notes_placeholder"),
      rows: 2,
      value: task.notes || "",
    });
    // textarea needs textContent for initial value
    notesInput.textContent = task.notes || "";
    let debounceTimer;
    notesInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this._updateTaskNotes(task.id, notesInput.value);
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
      subChildren.push(this._buildSubItem(task.id, sub));
    }
    const addSubBtn = this._el("button", {
      className: "add-sub-btn",
      textContent: this._t("add_sub_item"),
    });
    addSubBtn.addEventListener("click", () => this._addSubItem(task.id));
    subChildren.push(addSubBtn);
    const subSection = this._el("div", { className: "detail-section" }, subChildren);

    // Recurrence section
    const recurrenceEnabled = task.recurrence_enabled || false;
    const recurrenceValue = task.recurrence_value || 1;
    const recurrenceUnit = task.recurrence_unit || "days";

    const recurrenceToggle = this._el("input", { type: "checkbox", checked: recurrenceEnabled });
    const recurrenceCheckmark = this._el("span", { className: "checkmark" });
    const recurrenceLabel = this._el("label", { className: "checkbox-container small" }, [
      recurrenceToggle, recurrenceCheckmark,
    ]);
    const recurrenceToggleRow = this._el("div", { className: "recurrence-toggle-row" }, [
      recurrenceLabel,
      this._el("span", { textContent: this._t("recurrence_enabled") }),
    ]);

    const recurrenceValueInput = this._el("input", {
      type: "number",
      className: "recurrence-value",
      value: recurrenceValue,
    });
    recurrenceValueInput.min = 1;
    recurrenceValueInput.max = 365;

    const recurrenceUnitSelect = this._el("select", { className: "recurrence-select" });
    const unitOptions = [
      { value: "hours", label: this._t("rec_hours") },
      { value: "days", label: this._t("rec_days") },
      { value: "weeks", label: this._t("rec_weeks") },
      { value: "months", label: this._t("rec_months") },
    ];
    for (const opt of unitOptions) {
      const optEl = this._el("option", { value: opt.value, textContent: opt.label });
      if (opt.value === recurrenceUnit) optEl.selected = true;
      recurrenceUnitSelect.appendChild(optEl);
    }
    if (!recurrenceEnabled) {
      recurrenceValueInput.disabled = true;
      recurrenceUnitSelect.disabled = true;
    }

    const saveRecurrence = () => {
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      recurrenceValueInput.value = val;
      this._callWs("home_tasks/update_task", {
        list_id: this._config.list_id,
        task_id: task.id,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
      }).then(() => this._loadTasks());
    };

    recurrenceToggle.addEventListener("change", () => {
      const enabled = recurrenceToggle.checked;
      recurrenceValueInput.disabled = !enabled;
      recurrenceUnitSelect.disabled = !enabled;
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      this._callWs("home_tasks/update_task", {
        list_id: this._config.list_id,
        task_id: task.id,
        recurrence_enabled: enabled,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
      }).then(() => this._loadTasks());
    });
    recurrenceValueInput.addEventListener("change", saveRecurrence);
    recurrenceUnitSelect.addEventListener("change", saveRecurrence);

    const recurrenceRow = this._el("div", { className: "recurrence-input-row" }, [
      this._el("span", { textContent: this._t("recurrence_every"), className: "recurrence-prefix" }),
      recurrenceValueInput,
      recurrenceUnitSelect,
    ]);

    const recurrenceSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("recurrence") }),
      recurrenceToggleRow,
      recurrenceRow,
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
        list_id: this._config.list_id,
        task_id: task.id,
        assigned_person: personSelect.value || null,
      }).then(() => this._loadTasks());
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
            list_id: this._config.list_id,
            task_id: task.id,
            tags: newTags,
          }).then(() => this._loadTasks());
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
            list_id: this._config.list_id,
            task_id: task.id,
            tags: [...taskTags, val],
          }).then(() => this._loadTasks());
        }
        tagInput.value = "";
      }
    });
    tagSectionChildren.push(tagInput);
    const tagSection = this._el("div", { className: "detail-section" }, tagSectionChildren);

    // Delete button
    const deleteBtn = this._el("button", {
      className: "delete-task-btn",
      textContent: this._t("delete_task"),
    });
    deleteBtn.addEventListener("click", () => this._deleteTask(task.id));
    const actions = this._el("div", { className: "detail-actions" }, [deleteBtn]);

    const details = [];
    if (this._config.show_tags !== false) details.push(tagSection);
    if (this._config.show_notes !== false) details.push(notesSection);
    if (this._config.show_sub_items !== false) details.push(subSection);
    if (this._config.show_due_date !== false) details.push(dateSection);
    if (this._config.show_recurrence !== false) details.push(recurrenceSection);
    if (this._config.show_assigned_person !== false) details.push(personSection);
    details.push(actions);
    return this._el("div", { className: "task-details" }, details);
  }

  _buildSubItem(taskId, sub) {
    const isEditing = this._editingSubItemId === sub.id;

    const checkbox = this._el("input", { type: "checkbox", checked: sub.completed });
    checkbox.addEventListener("change", () =>
      this._toggleSubItem(taskId, sub.id, sub.completed)
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
        if (e.key === "Enter") this._updateSubItemTitle(taskId, sub.id, titleEl.value);
        else if (e.key === "Escape") { this._editingSubItemId = null; this._render(); }
      });
      titleEl.addEventListener("blur", () =>
        this._updateSubItemTitle(taskId, sub.id, titleEl.value)
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
    deleteBtn.addEventListener("click", () => this._deleteSubItem(taskId, sub.id));

    return this._el("div", { className: "sub-item" }, [label, titleEl, deleteBtn]);
  }

  // --- Drag & Drop (Desktop + Touch) ---

  _getOrderFromDom() {
    const taskList = this.shadowRoot.querySelector(".task-list");
    if (!taskList) return [];
    return Array.from(taskList.querySelectorAll(".task")).map((el) => el.dataset.taskId);
  }

  _liveMoveTask(draggedEl, targetEl) {
    if (!draggedEl || !targetEl || draggedEl === targetEl) return;
    const list = draggedEl.parentNode;
    if (!list) return;
    const draggedRect = draggedEl.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    if (draggedRect.top < targetRect.top) {
      list.insertBefore(draggedEl, targetEl.nextSibling);
    } else {
      list.insertBefore(draggedEl, targetEl);
    }
  }

  _finishDrag() {
    // Read final order from DOM and sync to backend
    const newOrder = this._getOrderFromDom();
    const draggedId = this._draggedTaskId;
    this._draggedTaskId = null;
    this._dragOverTaskId = null;

    // Clean up classes
    this.shadowRoot.querySelectorAll(".task").forEach((el) => {
      el.classList.remove("dragging", "drag-over");
    });

    // Remove touch clone
    if (this._touchClone) {
      this._touchClone.remove();
      this._touchClone = null;
    }
    if (this._touchStartTimer) {
      clearTimeout(this._touchStartTimer);
      this._touchStartTimer = null;
    }

    // Merge filtered order back into full order (for hidden tasks)
    if (draggedId && newOrder.length > 0) {
      const filteredIds = new Set(newOrder);
      const hiddenIds = this._tasks.map((t) => t.id).filter((id) => !filteredIds.has(id));
      // Insert hidden tasks at their relative positions
      const fullOrder = [...newOrder];
      const origOrder = this._tasks.map((t) => t.id);
      for (const hid of hiddenIds) {
        const origIdx = origOrder.indexOf(hid);
        // Find the best insertion point
        let insertIdx = fullOrder.length;
        for (let i = origIdx - 1; i >= 0; i--) {
          const prevId = origOrder[i];
          const posInNew = fullOrder.indexOf(prevId);
          if (posInNew !== -1) {
            insertIdx = posInNew + 1;
            break;
          }
        }
        fullOrder.splice(insertIdx, 0, hid);
      }
      this._reorderTasks(fullOrder);
    }
  }

  _attachDragToTask(taskEl, taskId, dragHandle) {
    // --- HTML5 Drag & Drop (Desktop) ---
    taskEl.addEventListener("dragstart", (e) => {
      this._draggedTaskId = taskId;
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
    });

    taskEl.addEventListener("drop", (e) => {
      e.preventDefault();
      this._finishDrag();
    });

    // --- Touch Events (Mobile) ---
    if (!dragHandle) return;

    dragHandle.addEventListener("touchstart", (e) => {
      if (e.touches.length !== 1) return;
      const touch = e.touches[0];
      this._touchStartTimer = setTimeout(() => {
        this._draggedTaskId = taskId;
        taskEl.classList.add("dragging");

        // Create visual clone
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
        // If finger moves before long-press fires, cancel the timer (allow scroll)
        if (this._touchStartTimer) {
          clearTimeout(this._touchStartTimer);
          this._touchStartTimer = null;
        }
        return;
      }
      e.preventDefault();
      const touch = e.touches[0];

      // Move clone
      if (this._touchClone) {
        this._touchClone.style.top = `${touch.clientY - this._touchOffsetY}px`;
      }

      // Find target element under finger (shadow DOM needs shadowRoot.elementFromPoint)
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
      .card-content { padding: 16px; }
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
      .filters { display: flex; gap: 4px; margin-bottom: 12px; }
      .filter-btn {
        padding: 6px 16px; border: none; border-radius: 20px; background: transparent;
        color: var(--todo-secondary-text); font-size: 13px; cursor: pointer;
        font-family: inherit; transition: all 0.2s;
      }
      .filter-btn.active { background: var(--todo-primary); color: #fff; }
      .filter-btn:not(.active):hover { background: var(--todo-surface); }
      .task-list { display: flex; flex-direction: column; gap: 6px; }
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
      .tag-badge.active {
        background: var(--success-color, #4caf50); color: #fff;
      }
      .tag-chips { display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap; }
      .tag-chip {
        padding: 4px 12px; border: 1px solid rgba(76, 175, 80, 0.3); border-radius: 16px;
        background: transparent; color: var(--success-color, #4caf50); font-size: 12px;
        cursor: pointer; font-family: inherit; transition: all 0.2s;
      }
      .tag-chip:hover { background: rgba(76, 175, 80, 0.1); }
      .tag-chip.active {
        background: var(--success-color, #4caf50); color: #fff;
        border-color: var(--success-color, #4caf50);
      }
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
      .recurrence-toggle-row {
        display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
      }
      .recurrence-input-row {
        display: flex; align-items: center; gap: 8px;
      }
      .recurrence-prefix {
        font-size: 13px; color: var(--todo-secondary-text); white-space: nowrap;
      }
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
      .date-input {
        padding: 6px 10px; border: 1px solid var(--todo-divider); border-radius: 4px;
        font-size: 13px; background: var(--todo-bg); color: var(--todo-text);
        font-family: inherit; max-width: 180px;
      }
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
    `;
  }

  // --- Card config ---

  static getConfigElement() {
    return document.createElement("home-tasks-card-editor");
  }

  static getStubConfig() {
    return { title: "" };
  }

  getCardSize() {
    return 3 + this._tasks.length;
  }
}

/**
 * Card Editor — uses safe DOM construction
 */
class HomeTasksCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._lists = [];
    this._listsLoaded = false;
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
    this._config = { ...config };
    if (this._listsLoaded) {
      // Only skip re-render if title input is focused (user is typing)
      const root = this.shadowRoot;
      const active = root && root.activeElement;
      const isTitleFocused = active && active.id === "title-input";
      if (isTitleFocused) {
        // Update everything except the title input
        this._updateNonInputValues();
      } else {
        this._render();
      }
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
        // Auto-select first list if none set
        if (!this._config.list_id && this._lists.length > 0) {
          this._config = { ...this._config, list_id: this._lists[0].id };
          this._fireChanged();
        }
        this._render();
      }
    } catch (e) {
      // Integration might not be loaded yet
    }
  }

  _updateNonInputValues() {
    // Update select and checkboxes without touching text inputs
    const root = this.shadowRoot;
    const select = root.getElementById("list-select");
    if (select && select.value !== this._config.list_id) {
      select.value = this._config.list_id || "";
    }
  }

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";
    this._rendered = true;

    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; }
      .editor { display: flex; flex-direction: column; gap: 16px; padding: 16px 0; }
      .field { display: flex; flex-direction: column; gap: 4px; }
      label { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: 0.5px; }
      select, input[type="text"] { padding: 8px 12px; border: 1px solid var(--divider-color); border-radius: 4px; font-size: 14px; background: var(--card-background-color); color: var(--primary-text-color); font-family: inherit; }
      .hint { font-size: 12px; color: var(--secondary-text-color); font-style: italic; }
      .toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; }
      .toggle-label { font-size: 14px; color: var(--primary-text-color); }
      .toggle-row input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; accent-color: var(--primary-color); }
    `;
    root.appendChild(style);

    // List select
    const listSelect = this._el("select", { id: "list-select" });
    for (const l of this._lists) {
      const option = this._el("option", {
        value: l.id,
        selected: l.id === this._config.list_id,
        textContent: l.name,
      });
      listSelect.appendChild(option);
    }
    listSelect.addEventListener("change", () => {
      this._config = { ...this._config, list_id: listSelect.value };
      this._fireChanged();
    });

    // Title input
    const titleInput = this._el("input", {
      type: "text",
      id: "title-input",
      value: this._config.title || "",
      placeholder: this._t("ed_title_placeholder"),
    });
    titleInput.addEventListener("input", () => {
      this._config = { ...this._config, title: titleInput.value };
      this._fireChanged();
    });

    // Show title toggle
    const showTitleCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-title",
      checked: this._config.show_title !== false,
    });
    showTitleCb.addEventListener("change", () => {
      this._config = { ...this._config, show_title: showTitleCb.checked };
      this._fireChanged();
    });
    const showTitleRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_title") }),
      showTitleCb,
    ]);

    // Show progress toggle
    const showProgressCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-progress",
      checked: this._config.show_progress !== false,
    });
    showProgressCb.addEventListener("change", () => {
      this._config = { ...this._config, show_progress: showProgressCb.checked };
      this._fireChanged();
    });
    const showProgressRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_progress") }),
      showProgressCb,
    ]);

    // Show due date toggle
    const showDueDateCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-due-date",
      checked: this._config.show_due_date !== false,
    });
    showDueDateCb.addEventListener("change", () => {
      this._config = { ...this._config, show_due_date: showDueDateCb.checked };
      this._fireChanged();
    });
    const showDueDateRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_due_date") }),
      showDueDateCb,
    ]);

    // Show notes toggle
    const showNotesCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-notes",
      checked: this._config.show_notes !== false,
    });
    showNotesCb.addEventListener("change", () => {
      this._config = { ...this._config, show_notes: showNotesCb.checked };
      this._fireChanged();
    });
    const showNotesRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_notes") }),
      showNotesCb,
    ]);

    // Show recurrence toggle
    const showRecurrenceCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-recurrence",
      checked: this._config.show_recurrence !== false,
    });
    showRecurrenceCb.addEventListener("change", () => {
      this._config = { ...this._config, show_recurrence: showRecurrenceCb.checked };
      this._fireChanged();
    });
    const showRecurrenceRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_recurrence") }),
      showRecurrenceCb,
    ]);

    // Show sub-items toggle
    const showSubItemsCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-sub-items",
      checked: this._config.show_sub_items !== false,
    });
    showSubItemsCb.addEventListener("change", () => {
      this._config = { ...this._config, show_sub_items: showSubItemsCb.checked };
      this._fireChanged();
    });
    const showSubItemsRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_sub_items") }),
      showSubItemsCb,
    ]);

    // Show assigned person toggle
    const showPersonCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-person",
      checked: this._config.show_assigned_person !== false,
    });
    showPersonCb.addEventListener("change", () => {
      this._config = { ...this._config, show_assigned_person: showPersonCb.checked };
      this._fireChanged();
    });
    const showPersonRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_person") }),
      showPersonCb,
    ]);

    // Show tags toggle
    const showTagsCb = this._el("input", {
      type: "checkbox",
      id: "cb-show-tags",
      checked: this._config.show_tags !== false,
    });
    showTagsCb.addEventListener("change", () => {
      this._config = { ...this._config, show_tags: showTagsCb.checked };
      this._fireChanged();
    });
    const showTagsRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_show_tags") }),
      showTagsCb,
    ]);

    // Auto-delete completed toggle
    const autoDeleteCb = this._el("input", {
      type: "checkbox",
      id: "cb-auto-delete",
      checked: this._config.auto_delete_completed === true,
    });
    autoDeleteCb.addEventListener("change", () => {
      this._config = { ...this._config, auto_delete_completed: autoDeleteCb.checked };
      this._fireChanged();
    });
    const autoDeleteRow = this._el("div", { className: "toggle-row" }, [
      this._el("span", { className: "toggle-label", textContent: this._t("ed_auto_delete") }),
      autoDeleteCb,
    ]);

    const hint = this._el("span", {
      className: "hint",
      textContent: this._t("ed_hint"),
    });

    const editor = this._el("div", { className: "editor" }, [
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
        this._el("label", { textContent: this._t("ed_display") }),
        showTitleRow,
        showProgressRow,
        showDueDateRow,
        showRecurrenceRow,
        showSubItemsRow,
        showPersonRow,
        showTagsRow,
        showNotesRow,
        autoDeleteRow,
      ]),
    ]);

    root.appendChild(editor);
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

// Register elements — try immediately and deferred to ensure HA's
// scoped custom element registry polyfill is active (fixes Firefox/Safari/iPad)
const _htRegister = () => {
  try { customElements.define("home-tasks-card", HomeTasksCard); } catch(_) {}
  try { customElements.define("home-tasks-card-editor", HomeTasksCardEditor); } catch(_) {}
};

_htRegister();
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", _htRegister, { once: true });
}
window.addEventListener("load", _htRegister, { once: true });

window.customCards = window.customCards || [];
window.customCards.push({
  type: "home-tasks-card",
  name: "Home Tasks",
  description: "A feature-rich todo list with drag & drop, sub-items, notes, and due dates.",
});
