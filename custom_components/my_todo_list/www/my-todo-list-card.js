/**
 * My ToDo List Card for Home Assistant
 * A feature-rich todo list with drag & drop, sub-items, notes, and due dates.
 *
 * Security: All user-controlled content is set via textContent or DOM properties,
 * never via innerHTML with unsanitized data.
 */

class MyTodoListCard extends HTMLElement {
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
    this._newTaskTitle = "";
    this._initialized = false;
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
    const result = await this._callWs("my_todo_list/get_lists");
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
    const result = await this._callWs("my_todo_list/get_tasks", {
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
    const result = await this._callWs("my_todo_list/add_task", {
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
    if (newCompleted && this._config.auto_delete_completed) {
      await this._callWs("my_todo_list/delete_task", {
        list_id: this._config.list_id,
        task_id: taskId,
      });
    } else {
      await this._callWs("my_todo_list/update_task", {
        list_id: this._config.list_id,
        task_id: taskId,
        completed: newCompleted,
      });
    }
    await this._loadTasks();
  }

  async _updateTaskTitle(taskId, title) {
    if (!title.trim()) return;
    const result = await this._callWs("my_todo_list/update_task", {
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
    await this._callWs("my_todo_list/update_task", {
      list_id: this._config.list_id,
      task_id: taskId,
      notes,
    });
  }

  async _updateTaskDueDate(taskId, dueDate) {
    await this._callWs("my_todo_list/update_task", {
      list_id: this._config.list_id,
      task_id: taskId,
      due_date: dueDate || null,
    });
    await this._loadTasks();
  }

  async _deleteTask(taskId) {
    await this._callWs("my_todo_list/delete_task", {
      list_id: this._config.list_id,
      task_id: taskId,
    });
    this._expandedTasks.delete(taskId);
    await this._loadTasks();
  }

  async _addSubItem(taskId) {
    const result = await this._callWs("my_todo_list/add_sub_item", {
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
    await this._callWs("my_todo_list/update_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      sub_item_id: subItemId,
      completed: !completed,
    });
    await this._loadTasks();
  }

  async _updateSubItemTitle(taskId, subItemId, title) {
    if (!title.trim()) return;
    const result = await this._callWs("my_todo_list/update_sub_item", {
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
    await this._callWs("my_todo_list/delete_sub_item", {
      list_id: this._config.list_id,
      task_id: taskId,
      sub_item_id: subItemId,
    });
    await this._loadTasks();
  }

  async _reorderTasks(taskIds) {
    await this._callWs("my_todo_list/reorder_tasks", {
      list_id: this._config.list_id,
      task_ids: taskIds,
    });
    await this._loadTasks();
  }

  // --- Filter ---

  get _filteredTasks() {
    switch (this._filter) {
      case "open":
        return this._tasks.filter((t) => !t.completed);
      case "done":
        return this._tasks.filter((t) => t.completed);
      default:
        return this._tasks;
    }
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
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  _getListName() {
    if (this._config.title) return this._config.title;
    const list = this._lists.find((l) => l.id === this._config.list_id);
    return list ? list.name : "Meine Aufgaben";
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
        textContent: `${completedCount} von ${totalCount} erledigt`,
      }));
    }
    const header = headerChildren.length > 0
      ? this._el("div", { className: "header" }, headerChildren)
      : null;

    // Add task input
    const addInput = this._el("input", {
      type: "text",
      className: "add-input",
      placeholder: "Neue Aufgabe hinzuf\u00fcgen...",
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
      this._buildFilterBtn("Alle", "all"),
      this._buildFilterBtn("Offen", "open"),
      this._buildFilterBtn("Erledigt", "done"),
    ]);

    // Task list
    const taskListChildren = [];
    if (filteredTasks.length === 0) {
      taskListChildren.push(
        this._el("div", { className: "empty-state", textContent: "Keine Aufgaben vorhanden" })
      );
    }
    for (const task of filteredTasks) {
      taskListChildren.push(this._buildTask(task));
    }
    const taskList = this._el("div", { className: "task-list" }, taskListChildren);

    const children = [];
    if (header) children.push(header);
    children.push(addTask);
    if (filters) children.push(filters);
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
    mainChildren.push(
      this._el("span", { className: "drag-handle", title: "Verschieben", textContent: "\u2237" })
    );

    // Checkbox
    const checkbox = this._el("input", { type: "checkbox", checked: task.completed });
    checkbox.addEventListener("change", () => this._toggleTask(task.id, task.completed));
    const checkmark = this._el("span", { className: "checkmark" });
    const label = this._el("label", { className: "checkbox-container" }, [checkbox, checkmark]);
    mainChildren.push(label);

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
      mainChildren.push(editInput);
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
      mainChildren.push(titleSpan);
    }

    // Meta (sub-item count + due date)
    const metaChildren = [];
    const subProgress = this._getSubItemProgress(task);
    if (subProgress) {
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
    mainChildren.push(this._el("div", { className: "task-meta" }, metaChildren));

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
    this._attachDragToTask(taskEl, task.id);

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
      this._el("label", { className: "detail-label", textContent: "F\u00e4lligkeitsdatum" }),
      dateInput,
    ]);

    // Notes section
    const notesInput = this._el("textarea", {
      className: "notes-input",
      placeholder: "Hier kannst du Notizen hinzuf\u00fcgen",
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
      this._el("label", { className: "detail-label", textContent: "Notizen" }),
      notesInput,
    ]);

    // Sub-items section
    const subChildren = [
      this._el("label", { className: "detail-label", textContent: "Unterpunkte" }),
    ];
    for (const sub of task.sub_items) {
      subChildren.push(this._buildSubItem(task.id, sub));
    }
    const addSubBtn = this._el("button", {
      className: "add-sub-btn",
      textContent: "+ Unterpunkt hinzuf\u00fcgen",
    });
    addSubBtn.addEventListener("click", () => this._addSubItem(task.id));
    subChildren.push(addSubBtn);
    const subSection = this._el("div", { className: "detail-section" }, subChildren);

    // Delete button
    const deleteBtn = this._el("button", {
      className: "delete-task-btn",
      textContent: "Aufgabe l\u00f6schen",
    });
    deleteBtn.addEventListener("click", () => this._deleteTask(task.id));
    const actions = this._el("div", { className: "detail-actions" }, [deleteBtn]);

    const details = [];
    if (this._config.show_due_date !== false) details.push(dateSection);
    if (this._config.show_notes !== false) details.push(notesSection);
    details.push(subSection, actions);
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
      title: "L\u00f6schen",
      textContent: "\u00D7",
    });
    deleteBtn.addEventListener("click", () => this._deleteSubItem(taskId, sub.id));

    return this._el("div", { className: "sub-item" }, [label, titleEl, deleteBtn]);
  }

  // --- Drag & Drop ---

  _attachDragToTask(taskEl, taskId) {
    taskEl.addEventListener("dragstart", (e) => {
      this._draggedTaskId = taskId;
      e.dataTransfer.effectAllowed = "move";
      taskEl.classList.add("dragging");
    });

    taskEl.addEventListener("dragend", () => {
      this._draggedTaskId = null;
      this._dragOverTaskId = null;
      this.shadowRoot.querySelectorAll(".task").forEach((el) => {
        el.classList.remove("dragging", "drag-over");
      });
    });

    taskEl.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (this._draggedTaskId && this._draggedTaskId !== taskId) {
        this._dragOverTaskId = taskId;
        this.shadowRoot.querySelectorAll(".task").forEach((el) =>
          el.classList.remove("drag-over")
        );
        taskEl.classList.add("drag-over");
      }
    });

    taskEl.addEventListener("dragleave", () => {
      taskEl.classList.remove("drag-over");
    });

    taskEl.addEventListener("drop", (e) => {
      e.preventDefault();
      if (!this._draggedTaskId || this._draggedTaskId === taskId) return;

      const currentOrder = this._filteredTasks.map((t) => t.id);
      const fromIndex = currentOrder.indexOf(this._draggedTaskId);
      const toIndex = currentOrder.indexOf(taskId);
      if (fromIndex === -1 || toIndex === -1) return;

      const allIds = this._tasks.map((t) => t.id);
      const draggedId = this._draggedTaskId;
      const newAllIds = allIds.filter((id) => id !== draggedId);
      const targetFullIndex = newAllIds.indexOf(taskId);
      newAllIds.splice(
        fromIndex < toIndex ? targetFullIndex + 1 : targetFullIndex,
        0,
        draggedId
      );

      this._draggedTaskId = null;
      this._dragOverTaskId = null;
      this._reorderTasks(newAllIds);
    });
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
      .task.dragging { opacity: 0.5; }
      .task.drag-over { border-color: var(--todo-primary); box-shadow: 0 0 0 1px var(--todo-primary); }
      .task-main { display: flex; align-items: center; padding: 10px 12px; gap: 8px; min-height: 44px; }
      .drag-handle {
        cursor: grab; color: var(--todo-disabled); font-size: 16px;
        user-select: none; padding: 4px 2px; line-height: 1;
      }
      .drag-handle:active { cursor: grabbing; }
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
        flex: 1; font-size: 14px; color: var(--todo-text); cursor: pointer;
        min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
      }
      .task.completed .task-title { text-decoration: line-through; color: var(--todo-disabled); }
      .edit-title-input, .edit-sub-input {
        flex: 1; padding: 4px 8px; border: 1px solid var(--todo-primary);
        border-radius: 4px; font-size: 14px; background: var(--todo-bg);
        color: var(--todo-text); outline: none; font-family: inherit; min-width: 0;
      }
      .task-meta { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
      .sub-badge {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: var(--todo-surface); color: var(--todo-secondary-text); font-weight: 500;
      }
      .due-date {
        font-size: 11px; padding: 2px 8px; border-radius: 10px;
        background: var(--todo-surface); color: var(--todo-secondary-text);
      }
      .due-date.today { background: #fff3e0; color: #e65100; }
      .due-date.overdue { background: #ffebee; color: var(--todo-error); font-weight: 500; }
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
      .delete-sub-btn:hover { color: var(--todo-error); background: #ffebee; }
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
      .delete-task-btn:hover { background: #ffebee; }
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
    return document.createElement("my-todo-list-card-editor");
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
class MyTodoListCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._lists = [];
    this._listsLoaded = false;
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
      const result = await this._hass.callWS({ type: "my_todo_list/get_lists" });
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
      placeholder: "Standard: Listenname",
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
      this._el("span", { className: "toggle-label", textContent: "Titel anzeigen" }),
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
      this._el("span", { className: "toggle-label", textContent: "Fortschritt anzeigen" }),
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
      this._el("span", { className: "toggle-label", textContent: "F\u00e4lligkeitsdatum anzeigen" }),
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
      this._el("span", { className: "toggle-label", textContent: "Notizen anzeigen" }),
      showNotesCb,
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
      this._el("span", { className: "toggle-label", textContent: "Erledigte Aufgaben sofort l\u00f6schen" }),
      autoDeleteCb,
    ]);

    const hint = this._el("span", {
      className: "hint",
      textContent: "Neue Listen k\u00f6nnen unter Einstellungen \u2192 Integrationen \u2192 My ToDo List erstellt werden.",
    });

    const editor = this._el("div", { className: "editor" }, [
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: "Liste" }),
        listSelect,
        hint,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: "Titel (optional)" }),
        titleInput,
      ]),
      this._el("div", { className: "field" }, [
        this._el("label", { textContent: "Anzeige" }),
        showTitleRow,
        showProgressRow,
        showDueDateRow,
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

customElements.define("my-todo-list-card", MyTodoListCard);
customElements.define("my-todo-list-card-editor", MyTodoListCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "my-todo-list-card",
  name: "My ToDo List",
  description: "A feature-rich todo list with drag & drop, sub-items, notes, and due dates.",
});
