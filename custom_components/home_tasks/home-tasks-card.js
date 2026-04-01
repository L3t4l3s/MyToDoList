/**
 * Home Tasks Card for Home Assistant
 * A feature-rich todo list with drag & drop, sub-tasks, notes, and due dates.
 *
 * Security: All user-controlled content is set via textContent or DOM properties,
 * never via innerHTML with unsanitized data.
 */
console.info("%c HOME-TASKS-CARD %c v1.3.0 ", "color: white; background: #03a9f4; font-weight: bold;", "color: #03a9f4; background: white; font-weight: bold;");

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
    sub_items: "Sub-tasks",
    add_sub_item: "+ Add sub-task",
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
    ed_show_title: "Title",
    ed_show_progress: "Progress",
    ed_show_due_date: "Due date",
    ed_show_notes: "Notes",
    ed_show_recurrence: "Recurrence",
    ed_show_sub_items: "Sub-tasks",
    ed_show_person: "Person",
    ed_auto_delete: "Delete completed immediately",
    ed_compact: "Compact",
    ed_show_tags: "Tags",
    ed_hint: "New lists can be created under Settings \u2192 Integrations \u2192 Home Tasks.",
    tags: "Tags",
    add_tag: "+ Add tag",
    tag_placeholder: "New tag...",
    remove_tag: "Remove",
    new_sub_item: "New sub-task",
    remove_reminder: "Remove reminder",
    sort_label: "Sort",
    sort_manual: "Manual",
    sort_due: "Due date",
    sort_priority: "Priority",
    sort_title: "Title (A\u2013Z)",
    sort_person: "Assigned",
    ed_show_sort: "Sort",
    ed_show_priority: "Priority",
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
    ed_show_reminders: "Reminders",
    ed_add_column: "Add column",
    ed_move_left: "Move left",
    ed_move_right: "Move right",
    ed_duplicate: "Duplicate column",
    ed_delete_column: "Delete column",
    ed_code_editor: "Code editor",
    ed_visual_editor: "Visual editor",
    ed_icon: "Icon (optional)",
    ed_card_title: "Card title (optional)",
    ed_card_title_placeholder: "Title shown above columns",
    ed_sec_view: "Display",
    ed_sec_display: "Configuration",
    due_time_lbl: "Time",
    due_date_lbl: "Date",
    rec_mode_lbl: "Mode",
    rec_time: "Reactivation time", rec_end: "End", rec_end_never: "Never", rec_end_date: "On date", rec_end_count: "After N times",
    rec_end_date_lbl: "End date", rec_max_count_lbl: "max", rec_remaining: "{0} left", rec_start_date_lbl: "Start date",
    history: "History", history_created: "Created", history_completed: "Completed", history_reopened: "Reopened",
    history_reset: "Auto-reset (recurrence)", history_changed: "changed", history_empty: "No history yet", hist_title: "Title", history_disabled: "Disabled",
    ed_show_history: "Show history", hist_by_user: "User",
  },
  nl: {
    my_tasks: "Mijn taken",
    add_placeholder: "Nieuwe taak toevoegen...",
    filter_all: "Alle", filter_open: "Open", filter_done: "Klaar",
    progress: "{0} van {1} klaar",
    empty: "Geen taken",
    drag_handle: "Slepen om te herordenen",
    due_date: "Deadline", notes: "Notities", notes_placeholder: "Voeg notities toe",
    sub_items: "Subtaken", add_sub_item: "+ Subtaak toevoegen",
    recurrence: "Herhaling", recurrence_enabled: "Ingeschakeld", recurrence_every: "Elke",
    rec_hours: "Uren", rec_days: "Dagen", rec_weeks: "Weken", rec_months: "Maanden",
    rec_short_h: "u", rec_short_d: "d", rec_short_w: "w", rec_short_m: "m",
    priority: "Prioriteit", pri_high: "Hoog", pri_medium: "Middel", pri_low: "Laag",
    ed_show_priority: "Prioriteit",
    rec_hourly: "Uurlijks", rec_daily: "Dagelijks", rec_weekly: "Wekelijks", rec_monthly: "Maandelijks",
    rec_type_interval: "Elke \u2026", rec_type_weekdays: "Op weekdagen",
    rec_wd_0: "Ma", rec_wd_1: "Di", rec_wd_2: "Wo", rec_wd_3: "Do", rec_wd_4: "Vr", rec_wd_5: "Za", rec_wd_6: "Zo",
    assigned_to: "Toegewezen aan", nobody: "\u2013 Niemand \u2013",
    delete_task: "Taak verwijderen", delete_sub: "Verwijderen",
    ed_default_filter: "Standaardfilter", ed_list: "Lijst",
    ed_title: "Titel (optioneel)", ed_title_placeholder: "Standaard: lijstnaam",
    ed_display: "Weergave", ed_show_title: "Titel", ed_show_progress: "Voortgang",
    ed_show_due_date: "Deadline", ed_show_notes: "Notities", ed_show_recurrence: "Herhaling",
    ed_show_sub_items: "Subtaken", ed_show_person: "Persoon",
    ed_auto_delete: "Voltooide meteen verwijderen", ed_compact: "Compact", ed_show_tags: "Tags",
    ed_hint: "Nieuwe lijsten kunnen worden aangemaakt via Instellingen \u2192 Integraties \u2192 Home Tasks.",
    tags: "Tags", add_tag: "+ Tag toevoegen", tag_placeholder: "Nieuwe tag...", remove_tag: "Verwijderen",
    new_sub_item: "Nieuwe subtaak", remove_reminder: "Herinnering verwijderen",
    sort_label: "Sorteren", sort_manual: "Handmatig", sort_due: "Deadline",
    sort_priority: "Prioriteit", sort_title: "Titel (A\u2013Z)", sort_person: "Toegewezen",
    ed_show_sort: "Sorteren", ed_default_sort: "Standaard sortering",
    reminder: "Herinneringen", rem_add: "+ Herinnering toevoegen", rem_none: "Geen herinnering",
    rem_at_due: "Op vervaldatum", rem_5m: "5 min. eerder", rem_15m: "15 min. eerder",
    rem_30m: "30 min. eerder", rem_1h: "1 uur eerder", rem_2h: "2 uur eerder",
    rem_1d: "1 dag eerder", rem_2d: "2 dagen eerder",
    ed_show_reminders: "Herinneringen", ed_add_column: "Kolom toevoegen",
    ed_move_left: "Naar links", ed_move_right: "Naar rechts",
    ed_duplicate: "Kolom dupliceren", ed_delete_column: "Kolom verwijderen",
    ed_code_editor: "Code-editor", ed_visual_editor: "Visuele editor",
    ed_icon: "Pictogram (optioneel)", ed_card_title: "Kaarttitel (optioneel)",
    ed_card_title_placeholder: "Titel boven kolommen",
    ed_sec_view: "Weergave", ed_sec_display: "Configuratie",
    due_time_lbl: "Tijd", due_date_lbl: "Datum", rec_mode_lbl: "Modus",
    rec_time: "Tijdstip", rec_end: "Einde", rec_end_never: "Nooit", rec_end_date: "Op datum", rec_end_count: "Na N keer",
    rec_end_date_lbl: "Einddatum", rec_max_count_lbl: "max", rec_remaining: "nog {0}", rec_start_date_lbl: "Startdatum",
    history: "Geschiedenis", history_created: "Aangemaakt", history_completed: "Voltooid", history_reopened: "Heropend",
    history_reset: "Automatisch teruggezet", history_changed: "gewijzigd", history_empty: "Geen geschiedenis", hist_title: "Titel", history_disabled: "Uitgeschakeld",
    ed_show_history: "Geschiedenis tonen", hist_by_user: "Gebruiker",
  },
  it: {
    my_tasks: "Le mie attivit\u00e0",
    add_placeholder: "Aggiungi nuova attivit\u00e0...",
    filter_all: "Tutte", filter_open: "Aperte", filter_done: "Completate",
    progress: "{0} di {1} completate",
    empty: "Nessuna attivit\u00e0",
    drag_handle: "Trascina per riordinare",
    due_date: "Scadenza", notes: "Note", notes_placeholder: "Aggiungi note qui",
    sub_items: "Sotto-attivit\u00e0", add_sub_item: "+ Aggiungi sotto-attivit\u00e0",
    recurrence: "Ricorrenza", recurrence_enabled: "Attivata", recurrence_every: "Ogni",
    rec_hours: "Ore", rec_days: "Giorni", rec_weeks: "Settimane", rec_months: "Mesi",
    rec_short_h: "h", rec_short_d: "g", rec_short_w: "s", rec_short_m: "m",
    priority: "Priorit\u00e0", pri_high: "Alta", pri_medium: "Media", pri_low: "Bassa",
    ed_show_priority: "Priorit\u00e0",
    rec_hourly: "Oraria", rec_daily: "Giornaliera", rec_weekly: "Settimanale", rec_monthly: "Mensile",
    rec_type_interval: "Ogni \u2026", rec_type_weekdays: "Nei giorni feriali",
    rec_wd_0: "Lun", rec_wd_1: "Mar", rec_wd_2: "Mer", rec_wd_3: "Gio", rec_wd_4: "Ven", rec_wd_5: "Sab", rec_wd_6: "Dom",
    assigned_to: "Assegnato a", nobody: "\u2013 Nessuno \u2013",
    delete_task: "Elimina attivit\u00e0", delete_sub: "Elimina",
    ed_default_filter: "Filtro predefinito", ed_list: "Lista",
    ed_title: "Titolo (opzionale)", ed_title_placeholder: "Predefinito: nome lista",
    ed_display: "Visualizzazione", ed_show_title: "Titolo", ed_show_progress: "Avanzamento",
    ed_show_due_date: "Scadenza", ed_show_notes: "Note", ed_show_recurrence: "Ricorrenza",
    ed_show_sub_items: "Sotto-attivit\u00e0", ed_show_person: "Persona",
    ed_auto_delete: "Elimina completate immediatamente", ed_compact: "Compatto", ed_show_tags: "Tag",
    ed_hint: "Nuove liste possono essere create in Impostazioni \u2192 Integrazioni \u2192 Home Tasks.",
    tags: "Tag", add_tag: "+ Aggiungi tag", tag_placeholder: "Nuovo tag...", remove_tag: "Rimuovi",
    new_sub_item: "Nuova sotto-attivit\u00e0", remove_reminder: "Rimuovi promemoria",
    sort_label: "Ordina", sort_manual: "Manuale", sort_due: "Scadenza",
    sort_priority: "Priorit\u00e0", sort_title: "Titolo (A\u2013Z)", sort_person: "Assegnato",
    ed_show_sort: "Ordinamento", ed_default_sort: "Ordinamento predefinito",
    reminder: "Promemoria", rem_add: "+ Aggiungi promemoria", rem_none: "Nessun promemoria",
    rem_at_due: "All\u2019ora di scadenza", rem_5m: "5 min. prima", rem_15m: "15 min. prima",
    rem_30m: "30 min. prima", rem_1h: "1 ora prima", rem_2h: "2 ore prima",
    rem_1d: "1 giorno prima", rem_2d: "2 giorni prima",
    ed_show_reminders: "Promemoria", ed_add_column: "Aggiungi colonna",
    ed_move_left: "Sposta a sinistra", ed_move_right: "Sposta a destra",
    ed_duplicate: "Duplica colonna", ed_delete_column: "Elimina colonna",
    ed_code_editor: "Editor codice", ed_visual_editor: "Editor visuale",
    ed_icon: "Icona (opzionale)", ed_card_title: "Titolo scheda (opzionale)",
    ed_card_title_placeholder: "Titolo sopra le colonne",
    ed_sec_view: "Visualizzazione", ed_sec_display: "Configurazione",
    due_time_lbl: "Ora", due_date_lbl: "Data", rec_mode_lbl: "Modalit\u00e0",
    rec_time: "Orario", rec_end: "Fine", rec_end_never: "Mai", rec_end_date: "Alla data", rec_end_count: "Dopo N volte",
    rec_end_date_lbl: "Data di fine", rec_max_count_lbl: "max", rec_remaining: "ancora {0}", rec_start_date_lbl: "Data di inizio",
    history: "Cronologia", history_created: "Creato", history_completed: "Completato", history_reopened: "Riaperto",
    history_reset: "Ripristino automatico", history_changed: "modificato", history_empty: "Nessuna cronologia", hist_title: "Titolo", history_disabled: "Disabilitato",
    ed_show_history: "Mostra cronologia", hist_by_user: "Utente",
  },
  pl: {
    my_tasks: "Moje zadania",
    add_placeholder: "Dodaj nowe zadanie...",
    filter_all: "Wszystkie", filter_open: "Otwarte", filter_done: "Uko\u0144czone",
    progress: "{0} z {1} uko\u0144czono",
    empty: "Brak zada\u0144",
    drag_handle: "Przeci\u0105gnij, aby zmieni\u0107 kolejno\u015b\u0107",
    due_date: "Termin", notes: "Notatki", notes_placeholder: "Dodaj notatki tutaj",
    sub_items: "Podzadania", add_sub_item: "+ Dodaj podzadanie",
    recurrence: "Powtarzanie", recurrence_enabled: "W\u0142\u0105czone", recurrence_every: "Co",
    rec_hours: "Godziny", rec_days: "Dni", rec_weeks: "Tygodnie", rec_months: "Miesi\u0105ce",
    rec_short_h: "g", rec_short_d: "d", rec_short_w: "t", rec_short_m: "m",
    priority: "Priorytet", pri_high: "Wysoki", pri_medium: "\u015arednij", pri_low: "Niski",
    ed_show_priority: "Priorytet",
    rec_hourly: "Co godz.", rec_daily: "Codziennie", rec_weekly: "Co tydz.", rec_monthly: "Co mies.",
    rec_type_interval: "Co \u2026", rec_type_weekdays: "W dni robocze",
    rec_wd_0: "Pn", rec_wd_1: "Wt", rec_wd_2: "\u015ar", rec_wd_3: "Cz", rec_wd_4: "Pt", rec_wd_5: "So", rec_wd_6: "Nd",
    assigned_to: "Przypisano do", nobody: "\u2013 Nikt \u2013",
    delete_task: "Usu\u0144 zadanie", delete_sub: "Usu\u0144",
    ed_default_filter: "Domy\u015blny filtr", ed_list: "Lista",
    ed_title: "Tytu\u0142 (opcjonalnie)", ed_title_placeholder: "Domy\u015blnie: nazwa listy",
    ed_display: "Wy\u015bwietlanie", ed_show_title: "Tytu\u0142", ed_show_progress: "Post\u0119p",
    ed_show_due_date: "Termin", ed_show_notes: "Notatki", ed_show_recurrence: "Powtarzanie",
    ed_show_sub_items: "Podzadania", ed_show_person: "Osoba",
    ed_auto_delete: "Natychmiast usu\u0144 uko\u0144czone", ed_compact: "Kompaktowy", ed_show_tags: "Tagi",
    ed_hint: "Nowe listy mo\u017cna tworzy\u0107 w Ustawienia \u2192 Integracje \u2192 Home Tasks.",
    tags: "Tagi", add_tag: "+ Dodaj tag", tag_placeholder: "Nowy tag...", remove_tag: "Usu\u0144",
    new_sub_item: "Nowe podzadanie", remove_reminder: "Usu\u0144 przypomnienie",
    sort_label: "Sortuj", sort_manual: "R\u0119cznie", sort_due: "Termin",
    sort_priority: "Priorytet", sort_title: "Tytu\u0142 (A\u2013Z)", sort_person: "Przypisany",
    ed_show_sort: "Sortowanie", ed_default_sort: "Domy\u015blne sortowanie",
    reminder: "Przypomnienia", rem_add: "+ Dodaj przypomnienie", rem_none: "Brak przypomnienia",
    rem_at_due: "W czasie terminu", rem_5m: "5 min. wcze\u015bniej", rem_15m: "15 min. wcze\u015bniej",
    rem_30m: "30 min. wcze\u015bniej", rem_1h: "1 godz. wcze\u015bniej", rem_2h: "2 godz. wcze\u015bniej",
    rem_1d: "1 dzie\u0144 wcze\u015bniej", rem_2d: "2 dni wcze\u015bniej",
    ed_show_reminders: "Przypomnienia", ed_add_column: "Dodaj kolumn\u0119",
    ed_move_left: "Przesu\u0144 w lewo", ed_move_right: "Przesu\u0144 w prawo",
    ed_duplicate: "Duplikuj kolumn\u0119", ed_delete_column: "Usu\u0144 kolumn\u0119",
    ed_code_editor: "Edytor kodu", ed_visual_editor: "Edytor wizualny",
    ed_icon: "Ikona (opcjonalnie)", ed_card_title: "Tytu\u0142 karty (opcjonalnie)",
    ed_card_title_placeholder: "Tytu\u0142 nad kolumnami",
    ed_sec_view: "Wy\u015bwietlanie", ed_sec_display: "Konfiguracja",
    due_time_lbl: "Czas", due_date_lbl: "Data", rec_mode_lbl: "Tryb",
    rec_time: "Godzina", rec_end: "Koniec", rec_end_never: "Nigdy", rec_end_date: "W dniu", rec_end_count: "Po N razach",
    rec_end_date_lbl: "Data ko\u0144cowa", rec_max_count_lbl: "max", rec_remaining: "jeszcze {0}", rec_start_date_lbl: "Data pocz\u0105tku",
    history: "Historia", history_created: "Utworzono", history_completed: "Uko\u0144czono", history_reopened: "Ponownie otwarto",
    history_reset: "Auto-reset", history_changed: "zmieniono", history_empty: "Brak historii", hist_title: "Tytu\u0142", history_disabled: "Wy\u0142\u0105czono",
    ed_show_history: "Poka\u017c histori\u0119", hist_by_user: "U\u017cytkownik",
  },
  sv: {
    my_tasks: "Mina uppgifter",
    add_placeholder: "L\u00e4gg till ny uppgift...",
    filter_all: "Alla", filter_open: "\u00d6ppna", filter_done: "Klara",
    progress: "{0} av {1} klara",
    empty: "Inga uppgifter",
    drag_handle: "Dra f\u00f6r att \u00e4ndra ordning",
    due_date: "F\u00f6rfallodatum", notes: "Anteckningar", notes_placeholder: "L\u00e4gg till anteckningar h\u00e4r",
    sub_items: "Deluppgifter", add_sub_item: "+ L\u00e4gg till deluppgift",
    recurrence: "Upprepning", recurrence_enabled: "Aktiverad", recurrence_every: "Var",
    rec_hours: "Timmar", rec_days: "Dagar", rec_weeks: "Veckor", rec_months: "M\u00e5nader",
    rec_short_h: "t", rec_short_d: "d", rec_short_w: "v", rec_short_m: "m\u00e5n",
    priority: "Prioritet", pri_high: "H\u00f6g", pri_medium: "Medel", pri_low: "L\u00e5g",
    ed_show_priority: "Prioritet",
    rec_hourly: "Varje timme", rec_daily: "Dagligen", rec_weekly: "Veckovis", rec_monthly: "M\u00e5nadsvis",
    rec_type_interval: "Var \u2026", rec_type_weekdays: "P\u00e5 vardagar",
    rec_wd_0: "M\u00e5n", rec_wd_1: "Tis", rec_wd_2: "Ons", rec_wd_3: "Tor", rec_wd_4: "Fre", rec_wd_5: "L\u00f6r", rec_wd_6: "S\u00f6n",
    assigned_to: "Tilldelad", nobody: "\u2013 Ingen \u2013",
    delete_task: "Ta bort uppgift", delete_sub: "Ta bort",
    ed_default_filter: "Standardfilter", ed_list: "Lista",
    ed_title: "Titel (valfritt)", ed_title_placeholder: "Standard: listnamn",
    ed_display: "Visning", ed_show_title: "Titel", ed_show_progress: "Framsteg",
    ed_show_due_date: "F\u00f6rfallodatum", ed_show_notes: "Anteckningar", ed_show_recurrence: "Upprepning",
    ed_show_sub_items: "Deluppgifter", ed_show_person: "Person",
    ed_auto_delete: "Ta bort slutf\u00f6rda omedelbart", ed_compact: "Kompakt", ed_show_tags: "Taggar",
    ed_hint: "Nya listor kan skapas under Inst\u00e4llningar \u2192 Integrationer \u2192 Home Tasks.",
    tags: "Taggar", add_tag: "+ L\u00e4gg till tagg", tag_placeholder: "Ny tagg...", remove_tag: "Ta bort",
    new_sub_item: "Ny deluppgift", remove_reminder: "Ta bort p\u00e5minnelse",
    sort_label: "Sortera", sort_manual: "Manuell", sort_due: "F\u00f6rfallodatum",
    sort_priority: "Prioritet", sort_title: "Titel (A\u2013\u00d6)", sort_person: "Tilldelad",
    ed_show_sort: "Sortering", ed_default_sort: "Standardsortering",
    reminder: "P\u00e5minnelser", rem_add: "+ L\u00e4gg till p\u00e5minnelse", rem_none: "Ingen p\u00e5minnelse",
    rem_at_due: "Vid f\u00f6rfallotid", rem_5m: "5 min. f\u00f6re", rem_15m: "15 min. f\u00f6re",
    rem_30m: "30 min. f\u00f6re", rem_1h: "1 timme f\u00f6re", rem_2h: "2 timmar f\u00f6re",
    rem_1d: "1 dag f\u00f6re", rem_2d: "2 dagar f\u00f6re",
    ed_show_reminders: "P\u00e5minnelser", ed_add_column: "L\u00e4gg till kolumn",
    ed_move_left: "Flytta v\u00e4nster", ed_move_right: "Flytta h\u00f6ger",
    ed_duplicate: "Duplicera kolumn", ed_delete_column: "Ta bort kolumn",
    ed_code_editor: "Kodredigerare", ed_visual_editor: "Visuell redigerare",
    ed_icon: "Ikon (valfritt)", ed_card_title: "Korttitel (valfritt)",
    ed_card_title_placeholder: "Titel ovanf\u00f6r kolumner",
    ed_sec_view: "Visning", ed_sec_display: "Konfiguration",
    due_time_lbl: "Tid", due_date_lbl: "Datum", rec_mode_lbl: "L\u00e4ge",
    rec_time: "Tid", rec_end: "Slut", rec_end_never: "Aldrig", rec_end_date: "P\u00e5 datum", rec_end_count: "Efter N g\u00e5nger",
    rec_end_date_lbl: "Slutdatum", rec_max_count_lbl: "max", rec_remaining: "{0} kvar", rec_start_date_lbl: "Startdatum",
    history: "Historik", history_created: "Skapad", history_completed: "Avklarad", history_reopened: "\u00d6ppnad igen",
    history_reset: "Auto-\u00e5terst\u00e4lld", history_changed: "\u00e4ndrad", history_empty: "Ingen historik", hist_title: "Titel", history_disabled: "Inaktiverad",
    ed_show_history: "Visa historik", hist_by_user: "Anv\u00e4ndare",
  },
  fr: {
    my_tasks: "Mes t\u00e2ches",
    add_placeholder: "Ajouter une nouvelle t\u00e2che...",
    filter_all: "Toutes", filter_open: "Ouvertes", filter_done: "Termin\u00e9es",
    progress: "{0} sur {1} termin\u00e9es",
    empty: "Aucune t\u00e2che",
    drag_handle: "Glisser pour r\u00e9organiser",
    due_date: "\u00c9ch\u00e9ance", notes: "Notes", notes_placeholder: "Ajouter des notes ici",
    sub_items: "Sous-t\u00e2ches", add_sub_item: "+ Ajouter une sous-t\u00e2che",
    recurrence: "R\u00e9currence", recurrence_enabled: "Activ\u00e9e", recurrence_every: "Tous les",
    rec_hours: "Heures", rec_days: "Jours", rec_weeks: "Semaines", rec_months: "Mois",
    rec_short_h: "h", rec_short_d: "j", rec_short_w: "s", rec_short_m: "m",
    priority: "Priorit\u00e9", pri_high: "Haute", pri_medium: "Moyenne", pri_low: "Basse",
    ed_show_priority: "Priorit\u00e9",
    rec_hourly: "Horaire", rec_daily: "Quotidien", rec_weekly: "Hebdomadaire", rec_monthly: "Mensuel",
    rec_type_interval: "Tous les \u2026", rec_type_weekdays: "Les jours de semaine",
    rec_wd_0: "Lun", rec_wd_1: "Mar", rec_wd_2: "Mer", rec_wd_3: "Jeu", rec_wd_4: "Ven", rec_wd_5: "Sam", rec_wd_6: "Dim",
    assigned_to: "Assign\u00e9 \u00e0", nobody: "\u2013 Personne \u2013",
    delete_task: "Supprimer la t\u00e2che", delete_sub: "Supprimer",
    ed_default_filter: "Filtre par d\u00e9faut", ed_list: "Liste",
    ed_title: "Titre (optionnel)", ed_title_placeholder: "Par d\u00e9faut\u00a0: nom de la liste",
    ed_display: "Affichage", ed_show_title: "Titre", ed_show_progress: "Progression",
    ed_show_due_date: "\u00c9ch\u00e9ance", ed_show_notes: "Notes", ed_show_recurrence: "R\u00e9currence",
    ed_show_sub_items: "Sous-t\u00e2ches", ed_show_person: "Personne",
    ed_auto_delete: "Supprimer les termin\u00e9es imm\u00e9diatement", ed_compact: "Compact", ed_show_tags: "\u00c9tiquettes",
    ed_hint: "De nouvelles listes peuvent \u00eatre cr\u00e9\u00e9es dans Param\u00e8tres \u2192 Int\u00e9grations \u2192 Home Tasks.",
    tags: "\u00c9tiquettes", add_tag: "+ Ajouter une \u00e9tiquette", tag_placeholder: "Nouvelle \u00e9tiquette...", remove_tag: "Supprimer",
    new_sub_item: "Nouvelle sous-t\u00e2che", remove_reminder: "Supprimer le rappel",
    sort_label: "Trier", sort_manual: "Manuel", sort_due: "\u00c9ch\u00e9ance",
    sort_priority: "Priorit\u00e9", sort_title: "Titre (A\u2013Z)", sort_person: "Assign\u00e9",
    ed_show_sort: "Tri", ed_default_sort: "Tri par d\u00e9faut",
    reminder: "Rappels", rem_add: "+ Ajouter un rappel", rem_none: "Aucun rappel",
    rem_at_due: "\u00c0 l\u2019heure d\u2019\u00e9ch\u00e9ance", rem_5m: "5 min. avant", rem_15m: "15 min. avant",
    rem_30m: "30 min. avant", rem_1h: "1 heure avant", rem_2h: "2 heures avant",
    rem_1d: "1 jour avant", rem_2d: "2 jours avant",
    ed_show_reminders: "Rappels", ed_add_column: "Ajouter une colonne",
    ed_move_left: "D\u00e9placer \u00e0 gauche", ed_move_right: "D\u00e9placer \u00e0 droite",
    ed_duplicate: "Dupliquer la colonne", ed_delete_column: "Supprimer la colonne",
    ed_code_editor: "\u00c9diteur de code", ed_visual_editor: "\u00c9diteur visuel",
    ed_icon: "Ic\u00f4ne (optionnel)", ed_card_title: "Titre de la carte (optionnel)",
    ed_card_title_placeholder: "Titre au-dessus des colonnes",
    ed_sec_view: "Affichage", ed_sec_display: "Configuration",
    due_time_lbl: "Heure", due_date_lbl: "Date", rec_mode_lbl: "Mode",
    rec_time: "Heure", rec_end: "Fin", rec_end_never: "Jamais", rec_end_date: "\u00c0 la date", rec_end_count: "Apr\u00e8s N fois",
    rec_end_date_lbl: "Date de fin", rec_max_count_lbl: "max", rec_remaining: "encore {0}", rec_start_date_lbl: "Date de d\u00e9but",
    history: "Historique", history_created: "Cr\u00e9\u00e9", history_completed: "Termin\u00e9", history_reopened: "R\u00e9ouvert",
    history_reset: "R\u00e9initialisation auto.", history_changed: "modifi\u00e9", history_empty: "Aucun historique", hist_title: "Titre", history_disabled: "D\u00e9sactiv\u00e9",
    ed_show_history: "Afficher l'historique", hist_by_user: "Utilisateur",
  },
  pt: {
    my_tasks: "Minhas tarefas",
    add_placeholder: "Adicionar nova tarefa...",
    filter_all: "Todas", filter_open: "Abertas", filter_done: "Conclu\u00eddas",
    progress: "{0} de {1} conclu\u00eddas",
    empty: "Nenhuma tarefa",
    drag_handle: "Arrastar para reordenar",
    due_date: "Prazo", notes: "Notas", notes_placeholder: "Adicionar notas aqui",
    sub_items: "Subtarefas", add_sub_item: "+ Adicionar subtarefa",
    recurrence: "Recorr\u00eancia", recurrence_enabled: "Ativada", recurrence_every: "A cada",
    rec_hours: "Horas", rec_days: "Dias", rec_weeks: "Semanas", rec_months: "Meses",
    rec_short_h: "h", rec_short_d: "d", rec_short_w: "s", rec_short_m: "m",
    priority: "Prioridade", pri_high: "Alta", pri_medium: "M\u00e9dia", pri_low: "Baixa",
    ed_show_priority: "Prioridade",
    rec_hourly: "Por hora", rec_daily: "Di\u00e1rio", rec_weekly: "Semanal", rec_monthly: "Mensal",
    rec_type_interval: "A cada \u2026", rec_type_weekdays: "Nos dias \u00fateis",
    rec_wd_0: "Seg", rec_wd_1: "Ter", rec_wd_2: "Qua", rec_wd_3: "Qui", rec_wd_4: "Sex", rec_wd_5: "S\u00e1b", rec_wd_6: "Dom",
    assigned_to: "Atribu\u00eddo a", nobody: "\u2013 Ningu\u00e9m \u2013",
    delete_task: "Excluir tarefa", delete_sub: "Excluir",
    ed_default_filter: "Filtro padr\u00e3o", ed_list: "Lista",
    ed_title: "T\u00edtulo (opcional)", ed_title_placeholder: "Padr\u00e3o: nome da lista",
    ed_display: "Exibi\u00e7\u00e3o", ed_show_title: "T\u00edtulo", ed_show_progress: "Progresso",
    ed_show_due_date: "Prazo", ed_show_notes: "Notas", ed_show_recurrence: "Recorr\u00eancia",
    ed_show_sub_items: "Subtarefas", ed_show_person: "Pessoa",
    ed_auto_delete: "Excluir conclu\u00eddas imediatamente", ed_compact: "Compacto", ed_show_tags: "Etiquetas",
    ed_hint: "Novas listas podem ser criadas em Configura\u00e7\u00f5es \u2192 Integra\u00e7\u00f5es \u2192 Home Tasks.",
    tags: "Etiquetas", add_tag: "+ Adicionar etiqueta", tag_placeholder: "Nova etiqueta...", remove_tag: "Remover",
    new_sub_item: "Nova subtarefa", remove_reminder: "Remover lembrete",
    sort_label: "Ordenar", sort_manual: "Manual", sort_due: "Prazo",
    sort_priority: "Prioridade", sort_title: "T\u00edtulo (A\u2013Z)", sort_person: "Atribu\u00eddo",
    ed_show_sort: "Ordena\u00e7\u00e3o", ed_default_sort: "Ordena\u00e7\u00e3o padr\u00e3o",
    reminder: "Lembretes", rem_add: "+ Adicionar lembrete", rem_none: "Sem lembrete",
    rem_at_due: "No prazo", rem_5m: "5 min. antes", rem_15m: "15 min. antes",
    rem_30m: "30 min. antes", rem_1h: "1 hora antes", rem_2h: "2 horas antes",
    rem_1d: "1 dia antes", rem_2d: "2 dias antes",
    ed_show_reminders: "Lembretes", ed_add_column: "Adicionar coluna",
    ed_move_left: "Mover para esquerda", ed_move_right: "Mover para direita",
    ed_duplicate: "Duplicar coluna", ed_delete_column: "Excluir coluna",
    ed_code_editor: "Editor de c\u00f3digo", ed_visual_editor: "Editor visual",
    ed_icon: "\u00cdcone (opcional)", ed_card_title: "T\u00edtulo do cart\u00e3o (opcional)",
    ed_card_title_placeholder: "T\u00edtulo acima das colunas",
    ed_sec_view: "Exibi\u00e7\u00e3o", ed_sec_display: "Configura\u00e7\u00e3o",
    due_time_lbl: "Hora", due_date_lbl: "Data", rec_mode_lbl: "Modo",
    rec_time: "Hora", rec_end: "Fim", rec_end_never: "Nunca", rec_end_date: "Em data", rec_end_count: "Ap\u00f3s N vezes",
    rec_end_date_lbl: "Data de fim", rec_max_count_lbl: "max", rec_remaining: "ainda {0}", rec_start_date_lbl: "Data de in\u00edcio",
    history: "Hist\u00f3rico", history_created: "Criado", history_completed: "Conclu\u00eddo", history_reopened: "Reaberto",
    history_reset: "Reiniciado automaticamente", history_changed: "alterado", history_empty: "Sem hist\u00f3rico", hist_title: "T\u00edtulo", history_disabled: "Desativado",
    ed_show_history: "Mostrar hist\u00f3rico", hist_by_user: "Utilizador",
  },
  es: {
    my_tasks: "Mis tareas",
    add_placeholder: "A\u00f1adir nueva tarea...",
    filter_all: "Todas", filter_open: "Abiertas", filter_done: "Completadas",
    progress: "{0} de {1} completadas",
    empty: "Sin tareas",
    drag_handle: "Arrastrar para reordenar",
    due_date: "Vencimiento", notes: "Notas", notes_placeholder: "A\u00f1adir notas aqu\u00ed",
    sub_items: "Subtareas", add_sub_item: "+ A\u00f1adir subtarea",
    recurrence: "Recurrencia", recurrence_enabled: "Activada", recurrence_every: "Cada",
    rec_hours: "Horas", rec_days: "D\u00edas", rec_weeks: "Semanas", rec_months: "Meses",
    rec_short_h: "h", rec_short_d: "d", rec_short_w: "s", rec_short_m: "m",
    priority: "Prioridad", pri_high: "Alta", pri_medium: "Media", pri_low: "Baja",
    ed_show_priority: "Prioridad",
    rec_hourly: "Por hora", rec_daily: "Diaria", rec_weekly: "Semanal", rec_monthly: "Mensual",
    rec_type_interval: "Cada \u2026", rec_type_weekdays: "En d\u00edas laborables",
    rec_wd_0: "Lun", rec_wd_1: "Mar", rec_wd_2: "Mi\u00e9", rec_wd_3: "Jue", rec_wd_4: "Vie", rec_wd_5: "S\u00e1b", rec_wd_6: "Dom",
    assigned_to: "Asignado a", nobody: "\u2013 Nadie \u2013",
    delete_task: "Eliminar tarea", delete_sub: "Eliminar",
    ed_default_filter: "Filtro predeterminado", ed_list: "Lista",
    ed_title: "T\u00edtulo (opcional)", ed_title_placeholder: "Predeterminado: nombre de lista",
    ed_display: "Visualizaci\u00f3n", ed_show_title: "T\u00edtulo", ed_show_progress: "Progreso",
    ed_show_due_date: "Vencimiento", ed_show_notes: "Notas", ed_show_recurrence: "Recurrencia",
    ed_show_sub_items: "Subtareas", ed_show_person: "Persona",
    ed_auto_delete: "Eliminar completadas inmediatamente", ed_compact: "Compacto", ed_show_tags: "Etiquetas",
    ed_hint: "Se pueden crear nuevas listas en Configuraci\u00f3n \u2192 Integraciones \u2192 Home Tasks.",
    tags: "Etiquetas", add_tag: "+ A\u00f1adir etiqueta", tag_placeholder: "Nueva etiqueta...", remove_tag: "Eliminar",
    new_sub_item: "Nueva subtarea", remove_reminder: "Eliminar recordatorio",
    sort_label: "Ordenar", sort_manual: "Manual", sort_due: "Vencimiento",
    sort_priority: "Prioridad", sort_title: "T\u00edtulo (A\u2013Z)", sort_person: "Asignado",
    ed_show_sort: "Ordenaci\u00f3n", ed_default_sort: "Ordenaci\u00f3n predeterminada",
    reminder: "Recordatorios", rem_add: "+ A\u00f1adir recordatorio", rem_none: "Sin recordatorio",
    rem_at_due: "A la hora de vencimiento", rem_5m: "5 min. antes", rem_15m: "15 min. antes",
    rem_30m: "30 min. antes", rem_1h: "1 hora antes", rem_2h: "2 horas antes",
    rem_1d: "1 d\u00eda antes", rem_2d: "2 d\u00edas antes",
    ed_show_reminders: "Recordatorios", ed_add_column: "A\u00f1adir columna",
    ed_move_left: "Mover a la izquierda", ed_move_right: "Mover a la derecha",
    ed_duplicate: "Duplicar columna", ed_delete_column: "Eliminar columna",
    ed_code_editor: "Editor de c\u00f3digo", ed_visual_editor: "Editor visual",
    ed_icon: "Icono (opcional)", ed_card_title: "T\u00edtulo de la tarjeta (opcional)",
    ed_card_title_placeholder: "T\u00edtulo sobre las columnas",
    ed_sec_view: "Visualizaci\u00f3n", ed_sec_display: "Configuraci\u00f3n",
    due_time_lbl: "Hora", due_date_lbl: "Fecha", rec_mode_lbl: "Modo",
    rec_time: "Hora", rec_end: "Fin", rec_end_never: "Nunca", rec_end_date: "En fecha", rec_end_count: "Despu\u00e9s de N veces",
    rec_end_date_lbl: "Fecha de fin", rec_max_count_lbl: "max", rec_remaining: "a\u00fan {0}", rec_start_date_lbl: "Fecha de inicio",
    history: "Historial", history_created: "Creado", history_completed: "Completado", history_reopened: "Reabierto",
    history_reset: "Restablecimiento autom.", history_changed: "modificado", history_empty: "Sin historial", hist_title: "T\u00edtulo", history_disabled: "Desactivado",
    ed_show_history: "Mostrar historial", hist_by_user: "Usuario",
  },
  ru: {
    my_tasks: "\u041c\u043e\u0438 \u0437\u0430\u0434\u0430\u0447\u0438",
    add_placeholder: "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0437\u0430\u0434\u0430\u0447\u0443...",
    filter_all: "\u0412\u0441\u0435", filter_open: "\u041e\u0442\u043a\u0440\u044b\u0442\u044b\u0435", filter_done: "\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u0435",
    progress: "{0} \u0438\u0437 {1} \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e",
    empty: "\u041d\u0435\u0442 \u0437\u0430\u0434\u0430\u0447",
    drag_handle: "\u041f\u0435\u0440\u0435\u0442\u0430\u0449\u0438\u0442\u044c \u0434\u043b\u044f \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u043f\u043e\u0440\u044f\u0434\u043a\u0430",
    due_date: "\u0421\u0440\u043e\u043a", notes: "\u0417\u0430\u043c\u0435\u0442\u043a\u0438", notes_placeholder: "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043c\u0435\u0442\u043a\u0438 \u0437\u0434\u0435\u0441\u044c",
    sub_items: "\u041f\u043e\u0434\u0437\u0430\u0434\u0430\u0447\u0438", add_sub_item: "+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u043e\u0434\u0437\u0430\u0434\u0430\u0447\u0443",
    recurrence: "\u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u0435", recurrence_enabled: "\u0412\u043a\u043b\u044e\u0447\u0435\u043d\u043e", recurrence_every: "\u041a\u0430\u0436\u0434\u044b\u0435",
    rec_hours: "\u0427\u0430\u0441\u044b", rec_days: "\u0414\u043d\u0438", rec_weeks: "\u041d\u0435\u0434\u0435\u043b\u0438", rec_months: "\u041c\u0435\u0441\u044f\u0446\u044b",
    rec_short_h: "\u0447", rec_short_d: "\u0434", rec_short_w: "\u043d", rec_short_m: "\u043c",
    priority: "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442", pri_high: "\u0412\u044b\u0441\u043e\u043a\u0438\u0439", pri_medium: "\u0421\u0440\u0435\u0434\u043d\u0438\u0439", pri_low: "\u041d\u0438\u0437\u043a\u0438\u0439",
    ed_show_priority: "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442",
    rec_hourly: "\u0415\u0436\u0435\u0447\u0430\u0441\u043d\u043e", rec_daily: "\u0415\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u043e", rec_weekly: "\u0415\u0436\u0435\u043d\u0435\u0434\u0435\u043b\u044c\u043d\u043e", rec_monthly: "\u0415\u0436\u0435\u043c\u0435\u0441\u044f\u0447\u043d\u043e",
    rec_type_interval: "\u041a\u0430\u0436\u0434\u044b\u0435 \u2026", rec_type_weekdays: "\u041f\u043e \u0431\u0443\u0434\u043d\u044f\u043c",
    rec_wd_0: "\u041f\u043d", rec_wd_1: "\u0412\u0442", rec_wd_2: "\u0421\u0440", rec_wd_3: "\u0427\u0442", rec_wd_4: "\u041f\u0442", rec_wd_5: "\u0421\u0431", rec_wd_6: "\u0412\u0441",
    assigned_to: "\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u043e", nobody: "\u2013 \u041d\u0438\u043a\u0442\u043e \u2013",
    delete_task: "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", delete_sub: "\u0423\u0434\u0430\u043b\u0438\u0442\u044c",
    ed_default_filter: "\u0424\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e", ed_list: "\u0421\u043f\u0438\u0441\u043e\u043a",
    ed_title: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a (\u043d\u0435\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e)", ed_title_placeholder: "\u041f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e: \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u043f\u0438\u0441\u043a\u0430",
    ed_display: "\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435", ed_show_title: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a", ed_show_progress: "\u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441",
    ed_show_due_date: "\u0421\u0440\u043e\u043a", ed_show_notes: "\u0417\u0430\u043c\u0435\u0442\u043a\u0438", ed_show_recurrence: "\u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u0435",
    ed_show_sub_items: "\u041f\u043e\u0434\u0437\u0430\u0434\u0430\u0447\u0438", ed_show_person: "\u041f\u0435\u0440\u0441\u043e\u043d\u0430",
    ed_auto_delete: "\u0421\u0440\u0430\u0437\u0443 \u0443\u0434\u0430\u043b\u044f\u0442\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u0435", ed_compact: "\u041a\u043e\u043c\u043f\u0430\u043a\u0442\u043d\u044b\u0439", ed_show_tags: "\u0422\u0435\u0433\u0438",
    ed_hint: "\u041d\u043e\u0432\u044b\u0435 \u0441\u043f\u0438\u0441\u043a\u0438 \u043c\u043e\u0436\u043d\u043e \u0441\u043e\u0437\u0434\u0430\u0442\u044c \u0432 \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u2192 \u0418\u043d\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u0438 \u2192 Home Tasks.",
    tags: "\u0422\u0435\u0433\u0438", add_tag: "+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0442\u0435\u0433", tag_placeholder: "\u041d\u043e\u0432\u044b\u0439 \u0442\u0435\u0433...", remove_tag: "\u0423\u0434\u0430\u043b\u0438\u0442\u044c",
    new_sub_item: "\u041d\u043e\u0432\u0430\u044f \u043f\u043e\u0434\u0437\u0430\u0434\u0430\u0447\u0430", remove_reminder: "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435",
    sort_label: "\u0421\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430", sort_manual: "\u0412\u0440\u0443\u0447\u043d\u0443\u044e", sort_due: "\u0421\u0440\u043e\u043a",
    sort_priority: "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442", sort_title: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a (\u0410\u2013\u042f)", sort_person: "\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u043e",
    ed_show_sort: "\u0421\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430", ed_default_sort: "\u0421\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e",
    reminder: "\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f", rem_add: "+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435", rem_none: "\u041d\u0435\u0442 \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f",
    rem_at_due: "\u0412 \u0441\u0440\u043e\u043a", rem_5m: "\u0417\u0430 5 \u043c\u0438\u043d.", rem_15m: "\u0417\u0430 15 \u043c\u0438\u043d.",
    rem_30m: "\u0417\u0430 30 \u043c\u0438\u043d.", rem_1h: "\u0417\u0430 1 \u0447\u0430\u0441", rem_2h: "\u0417\u0430 2 \u0447\u0430\u0441\u0430",
    rem_1d: "\u0417\u0430 1 \u0434\u0435\u043d\u044c", rem_2d: "\u0417\u0430 2 \u0434\u043d\u044f",
    ed_show_reminders: "\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f", ed_add_column: "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0441\u0442\u043e\u043b\u0431\u0435\u0446",
    ed_move_left: "\u0412\u043b\u0435\u0432\u043e", ed_move_right: "\u0412\u043f\u0440\u0430\u0432\u043e",
    ed_duplicate: "\u0414\u0443\u0431\u043b\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u0442\u043e\u043b\u0431\u0435\u0446", ed_delete_column: "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0441\u0442\u043e\u043b\u0431\u0435\u0446",
    ed_code_editor: "\u0420\u0435\u0434\u0430\u043a\u0442\u043e\u0440 \u043a\u043e\u0434\u0430", ed_visual_editor: "\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0440\u0435\u0434\u0430\u043a\u0442\u043e\u0440",
    ed_icon: "\u0418\u043a\u043e\u043d\u043a\u0430 (\u043d\u0435\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e)", ed_card_title: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u043a\u0430\u0440\u0442\u043e\u0447\u043a\u0438 (\u043d\u0435\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e)",
    ed_card_title_placeholder: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u043d\u0430\u0434 \u0441\u0442\u043e\u043b\u0431\u0446\u0430\u043c\u0438",
    ed_sec_view: "\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435", ed_sec_display: "\u041a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u044f",
    due_time_lbl: "\u0412\u0440\u0435\u043c\u044f", due_date_lbl: "\u0414\u0430\u0442\u0430", rec_mode_lbl: "\u0420\u0435\u0436\u0438\u043c",
    rec_time: "\u0412\u0440\u0435\u043c\u044f", rec_end: "\u041e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u0435", rec_end_never: "\u041d\u0438\u043a\u043e\u0433\u0434\u0430", rec_end_date: "\u041f\u043e \u0434\u0430\u0442\u0435", rec_end_count: "\u041f\u043e\u0441\u043b\u0435 N \u0440\u0430\u0437",
    rec_end_date_lbl: "\u0414\u0430\u0442\u0430 \u043e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u044f", rec_max_count_lbl: "max", rec_remaining: "\u0435\u0449\u0451 {0}", rec_start_date_lbl: "\u0414\u0430\u0442\u0430 \u043d\u0430\u0447\u0430\u043b\u0430",
    history: "\u0418\u0441\u0442\u043e\u0440\u0438\u044f", history_created: "\u0421\u043e\u0437\u0434\u0430\u043d\u043e", history_completed: "\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e", history_reopened: "\u041f\u0435\u0440\u0435\u043e\u0442\u043a\u0440\u044b\u0442\u043e",
    history_reset: "\u0410\u0432\u0442\u043e\u0441\u0431\u0440\u043e\u0441", history_changed: "\u0438\u0437\u043c\u0435\u043d\u0435\u043d\u043e", history_empty: "\u041d\u0435\u0442 \u0438\u0441\u0442\u043e\u0440\u0438\u0438", hist_title: "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a", history_disabled: "\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u043e",
    ed_show_history: "\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0438\u0441\u0442\u043e\u0440\u0438\u044e", hist_by_user: "\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c",
  },
  cs: {
    my_tasks: "Moje \u00fakoly",
    add_placeholder: "P\u0159idat nov\u00fd \u00fakol...",
    filter_all: "V\u0161e", filter_open: "Otev\u0159en\u00e9", filter_done: "Dokon\u010den\u00e9",
    progress: "{0} z {1} dokon\u010deno",
    empty: "\u017d\u00e1dn\u00e9 \u00fakoly",
    drag_handle: "P\u0159et\u00e1hnout pro zm\u011bnu po\u0159ad\u00ed",
    due_date: "Term\u00edn", notes: "Pozn\u00e1mky", notes_placeholder: "P\u0159idat pozn\u00e1mky zde",
    sub_items: "Pod\u00fakoly", add_sub_item: "+ P\u0159idat pod\u00fakol",
    recurrence: "Opakov\u00e1n\u00ed", recurrence_enabled: "Povoleno", recurrence_every: "Ka\u017ed\u00fd",
    rec_hours: "Hodiny", rec_days: "Dny", rec_weeks: "T\u00fddny", rec_months: "M\u011bs\u00edce",
    rec_short_h: "h", rec_short_d: "d", rec_short_w: "t", rec_short_m: "m",
    priority: "Priorita", pri_high: "Vysok\u00e1", pri_medium: "St\u0159edn\u00ed", pri_low: "N\u00edzk\u00e1",
    ed_show_priority: "Priorita",
    rec_hourly: "Hodinov\u011b", rec_daily: "Denn\u011b", rec_weekly: "T\u00fddn\u011b", rec_monthly: "M\u011bs\u00ed\u010dn\u011b",
    rec_type_interval: "Ka\u017ed\u00fd \u2026", rec_type_weekdays: "Ve v\u0161ední dny",
    rec_wd_0: "Po", rec_wd_1: "\u00dat", rec_wd_2: "St", rec_wd_3: "\u010ct", rec_wd_4: "P\u00e1", rec_wd_5: "So", rec_wd_6: "Ne",
    assigned_to: "P\u0159i\u0159azeno", nobody: "\u2013 Nikdo \u2013",
    delete_task: "Smazat \u00fakol", delete_sub: "Smazat",
    ed_default_filter: "V\u00fdchoz\u00ed filtr", ed_list: "Seznam",
    ed_title: "N\u00e1zev (voliteln\u011b)", ed_title_placeholder: "V\u00fdchoz\u00ed: n\u00e1zev seznamu",
    ed_display: "Zobrazen\u00ed", ed_show_title: "N\u00e1zev", ed_show_progress: "Pokrok",
    ed_show_due_date: "Term\u00edn", ed_show_notes: "Pozn\u00e1mky", ed_show_recurrence: "Opakov\u00e1n\u00ed",
    ed_show_sub_items: "Pod\u00fakoly", ed_show_person: "Osoba",
    ed_auto_delete: "Okam\u017eit\u011b smazat dokon\u010den\u00e9", ed_compact: "Kompaktn\u00ed", ed_show_tags: "\u0160t\u00edtky",
    ed_hint: "Nov\u00e9 seznamy lze vytvo\u0159it v Nastaven\u00ed \u2192 Integrace \u2192 Home Tasks.",
    tags: "\u0160t\u00edtky", add_tag: "+ P\u0159idat \u0161t\u00edtek", tag_placeholder: "Nov\u00fd \u0161t\u00edtek...", remove_tag: "Odebrat",
    new_sub_item: "Nov\u00fd pod\u00fakol", remove_reminder: "Odebrat p\u0159ipom\u00ednku",
    sort_label: "\u0158adit", sort_manual: "Ru\u010dn\u011b", sort_due: "Term\u00edn",
    sort_priority: "Priorita", sort_title: "N\u00e1zev (A\u2013Z)", sort_person: "P\u0159i\u0159azeno",
    ed_show_sort: "\u0158azen\u00ed", ed_default_sort: "V\u00fdchoz\u00ed \u0159azen\u00ed",
    reminder: "P\u0159ipom\u00ednky", rem_add: "+ P\u0159idat p\u0159ipom\u00ednku", rem_none: "Bez p\u0159ipom\u00ednky",
    rem_at_due: "V \u010das term\u00ednu", rem_5m: "5 min. p\u0159ed", rem_15m: "15 min. p\u0159ed",
    rem_30m: "30 min. p\u0159ed", rem_1h: "1 hod. p\u0159ed", rem_2h: "2 hod. p\u0159ed",
    rem_1d: "1 den p\u0159ed", rem_2d: "2 dny p\u0159ed",
    ed_show_reminders: "P\u0159ipom\u00ednky", ed_add_column: "P\u0159idat sloupec",
    ed_move_left: "P\u0159esunout vlevo", ed_move_right: "P\u0159esunout vpravo",
    ed_duplicate: "Duplikovat sloupec", ed_delete_column: "Smazat sloupec",
    ed_code_editor: "Editor k\u00f3du", ed_visual_editor: "Vizu\u00e1ln\u00ed editor",
    ed_icon: "Ikona (voliteln\u011b)", ed_card_title: "N\u00e1zev karty (voliteln\u011b)",
    ed_card_title_placeholder: "N\u00e1zev nad sloupci",
    ed_sec_view: "Zobrazen\u00ed", ed_sec_display: "Konfigurace",
    due_time_lbl: "\u010cas", due_date_lbl: "Datum", rec_mode_lbl: "Re\u017eim",
    rec_time: "\u010cas", rec_end: "Konec", rec_end_never: "Nikdy", rec_end_date: "K datu", rec_end_count: "Po N kr\u00e1t",
    rec_end_date_lbl: "Datum konce", rec_max_count_lbl: "max", rec_remaining: "je\u0161t\u011b {0}", rec_start_date_lbl: "Datum za\u010d\u00e1tku",
    history: "Historie", history_created: "Vytvo\u0159eno", history_completed: "Dokon\u010deno", history_reopened: "Znovu otev\u0159eno",
    history_reset: "Automaticky obnoveno", history_changed: "zm\u011bn\u011bno", history_empty: "\u017d\u00e1dn\u00e1 historie", hist_title: "N\u00e1zev", history_disabled: "Deaktivov\u00e1no",
    ed_show_history: "Zobrazit historii", hist_by_user: "U\u017eivatel",
  },
  da: {
    my_tasks: "Mine opgaver",
    add_placeholder: "Tilf\u00f8j ny opgave...",
    filter_all: "Alle", filter_open: "\u00c5bne", filter_done: "F\u00e6rdige",
    progress: "{0} af {1} f\u00e6rdige",
    empty: "Ingen opgaver",
    drag_handle: "Tr\u00e6k for at sortere",
    due_date: "Forfald", notes: "Noter", notes_placeholder: "Tilf\u00f8j noter her",
    sub_items: "Delopgaver", add_sub_item: "+ Tilf\u00f8j delopgave",
    recurrence: "Gentagelse", recurrence_enabled: "Aktiveret", recurrence_every: "Hver",
    rec_hours: "Timer", rec_days: "Dage", rec_weeks: "Uger", rec_months: "M\u00e5neder",
    rec_short_h: "t", rec_short_d: "d", rec_short_w: "u", rec_short_m: "md",
    priority: "Prioritet", pri_high: "H\u00f8j", pri_medium: "Mellem", pri_low: "Lav",
    ed_show_priority: "Prioritet",
    rec_hourly: "Hver time", rec_daily: "Dagligt", rec_weekly: "Ugentligt", rec_monthly: "M\u00e5nedligt",
    rec_type_interval: "Hver \u2026", rec_type_weekdays: "P\u00e5 hverdage",
    rec_wd_0: "Man", rec_wd_1: "Tir", rec_wd_2: "Ons", rec_wd_3: "Tor", rec_wd_4: "Fre", rec_wd_5: "L\u00f8r", rec_wd_6: "S\u00f8n",
    assigned_to: "Tildelt", nobody: "\u2013 Ingen \u2013",
    delete_task: "Slet opgave", delete_sub: "Slet",
    ed_default_filter: "Standardfilter", ed_list: "Liste",
    ed_title: "Titel (valgfrit)", ed_title_placeholder: "Standard: listenavn",
    ed_display: "Visning", ed_show_title: "Titel", ed_show_progress: "Fremgang",
    ed_show_due_date: "Forfald", ed_show_notes: "Noter", ed_show_recurrence: "Gentagelse",
    ed_show_sub_items: "Delopgaver", ed_show_person: "Person",
    ed_auto_delete: "Slet f\u00e6rdige \u00f8jeblikkeligt", ed_compact: "Kompakt", ed_show_tags: "Tags",
    ed_hint: "Nye lister kan oprettes under Indstillinger \u2192 Integrationer \u2192 Home Tasks.",
    tags: "Tags", add_tag: "+ Tilf\u00f8j tag", tag_placeholder: "Nyt tag...", remove_tag: "Fjern",
    new_sub_item: "Ny delopgave", remove_reminder: "Fjern p\u00e5mindelse",
    sort_label: "Sorter", sort_manual: "Manuel", sort_due: "Forfald",
    sort_priority: "Prioritet", sort_title: "Titel (A\u2013Z)", sort_person: "Tildelt",
    ed_show_sort: "Sortering", ed_default_sort: "Standardsortering",
    reminder: "P\u00e5mindelser", rem_add: "+ Tilf\u00f8j p\u00e5mindelse", rem_none: "Ingen p\u00e5mindelse",
    rem_at_due: "Ved forfaldstid", rem_5m: "5 min. f\u00f8r", rem_15m: "15 min. f\u00f8r",
    rem_30m: "30 min. f\u00f8r", rem_1h: "1 time f\u00f8r", rem_2h: "2 timer f\u00f8r",
    rem_1d: "1 dag f\u00f8r", rem_2d: "2 dage f\u00f8r",
    ed_show_reminders: "P\u00e5mindelser", ed_add_column: "Tilf\u00f8j kolonne",
    ed_move_left: "Flyt til venstre", ed_move_right: "Flyt til h\u00f8jre",
    ed_duplicate: "Dupliker kolonne", ed_delete_column: "Slet kolonne",
    ed_code_editor: "Kodeeditor", ed_visual_editor: "Visuel editor",
    ed_icon: "Ikon (valgfrit)", ed_card_title: "Korttitel (valgfrit)",
    ed_card_title_placeholder: "Titel over kolonner",
    ed_sec_view: "Visning", ed_sec_display: "Konfiguration",
    due_time_lbl: "Tid", due_date_lbl: "Dato", rec_mode_lbl: "Tilstand",
    rec_time: "Tidspunkt", rec_end: "Slut", rec_end_never: "Aldrig", rec_end_date: "P\u00e5 dato", rec_end_count: "Efter N gange",
    rec_end_date_lbl: "Slutdato", rec_max_count_lbl: "max", rec_remaining: "{0} tilbage", rec_start_date_lbl: "Startdato",
    history: "Historik", history_created: "Oprettet", history_completed: "F\u00e6rdiggjort", history_reopened: "\u00c5bnet igen",
    history_reset: "Auto-nulstillet", history_changed: "\u00e6ndret", history_empty: "Ingen historik", hist_title: "Titel", history_disabled: "Deaktiveret",
    ed_show_history: "Vis historik", hist_by_user: "Bruger",
  },
  no: {
    my_tasks: "Mine oppgaver",
    add_placeholder: "Legg til ny oppgave...",
    filter_all: "Alle", filter_open: "\u00c5pne", filter_done: "Ferdige",
    progress: "{0} av {1} ferdige",
    empty: "Ingen oppgaver",
    drag_handle: "Dra for \u00e5 endre rekkefl\u00f8lge",
    due_date: "Frist", notes: "Notater", notes_placeholder: "Legg til notater her",
    sub_items: "Deloppgaver", add_sub_item: "+ Legg til deloppgave",
    recurrence: "Gjentakelse", recurrence_enabled: "Aktivert", recurrence_every: "Hver",
    rec_hours: "Timer", rec_days: "Dager", rec_weeks: "Uker", rec_months: "M\u00e5neder",
    rec_short_h: "t", rec_short_d: "d", rec_short_w: "u", rec_short_m: "md",
    priority: "Prioritet", pri_high: "H\u00f8y", pri_medium: "Middels", pri_low: "Lav",
    ed_show_priority: "Prioritet",
    rec_hourly: "Hver time", rec_daily: "Daglig", rec_weekly: "Ukentlig", rec_monthly: "M\u00e5nedlig",
    rec_type_interval: "Hver \u2026", rec_type_weekdays: "P\u00e5 hverdager",
    rec_wd_0: "Man", rec_wd_1: "Tir", rec_wd_2: "Ons", rec_wd_3: "Tor", rec_wd_4: "Fre", rec_wd_5: "L\u00f8r", rec_wd_6: "S\u00f8n",
    assigned_to: "Tildelt", nobody: "\u2013 Ingen \u2013",
    delete_task: "Slett oppgave", delete_sub: "Slett",
    ed_default_filter: "Standardfilter", ed_list: "Liste",
    ed_title: "Tittel (valgfritt)", ed_title_placeholder: "Standard: listenavn",
    ed_display: "Visning", ed_show_title: "Tittel", ed_show_progress: "Fremgang",
    ed_show_due_date: "Frist", ed_show_notes: "Notater", ed_show_recurrence: "Gjentakelse",
    ed_show_sub_items: "Deloppgaver", ed_show_person: "Person",
    ed_auto_delete: "Slett ferdige umiddelbart", ed_compact: "Kompakt", ed_show_tags: "Tagger",
    ed_hint: "Nye lister kan opprettes under Innstillinger \u2192 Integrasjoner \u2192 Home Tasks.",
    tags: "Tagger", add_tag: "+ Legg til tagg", tag_placeholder: "Ny tagg...", remove_tag: "Fjern",
    new_sub_item: "Ny deloppgave", remove_reminder: "Fjern p\u00e5minnelse",
    sort_label: "Sorter", sort_manual: "Manuell", sort_due: "Frist",
    sort_priority: "Prioritet", sort_title: "Tittel (A\u2013Z)", sort_person: "Tildelt",
    ed_show_sort: "Sortering", ed_default_sort: "Standardsortering",
    reminder: "P\u00e5minnelser", rem_add: "+ Legg til p\u00e5minnelse", rem_none: "Ingen p\u00e5minnelse",
    rem_at_due: "Ved fristen", rem_5m: "5 min. f\u00f8r", rem_15m: "15 min. f\u00f8r",
    rem_30m: "30 min. f\u00f8r", rem_1h: "1 time f\u00f8r", rem_2h: "2 timer f\u00f8r",
    rem_1d: "1 dag f\u00f8r", rem_2d: "2 dager f\u00f8r",
    ed_show_reminders: "P\u00e5minnelser", ed_add_column: "Legg til kolonne",
    ed_move_left: "Flytt til venstre", ed_move_right: "Flytt til h\u00f8yre",
    ed_duplicate: "Dupliser kolonne", ed_delete_column: "Slett kolonne",
    ed_code_editor: "Kodeeditor", ed_visual_editor: "Visuell editor",
    ed_icon: "Ikon (valgfritt)", ed_card_title: "Korttittel (valgfritt)",
    ed_card_title_placeholder: "Tittel over kolonner",
    ed_sec_view: "Visning", ed_sec_display: "Konfigurasjon",
    due_time_lbl: "Tid", due_date_lbl: "Dato", rec_mode_lbl: "Modus",
    rec_time: "Klokkeslett", rec_end: "Slutt", rec_end_never: "Aldri", rec_end_date: "P\u00e5 dato", rec_end_count: "Etter N ganger",
    rec_end_date_lbl: "Sluttdato", rec_max_count_lbl: "max", rec_remaining: "{0} igjen", rec_start_date_lbl: "Startdato",
    history: "Historikk", history_created: "Opprettet", history_completed: "Fullf\u00f8rt", history_reopened: "\u00c5pnet igjen",
    history_reset: "Auto-tilbakestilt", history_changed: "endret", history_empty: "Ingen historikk", hist_title: "Tittel", history_disabled: "Deaktivert",
    ed_show_history: "Vis historikk", hist_by_user: "Bruker",
  },
  fi: {
    my_tasks: "Omat teht\u00e4v\u00e4t",
    add_placeholder: "Lis\u00e4\u00e4 uusi teht\u00e4v\u00e4...",
    filter_all: "Kaikki", filter_open: "Avoimet", filter_done: "Valmiit",
    progress: "{0} / {1} valmis",
    empty: "Ei teht\u00e4vi\u00e4",
    drag_handle: "Vet\u00e4\u00e4 j\u00e4rjest\u00e4\u00e4ksesi",
    due_date: "Er\u00e4p\u00e4iv\u00e4", notes: "Muistiinpanot", notes_placeholder: "Lis\u00e4\u00e4 muistiinpanoja t\u00e4h\u00e4n",
    sub_items: "Aliteht\u00e4v\u00e4t", add_sub_item: "+ Lis\u00e4\u00e4 aliteht\u00e4v\u00e4",
    recurrence: "Toistuvuus", recurrence_enabled: "K\u00e4yt\u00f6ss\u00e4", recurrence_every: "Joka",
    rec_hours: "Tunnit", rec_days: "P\u00e4iv\u00e4t", rec_weeks: "Viikot", rec_months: "Kuukaudet",
    rec_short_h: "t", rec_short_d: "p", rec_short_w: "v", rec_short_m: "kk",
    priority: "Prioriteetti", pri_high: "Korkea", pri_medium: "Keskitaso", pri_low: "Matala",
    ed_show_priority: "Prioriteetti",
    rec_hourly: "Tunneittain", rec_daily: "P\u00e4ivitt\u00e4in", rec_weekly: "Viikoittain", rec_monthly: "Kuukausittain",
    rec_type_interval: "Joka \u2026", rec_type_weekdays: "Arkip\u00e4ivin\u00e4",
    rec_wd_0: "Ma", rec_wd_1: "Ti", rec_wd_2: "Ke", rec_wd_3: "To", rec_wd_4: "Pe", rec_wd_5: "La", rec_wd_6: "Su",
    assigned_to: "M\u00e4\u00e4ritetty", nobody: "\u2013 Ei ket\u00e4\u00e4n \u2013",
    delete_task: "Poista teht\u00e4v\u00e4", delete_sub: "Poista",
    ed_default_filter: "Oletussuodatin", ed_list: "Lista",
    ed_title: "Otsikko (valinnainen)", ed_title_placeholder: "Oletus: listan nimi",
    ed_display: "N\u00e4ytt\u00f6", ed_show_title: "Otsikko", ed_show_progress: "Edistyminen",
    ed_show_due_date: "Er\u00e4p\u00e4iv\u00e4", ed_show_notes: "Muistiinpanot", ed_show_recurrence: "Toistuvuus",
    ed_show_sub_items: "Aliteht\u00e4v\u00e4t", ed_show_person: "Henkil\u00f6",
    ed_auto_delete: "Poista valmiit v\u00e4litt\u00f6m\u00e4sti", ed_compact: "Kompakti", ed_show_tags: "Tunnisteet",
    ed_hint: "Uusia listoja voi luoda kohdassa Asetukset \u2192 Integraatiot \u2192 Home Tasks.",
    tags: "Tunnisteet", add_tag: "+ Lis\u00e4\u00e4 tunniste", tag_placeholder: "Uusi tunniste...", remove_tag: "Poista",
    new_sub_item: "Uusi aliteht\u00e4v\u00e4", remove_reminder: "Poista muistutus",
    sort_label: "Lajittele", sort_manual: "Manuaalinen", sort_due: "Er\u00e4p\u00e4iv\u00e4",
    sort_priority: "Prioriteetti", sort_title: "Otsikko (A\u2013\u00d6)", sort_person: "M\u00e4\u00e4ritetty",
    ed_show_sort: "Lajittelu", ed_default_sort: "Oletuslajittelu",
    reminder: "Muistutukset", rem_add: "+ Lis\u00e4\u00e4 muistutus", rem_none: "Ei muistutusta",
    rem_at_due: "Er\u00e4ajalla", rem_5m: "5 min. ennen", rem_15m: "15 min. ennen",
    rem_30m: "30 min. ennen", rem_1h: "1 tunti ennen", rem_2h: "2 tuntia ennen",
    rem_1d: "1 p\u00e4iv\u00e4 ennen", rem_2d: "2 p\u00e4iv\u00e4\u00e4 ennen",
    ed_show_reminders: "Muistutukset", ed_add_column: "Lis\u00e4\u00e4 sarake",
    ed_move_left: "Siirr\u00e4 vasemmalle", ed_move_right: "Siirr\u00e4 oikealle",
    ed_duplicate: "Kopioi sarake", ed_delete_column: "Poista sarake",
    ed_code_editor: "Koodieditori", ed_visual_editor: "Visuaalinen editori",
    ed_icon: "Kuvake (valinnainen)", ed_card_title: "Kortin otsikko (valinnainen)",
    ed_card_title_placeholder: "Otsikko sarakkeiden yl\u00e4puolella",
    ed_sec_view: "N\u00e4ytt\u00f6", ed_sec_display: "Konfiguraatio",
    due_time_lbl: "Aika", due_date_lbl: "P\u00e4iv\u00e4m\u00e4\u00e4r\u00e4", rec_mode_lbl: "Tila",
    rec_time: "Aika", rec_end: "Loppu", rec_end_never: "Ei koskaan", rec_end_date: "P\u00e4iv\u00e4m\u00e4\u00e4r\u00e4n\u00e4", rec_end_count: "N kerran j\u00e4lkeen",
    rec_end_date_lbl: "Loppup\u00e4iv\u00e4", rec_max_count_lbl: "max", rec_remaining: "{0} j\u00e4ljell\u00e4", rec_start_date_lbl: "Alkamisp\u00e4iv\u00e4",
    history: "Historia", history_created: "Luotu", history_completed: "Valmis", history_reopened: "Avattu uudelleen",
    history_reset: "Automaattinen palautus", history_changed: "muutettu", history_empty: "Ei historiaa", hist_title: "Otsikko", history_disabled: "K\u00e4yt\u00f6ss\u00e4 poistettu",
    ed_show_history: "N\u00e4yt\u00e4 historia", hist_by_user: "K\u00e4ytt\u00e4j\u00e4",
  },
  hu: {
    my_tasks: "Feladataim",
    add_placeholder: "\u00daj feladat hozz\u00e1ad\u00e1sa...",
    filter_all: "\u00d6sszes", filter_open: "Nyitott", filter_done: "K\u00e9sz",
    progress: "{0} / {1} k\u00e9sz",
    empty: "Nincsenek feladatok",
    drag_handle: "H\u00fazza az \u00e1trendez\u00e9shez",
    due_date: "Hat\u00e1rid\u0151", notes: "Megjegyz\u00e9sek", notes_placeholder: "Megjegyz\u00e9sek hozz\u00e1ad\u00e1sa",
    sub_items: "Alfeladatok", add_sub_item: "+ Alfeladat hozz\u00e1ad\u00e1sa",
    recurrence: "Ism\u00e9tl\u00e9s", recurrence_enabled: "Enged\u00e9lyezve", recurrence_every: "Minden",
    rec_hours: "\u00d3ra", rec_days: "Nap", rec_weeks: "H\u00e9t", rec_months: "H\u00f3nap",
    rec_short_h: "\u00f3", rec_short_d: "n", rec_short_w: "h", rec_short_m: "h\u00f3",
    priority: "Priorit\u00e1s", pri_high: "Magas", pri_medium: "K\u00f6zepes", pri_low: "Alacsony",
    ed_show_priority: "Priorit\u00e1s",
    rec_hourly: "\u00d3r\u00e1nk\u00e9nt", rec_daily: "Naponta", rec_weekly: "Hetente", rec_monthly: "Havonta",
    rec_type_interval: "Minden \u2026", rec_type_weekdays: "Munkanapokon",
    rec_wd_0: "H", rec_wd_1: "K", rec_wd_2: "Sze", rec_wd_3: "Cs", rec_wd_4: "P", rec_wd_5: "Szo", rec_wd_6: "V",
    assigned_to: "Hozz\u00e1rendelve", nobody: "\u2013 Senki \u2013",
    delete_task: "Feladat t\u00f6rl\u00e9se", delete_sub: "T\u00f6rl\u00e9s",
    ed_default_filter: "Alap\u00e9rtelmezett sz\u0171r\u0151", ed_list: "Lista",
    ed_title: "C\u00edm (nem k\u00f6telez\u0151)", ed_title_placeholder: "Alap\u00e9rtelmezett: lista neve",
    ed_display: "Megjelen\u00edt\u00e9s", ed_show_title: "C\u00edm", ed_show_progress: "Halad\u00e1s",
    ed_show_due_date: "Hat\u00e1rid\u0151", ed_show_notes: "Megjegyz\u00e9sek", ed_show_recurrence: "Ism\u00e9tl\u00e9s",
    ed_show_sub_items: "Alfeladatok", ed_show_person: "Szem\u00e9ly",
    ed_auto_delete: "K\u00e9sz feladatok azonnali t\u00f6rl\u00e9se", ed_compact: "Kompakt", ed_show_tags: "C\u00edmk\u00e9k",
    ed_hint: "\u00daj list\u00e1k a Be\u00e1ll\u00edt\u00e1sok \u2192 Integr\u00e1ci\u00f3k \u2192 Home Tasks alatt hozhat\u00f3k l\u00e9tre.",
    tags: "C\u00edmk\u00e9k", add_tag: "+ C\u00edmke hozz\u00e1ad\u00e1sa", tag_placeholder: "\u00daj c\u00edmke...", remove_tag: "Elt\u00e1vol\u00edt\u00e1s",
    new_sub_item: "\u00daj alfeladat", remove_reminder: "Eml\u00e9keztet\u0151 elt\u00e1vol\u00edt\u00e1sa",
    sort_label: "Rendez\u00e9s", sort_manual: "Manu\u00e1lis", sort_due: "Hat\u00e1rid\u0151",
    sort_priority: "Priorit\u00e1s", sort_title: "C\u00edm (A\u2013Z)", sort_person: "Hozz\u00e1rendelve",
    ed_show_sort: "Rendez\u00e9s", ed_default_sort: "Alap\u00e9rtelmezett rendez\u00e9s",
    reminder: "Eml\u00e9keztet\u0151k", rem_add: "+ Eml\u00e9keztet\u0151 hozz\u00e1ad\u00e1sa", rem_none: "Nincs eml\u00e9keztet\u0151",
    rem_at_due: "A hat\u00e1rid\u0151kor", rem_5m: "5 perccel el\u0151tte", rem_15m: "15 perccel el\u0151tte",
    rem_30m: "30 perccel el\u0151tte", rem_1h: "1 \u00f3r\u00e1val el\u0151tte", rem_2h: "2 \u00f3r\u00e1val el\u0151tte",
    rem_1d: "1 nappal el\u0151tte", rem_2d: "2 nappal el\u0151tte",
    ed_show_reminders: "Eml\u00e9keztet\u0151k", ed_add_column: "Oszlop hozz\u00e1ad\u00e1sa",
    ed_move_left: "Mozgat\u00e1s balra", ed_move_right: "Mozgat\u00e1s jobbra",
    ed_duplicate: "Oszlop duplik\u00e1l\u00e1sa", ed_delete_column: "Oszlop t\u00f6rl\u00e9se",
    ed_code_editor: "K\u00f3dszerkeszt\u0151", ed_visual_editor: "Vizu\u00e1lis szerkeszt\u0151",
    ed_icon: "Ikon (nem k\u00f6telez\u0151)", ed_card_title: "K\u00e1rtya c\u00edme (nem k\u00f6telez\u0151)",
    ed_card_title_placeholder: "C\u00edm az oszlopok felett",
    ed_sec_view: "Megjelen\u00edt\u00e9s", ed_sec_display: "Konfigur\u00e1ci\u00f3",
    due_time_lbl: "Id\u0151pont", due_date_lbl: "D\u00e1tum", rec_mode_lbl: "M\u00f3d",
    rec_time: "Id\u0151pont", rec_end: "V\u00e9ge", rec_end_never: "Soha", rec_end_date: "D\u00e1tumon", rec_end_count: "N alkalom ut\u00e1n",
    rec_end_date_lbl: "V\u00e9gdatum", rec_max_count_lbl: "max", rec_remaining: "m\u00e9g {0}", rec_start_date_lbl: "Kezd\u0151 d\u00e1tum",
    history: "El\u0151zm\u00e9nyek", history_created: "L\u00e9trehozva", history_completed: "Teljes\u00edtve", history_reopened: "\u00dajranyitva",
    history_reset: "Automatikus visszavonas", history_changed: "m\u00f3dos\u00edtva", history_empty: "Nincs el\u0151zm\u00e9ny", hist_title: "C\u00edm", history_disabled: "Letiltva",
    ed_show_history: "El\u0151zm\u00e9nyek mutat\u00e1sa", hist_by_user: "Felhaszn\u00e1l\u00f3",
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
    sub_items: "Unteraufgaben",
    add_sub_item: "+ Unteraufgabe hinzuf\u00fcgen",
    recurrence: "Wiederholung",
    recurrence_enabled: "Aktiviert",
    recurrence_every: "Alle",
    rec_hours: "Stunden", rec_days: "Tage", rec_weeks: "Wochen", rec_months: "Monate",
    rec_short_h: "Std.", rec_short_d: "T.", rec_short_w: "Wo.", rec_short_m: "Mon.",
    priority: "Priorit\u00e4t",
    pri_high: "Hoch", pri_medium: "Mittel", pri_low: "Niedrig",
    ed_show_priority: "Priorit\u00e4t",
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
    ed_show_title: "Titel",
    ed_show_progress: "Fortschritt",
    ed_show_due_date: "F\u00e4lligkeit",
    ed_show_notes: "Notizen",
    ed_show_recurrence: "Wiederholung",
    ed_show_sub_items: "Unteraufgaben",
    ed_show_person: "Person",
    ed_auto_delete: "Erledigte sofort l\u00f6schen",
    ed_compact: "Kompakt",
    ed_show_tags: "Tags",
    ed_hint: "Neue Listen k\u00f6nnen unter Einstellungen \u2192 Integrationen \u2192 Home Tasks erstellt werden.",
    tags: "Tags",
    add_tag: "+ Tag hinzuf\u00fcgen",
    tag_placeholder: "Neues Tag...",
    remove_tag: "Entfernen",
    new_sub_item: "Neue Unteraufgabe",
    remove_reminder: "Erinnerung entfernen",
    sort_label: "Sortierung",
    sort_manual: "Manuell",
    sort_due: "F\u00e4lligkeit",
    sort_priority: "Priorit\u00e4t",
    sort_title: "Titel (A\u2013Z)",
    sort_person: "Zugewiesen",
    ed_show_sort: "Sortierung",
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
    ed_show_reminders: "Erinnerungen",
    ed_add_column: "Spalte hinzuf\u00fcgen",
    ed_move_left: "Nach links",
    ed_move_right: "Nach rechts",
    ed_duplicate: "Spalte duplizieren",
    ed_delete_column: "Spalte l\u00f6schen",
    ed_code_editor: "Code-Editor",
    ed_visual_editor: "Visueller Editor",
    ed_icon: "Symbol (optional)",
    ed_card_title: "Kartentitel (optional)",
    ed_card_title_placeholder: "Titel \u00fcber den Spalten",
    ed_sec_view: "Darstellung",
    ed_sec_display: "Konfiguration",
    due_time_lbl: "Uhrzeit",
    due_date_lbl: "Datum",
    rec_mode_lbl: "Modus",
    rec_time: "Uhrzeit", rec_end: "Ende", rec_end_never: "Nie", rec_end_date: "An Datum", rec_end_count: "Nach X mal",
    rec_end_date_lbl: "Enddatum", rec_max_count_lbl: "max", rec_remaining: "noch {0}", rec_start_date_lbl: "Startdatum",
    history: "Verlauf", history_created: "Erstellt", history_completed: "Erledigt", history_reopened: "Wieder ge\u00f6ffnet",
    history_reset: "Automatisch zur\u00fcckgesetzt", history_changed: "ge\u00e4ndert", history_empty: "Noch kein Verlauf", hist_title: "Titel", history_disabled: "Deaktiviert",
    ed_show_history: "Verlauf anzeigen", hist_by_user: "Benutzer",
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
    // Per-column state: [{filter, sortBy, sortOpen, tagFilters, personFilters, tasks, newTaskTitle}]
    this._columns = [];
    this._expandedTasks = new Set();
    this._editingTaskId = null;
    this._editingSubTaskId = null;
    this._draggedTaskId = null;
    this._draggedColIdx = null;
    this._touchClone = null;
    this._touchStartTimer = null;
    this._touchOffsetY = 0;
    this._touchBound = {};
    this._draggedSubTaskId = null;
    this._subTouchClone = null;
    this._subTouchStartTimer = null;
    this._subTouchOffsetY = 0;
    this._lastTitleClick = null;
    this._initialized = false;
    this._pendingRender = false;
    this._styleEl = null;
  }

  _defaultColState() {
    return { filter: "all", sortBy: "manual", sortOpen: false, tagFilters: new Set(), personFilters: new Set(), tasks: [], newTaskTitle: "" };
  }

  _t(key, ...args) {
    let lang = (this._hass && this._hass.language) || "en";
    if (lang === "nb" || lang === "nn") lang = "no";
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
    // Clean up stale expanded/editing state when columns are removed
    if (this._editingTaskId) {
      const taskStillExists = this._columns.some(cs => cs.tasks?.some(t => t.id === this._editingTaskId));
      if (!taskStillExists) this._editingTaskId = null;
    }
    // _expandedTasks is a Set of task IDs — clean up IDs no longer in any column
    const allTaskIds = new Set(this._columns.flatMap(cs => (cs.tasks || []).map(t => t.id)));
    for (const id of this._expandedTasks) {
      if (!allTaskIds.has(id)) this._expandedTasks.delete(id);
    }

    // Reset per-column filter/sort when list or defaults change
    for (let i = 0; i < config.columns.length; i++) {
      const col = config.columns[i];
      const prevCol = prevConfig.columns?.[i];
      if (col.list_id !== prevCol?.list_id || col.default_filter !== prevCol?.default_filter) {
        this._columns[i].filter = col.default_filter || "all";
        this._columns[i].tagFilters = new Set();
        this._columns[i].personFilters = new Set();
      }
      if (col.show_tags === false && prevCol?.show_tags !== false) {
        this._columns[i].tagFilters = new Set();
      }
      if (col.show_assigned_person === false && prevCol?.show_assigned_person !== false) {
        this._columns[i].personFilters = new Set();
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
    const tasks = this._columns[colIdx]?.tasks;
    if (tasks) {
      const t = tasks.find(t => t.id === taskId);
      if (t) t.notes = notes;
    }
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

  async _addSubTask(taskId, colIdx) {
    const result = await this._callWs("home_tasks/add_sub_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      title: this._t("new_sub_item"),
    });
    if (result) {
      this._editingSubTaskId = result.id;
    }
    await this._loadAllTasks();
  }

  async _toggleSubTask(taskId, subItemId, completed, colIdx) {
    await this._callWs("home_tasks/update_sub_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_task_id: subItemId,
      completed: !completed,
    });
    await this._loadAllTasks();
  }

  async _updateSubTaskTitle(taskId, subItemId, title, colIdx) {
    if (!title.trim()) return;
    const result = await this._callWs("home_tasks/update_sub_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_task_id: subItemId,
      title: title.trim(),
    });
    if (result) {
      this._editingSubTaskId = null;
      await this._loadAllTasks();
    }
  }

  async _deleteSubTask(taskId, subItemId, colIdx) {
    await this._callWs("home_tasks/delete_sub_task", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_task_id: subItemId,
    });
    await this._loadAllTasks();
  }

  async _reorderSubTasks(taskId, subTaskIds, colIdx) {
    await this._callWs("home_tasks/reorder_sub_tasks", {
      list_id: this._colListId(colIdx),
      task_id: taskId,
      sub_task_ids: subTaskIds,
    });
    const tasks = this._columns[colIdx]?.tasks;
    if (tasks) {
      const task = tasks.find(t => t.id === taskId);
      if (task && task.sub_items) {
        const idToSub = Object.fromEntries(task.sub_items.map(s => [s.id, s]));
        task.sub_items = subTaskIds.map(id => idToSub[id]).filter(Boolean);
      }
    }
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
    if (!srcListId || !tgtListId) {
      this._showError("Cannot move task: list not configured");
      await this._loadAllTasks();
      return;
    }
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
    if (cs.tagFilters.size > 0) {
      tasks = tasks.filter((t) => t.tags && t.tags.some((tag) => cs.tagFilters.has(tag)));
    }
    if (cs.personFilters.size > 0) {
      tasks = tasks.filter((t) => cs.personFilters.has(t.assigned_person));
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
        const da = a.due_date ? a.due_date + "T" + (a.due_time || "00:00") : null;
        const db = b.due_date ? b.due_date + "T" + (b.due_time || "00:00") : null;
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

  _getSubTaskProgress(task) {
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
    // Don't tear down DOM while a drag is in progress
    if (this._draggedTaskId !== null || this._draggedSubTaskId !== null) { this._pendingRender = true; return; }
    this._pendingRender = false;

    // Remove any stale sort close handler before rebuilding DOM
    if (this._sortCloseHandler) {
      document.removeEventListener("click", this._sortCloseHandler);
      this._sortCloseHandler = null;
    }

    const root = this.shadowRoot;
    root.innerHTML = "";

    if (!this._styleEl) {
      this._styleEl = document.createElement("style");
      this._styleEl.textContent = this._getStyles();
    }
    root.appendChild(this._styleEl);

    const card = this._el("ha-card", {}, [
      this._buildCardContent(),
    ]);
    root.appendChild(card);

    // Close any open sort dropdowns on next outside click
    if (this._columns.some(c => c.sortOpen)) {
      this._sortCloseHandler = () => {
        this._sortCloseHandler = null;
        this._columns.forEach(c => { c.sortOpen = false; });
        this._render();
      };
      setTimeout(() => document.addEventListener("click", this._sortCloseHandler, { once: true }), 0);
    }
  }

  _buildCardContent() {
    const cols = this._config.columns;
    if (cols.length === 1) {
      return this._buildColumn(0);
    }
    const children = [];
    if (this._config.title) {
      const titleEl = document.createElement("h1");
      titleEl.className = "card-global-title";
      titleEl.textContent = this._config.title;
      children.push(titleEl);
    }
    children.push(this._el("div", { className: "multi-columns" }, cols.map((_, i) => this._buildColumn(i))));
    return this._el("div", {}, children);
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
      const titleEl = document.createElement("h1");
      titleEl.className = "title";
      if (col.icon) {
        const iconEl = document.createElement("ha-icon");
        iconEl.setAttribute("icon", col.icon);
        iconEl.style.cssText = "--mdc-icon-size:1em;width:1em;height:1em;flex-shrink:0;";
        titleEl.appendChild(iconEl);
      }
      titleEl.appendChild(document.createTextNode(this._getListName(colIdx)));
      headerChildren.push(titleEl);
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
    const effectiveSortBy = sortKeys.includes(cs.sortBy) ? cs.sortBy : "manual";

    const sortDropdown = this._el("div", { className: "sort-dropdown" + (cs.sortOpen ? "" : " hidden") });
    for (const key of sortKeys) {
      const opt = this._el("div", {
        className: "sort-option" + (effectiveSortBy === key ? " active" : ""),
        textContent: sortLabels[key],
      });
      opt.addEventListener("click", (e) => {
        e.stopPropagation();
        // Snapshot task positions before re-render for FLIP animation
        const before = new Map();
        this.shadowRoot.querySelectorAll(`.task-list[data-col-idx="${colIdx}"] .task`).forEach(el => {
          if (el.dataset.taskId) before.set(el.dataset.taskId, el.getBoundingClientRect().top);
        });
        cs.sortBy = key;
        cs.sortOpen = false;
        this._render();
        // FLIP: animate tasks from old positions to new
        if (before.size > 0) {
          this.shadowRoot.querySelectorAll(`.task-list[data-col-idx="${colIdx}"] .task`).forEach(el => {
            const id = el.dataset.taskId;
            if (!id || !before.has(id)) return;
            const dy = before.get(id) - el.getBoundingClientRect().top;
            if (Math.abs(dy) < 1) return;
            el.style.transition = "none";
            el.style.transform = `translateY(${dy}px)`;
            requestAnimationFrame(() => {
              el.style.transition = "transform 0.3s ease";
              el.style.transform = "";
              el.addEventListener("transitionend", () => {
                el.style.transition = "";
                el.style.transform = "";
              }, { once: true });
            });
          });
        }
      });
      sortDropdown.appendChild(opt);
    }
    const sortBtnWrapper = this._el("div", { className: "sort-btn-wrapper" });
    const sortBtn = this._el("button", {
      className: "sort-btn" + (effectiveSortBy !== "manual" ? " active" : ""),
      textContent: "\u2191 \u2193",
      title: sortLabels[effectiveSortBy],
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

    // Tag chips (built before filter row to decide sort button placement)
    const hideFilters = col.auto_delete_completed === true;
    let tagChips = null;
    if (col.show_tags !== false) {
      const allTags = new Set();
      for (const t of cs.tasks) {
        for (const tag of (t.tags || [])) allTags.add(tag);
      }
      if (allTags.size > 0) {
        const chipChildren = [];
        for (const tag of [...allTags].sort()) {
          const isActive = cs.tagFilters.has(tag);
          const chip = this._el("button", {
            className: "tag-chip" + (isActive ? " active" : "") + (this._animChipTag === tag ? " chip-anim" : ""),
            textContent: "#" + tag,
          });
          chip.addEventListener("click", () => {
            if (cs.tagFilters.has(tag)) cs.tagFilters.delete(tag);
            else cs.tagFilters.add(tag);
            this._animChipTag = tag;
            this._render();
            this._animChipTag = null;
          });
          chipChildren.push(chip);
        }
        tagChips = this._el("div", { className: "tag-chips" }, chipChildren);
      }
    }

    // Person chips
    let personChips = null;
    if (col.show_assigned_person !== false) {
      const assignedPersons = new Set();
      for (const t of cs.tasks) {
        if (t.assigned_person) assignedPersons.add(t.assigned_person);
      }
      if (assignedPersons.size > 0) {
        const chipChildren = [];
        for (const eid of [...assignedPersons].sort()) {
          const isActive = cs.personFilters.has(eid);
          let name = eid;
          if (this._hass && this._hass.states && this._hass.states[eid]) {
            name = this._hass.states[eid].attributes?.friendly_name || eid;
          }
          const chip = this._el("button", {
            className: "person-chip" + (isActive ? " active" : "") + (this._animChipPerson === eid ? " chip-anim" : ""),
            textContent: "\uD83D\uDC64 " + name,
          });
          chip.addEventListener("click", () => {
            if (cs.personFilters.has(eid)) cs.personFilters.delete(eid);
            else cs.personFilters.add(eid);
            this._animChipPerson = eid;
            this._render();
            this._animChipPerson = null;
          });
          chipChildren.push(chip);
        }
        personChips = this._el("div", { className: "person-chips" }, chipChildren);
      }
    }

    // Sort button placement: move into first available chips row when filters are hidden
    const sortInTagRow = hideFilters && tagChips !== null && col.show_sort !== false;
    const sortInPersonRow = hideFilters && tagChips === null && personChips !== null && col.show_sort !== false;

    // Filter row
    const filterRowChildren = [];
    if (!hideFilters) {
      filterRowChildren.push(
        this._buildFilterBtn(this._t("filter_all"), "all", colIdx),
        this._buildFilterBtn(this._t("filter_open"), "open", colIdx),
        this._buildFilterBtn(this._t("filter_done"), "done", colIdx),
      );
      filterRowChildren.push(this._el("div", { className: "filter-spacer" }));
      if (col.show_sort !== false) filterRowChildren.push(sortBtnWrapper);
    } else if (col.show_sort !== false && !sortInTagRow && !sortInPersonRow) {
      filterRowChildren.push(this._el("div", { className: "filter-spacer" }));
      filterRowChildren.push(sortBtnWrapper);
    }
    const filters = filterRowChildren.length > 0
      ? this._el("div", { className: "filters" }, filterRowChildren)
      : null;

    // Wrap chips + sort button together when sort moves into that row
    const tagChipsEl = (tagChips && sortInTagRow)
      ? this._el("div", { className: "tag-chips-row" }, [tagChips, sortBtnWrapper])
      : tagChips;
    const personChipsEl = (personChips && sortInPersonRow)
      ? this._el("div", { className: "person-chips-row" }, [personChips, sortBtnWrapper])
      : personChips;

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
        const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${CSS.escape(String(this._draggedTaskId))}"]`);
        if (draggedEl && draggedEl.parentNode !== taskList) {
          if (draggedEl.parentElement) draggedEl.parentElement.removeChild(draggedEl);
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
    if (filters) children.push(filters);
    if (tagChipsEl) children.push(tagChipsEl);
    if (personChipsEl) children.push(personChipsEl);
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
      // Stop mousedown from reaching the draggable taskEl — otherwise the browser's
      // drag-detection system intercepts mousedown and prevents cursor positioning.
      editInput.addEventListener("mousedown", (e) => { e.stopPropagation(); });
      editInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this._editingTaskId = null;  // clear BEFORE calling so blur skips
          this._updateTaskTitle(task.id, editInput.value, colIdx);
        } else if (e.key === "Escape") { this._editingTaskId = null; this._render(); }
      });
      editInput.addEventListener("blur", () => {
        if (this._editingTaskId === task.id) this._updateTaskTitle(task.id, editInput.value, colIdx);
      });
      contentChildren.push(editInput);
      setTimeout(() => { editInput.focus(); editInput.select(); }, 0);
    } else {
      const titleSpan = this._el("span", { className: "task-title", textContent: task.title });
      titleSpan.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        this._expandedTasks.add(task.id);
        this._editingTaskId = task.id;
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
    const subProgress = this._getSubTaskProgress(task);
    if (subProgress && (col.show_sub_tasks ?? col.show_sub_items) !== false) {
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
        let badgeText = "\u21BB " + recLabel;
        if (task.recurrence_end_type === "count" && task.recurrence_remaining_count != null) {
          badgeText += " \u00b7 " + this._t("rec_remaining", task.recurrence_remaining_count);
        }
        metaChildren.push(this._el("span", { className: "recurrence-badge", textContent: badgeText }));
      }
    }
    if (task.assigned_person && col.show_assigned_person !== false) {
      let personName = task.assigned_person;
      if (this._hass && this._hass.states && this._hass.states[task.assigned_person]) {
        const attrs = this._hass.states[task.assigned_person].attributes;
        personName = (attrs && attrs.friendly_name) || task.assigned_person;
      }
      const isActivePerson = cs.personFilters.has(task.assigned_person);
      const assignedBadge = this._el("span", {
        className: "assigned-badge" + (isActivePerson ? " active" : ""),
        textContent: "\uD83D\uDC64 " + personName,
        "data-eid": task.assigned_person,
      });
      assignedBadge.addEventListener("click", (e) => {
        e.stopPropagation();
        if (cs.personFilters.has(task.assigned_person)) cs.personFilters.delete(task.assigned_person);
        else cs.personFilters.add(task.assigned_person);
        this._render();
        this.shadowRoot.querySelectorAll(`.assigned-badge[data-eid="${CSS.escape(task.assigned_person)}"]`)
          .forEach(b => b.classList.add("chip-anim"));
      });
      metaChildren.push(assignedBadge);
    }
    if (task.tags && task.tags.length > 0 && col.show_tags !== false) {
      for (const tag of task.tags) {
        const isActive = cs.tagFilters.has(tag);
        const tagBadge = this._el("span", {
          className: "tag-badge" + (isActive ? " active" : ""),
          textContent: "#" + tag,
          "data-tag": tag,
        });
        tagBadge.addEventListener("click", (e) => {
          e.stopPropagation();
          if (cs.tagFilters.has(tag)) cs.tagFilters.delete(tag);
          else cs.tagFilters.add(tag);
          this._render();
          this.shadowRoot.querySelectorAll(`.tag-badge[data-tag="${CSS.escape(tag)}"]`)
            .forEach(b => b.classList.add("chip-anim"));
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

    const expandBtn = this._el("button", { className: "expand-btn" + (isExpanded ? " expanded" : "") });
    const expandIcon = document.createElement("ha-icon");
    expandIcon.setAttribute("icon", "mdi:chevron-down");
    expandBtn.appendChild(expandIcon);
    mainChildren.push(expandBtn);

    const mainRow = this._el("div", { className: "task-main" }, mainChildren);
    mainRow.addEventListener("click", (e) => {
      if (e.detail > 1) return;
      if (e.target.closest(".checkbox-container")) return;
      if (e.target.closest(".tag-badge")) return;
      if (e.target.closest(".assigned-badge")) return;
      if (e.target.closest(".edit-title-input")) return;
      if (this._expandedTasks.has(task.id)) {
        // Animate close, then re-render
        const detailsEl = taskEl.querySelector(".task-details");
        if (detailsEl) {
          const h = detailsEl.scrollHeight;
          detailsEl.animate(
            [{ height: h + "px", overflow: "hidden" }, { height: "0px", overflow: "hidden" }],
            { duration: 200, easing: "ease-in" }
          );
          setTimeout(() => { this._expandedTasks.delete(task.id); this._render(); }, 200);
        } else {
          this._expandedTasks.delete(task.id);
          this._render();
        }
      } else {
        // Re-render with expanded state, then animate open
        this._justExpandedTaskId = task.id;
        this._expandedTasks.add(task.id);
        this._render();
        this._justExpandedTaskId = null;
      }
    });
    taskEl.appendChild(mainRow);

    if (isExpanded) {
      const detailsEl = this._buildTaskDetails(task, colIdx);
      if (this._justExpandedTaskId === task.id) {
        // Use a padding-free wrapper for height animation — avoids padding-stutter with box-sizing: content-box
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "overflow:hidden;height:0;";
        taskEl.appendChild(wrapper);
        wrapper.appendChild(detailsEl);
        // scrollHeight of inner element is unaffected by wrapper's height:0 constraint
        const h = detailsEl.scrollHeight;
        // Double rAF: first ensures style is committed, second ensures layout is complete
        requestAnimationFrame(() => requestAnimationFrame(() => {
          wrapper.animate(
            [{ height: "0px" }, { height: h + "px" }],
            { duration: 250, easing: "ease-out" }
          ).onfinish = () => {
            taskEl.insertBefore(detailsEl, wrapper);
            wrapper.remove();
          };
        }));
      } else {
        taskEl.appendChild(detailsEl);
      }
    }

    this._attachDragToTask(taskEl, task.id, colIdx);

    return taskEl;
  }

  _buildTaskDetails(task, colIdx) {
    const col = this._config.columns[colIdx];
    const listId = this._colListId(colIdx);

    // Due section
    const dateInput = this._el("input", {
      type: "date",
      value: task.due_date || "",
    });
    const timeInput = this._el("input", {
      type: "time",
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

    const dateWrap = this._el("div", { className: "field-wrap" }, [
      dateInput,
      this._el("span", { textContent: this._t("due_date_lbl") }),
    ]);
    const timeWrap = this._el("div", { className: "field-wrap" }, [
      timeInput,
      this._el("span", { textContent: this._t("due_time_lbl") }),
    ]);
    const dateSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("due_date") }),
      this._el("div", { className: "due-input-row" }, [dateWrap, timeWrap]),
    ]);

    // Notes section
    const notesInput = this._el("textarea", {
      placeholder: this._t("notes_placeholder"),
      rows: 2,
      value: task.notes || "",
    });
    let debounceTimer;
    const saveNotes = () => {
      clearTimeout(debounceTimer);
      debounceTimer = null;
      this._updateTaskNotes(task.id, notesInput.value, colIdx);
    };
    notesInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(saveNotes, 500);
    });
    notesInput.addEventListener("blur", saveNotes);
    const notesWrap = this._el("div", { className: "field-wrap no-label" }, [notesInput]);
    const notesSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("notes") }),
      notesWrap,
    ]);

    // Sub-tasks section
    const subList = this._el("div", { className: "sub-task-list" });
    subList.dataset.taskId = task.id;
    for (const sub of (task.sub_items || [])) {
      subList.appendChild(this._buildSubTask(task.id, sub, colIdx));
    }
    subList.addEventListener("dragover", (e) => { e.preventDefault(); });
    subList.addEventListener("drop", (e) => { e.preventDefault(); this._finishSubDrag(task.id, colIdx); });
    const addSubBtn = this._el("button", {
      className: "add-sub-btn",
      textContent: this._t("add_sub_item"),
    });
    addSubBtn.addEventListener("click", () => this._addSubTask(task.id, colIdx));
    const subSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("sub_items") }),
      subList,
      addSubBtn,
    ]);

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
        })?.then(() => this._loadAllTasks());
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
    const recurrenceStartDate = task.recurrence_start_date || "";
    const recurrenceTime = task.recurrence_time || "00:00";
    const recurrenceEndType = task.recurrence_end_type || "none";
    const recurrenceEndDate = task.recurrence_end_date || "";
    const recurrenceMaxCount = task.recurrence_max_count ?? null;
    const recurrenceRemainingCount = task.recurrence_remaining_count ?? task.recurrence_max_count ?? null;

    const recSwitch = document.createElement("ha-switch");
    recSwitch.checked = recurrenceEnabled;
    const recurrenceToggleRow = this._el("div", { className: "recurrence-toggle-row" }, [
      this._el("label", { className: "detail-label", style: "margin: 0;" }, [
        document.createTextNode(this._t("recurrence"))
      ]),
      recSwitch,
    ]);

    const recurrenceModeSelect = this._el("select", {});
    for (const [val, key] of [["interval", "rec_type_interval"], ["weekdays", "rec_type_weekdays"]]) {
      const opt = this._el("option", { value: val, textContent: this._t(key) });
      if (val === recurrenceType) opt.selected = true;
      recurrenceModeSelect.appendChild(opt);
    }
    const recurrenceModeWrap = this._el("div", { className: "sel-wrap" }, [
      recurrenceModeSelect,
      this._el("span", { textContent: this._t("rec_mode_lbl") }),
    ]);

    const recurrenceValueInput = this._el("input", { type: "number", value: recurrenceValue });
    recurrenceValueInput.min = 1;
    recurrenceValueInput.max = 365;

    const recurrenceUnitSelect = this._el("select", {});
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

    const spinUp = this._el("button", { className: "spin-btn spin-up", textContent: "\u25b4", type: "button" });
    const spinDown = this._el("button", { className: "spin-btn spin-down", textContent: "\u25be", type: "button" });
    spinUp.addEventListener("click", () => {
      const v = Math.min(365, (parseInt(recurrenceValueInput.value) || 1) + 1);
      recurrenceValueInput.value = v;
      recurrenceValueInput.dispatchEvent(new Event("change"));
    });
    spinDown.addEventListener("click", () => {
      const v = Math.max(1, (parseInt(recurrenceValueInput.value) || 1) - 1);
      recurrenceValueInput.value = v;
      recurrenceValueInput.dispatchEvent(new Event("change"));
    });
    const recValueWrap = this._el("div", { className: "field-wrap inline" }, [
      recurrenceValueInput,
      this._el("span", { textContent: "#" }),
      this._el("div", { className: "spin-btns" }, [spinUp, spinDown]),
    ]);
    const recUnitWrap = this._el("div", { className: "sel-wrap inline" }, [
      recurrenceUnitSelect,
      this._el("span", { textContent: this._t("recurrence_every") }),
    ]);
    const recurrenceIntervalRow = this._el("div", { className: "recurrence-input-row" }, [recValueWrap, recUnitWrap]);

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

    // Start date + reactivation time (start date + time row, time hidden for hours mode)
    const recurrenceStartDateInput = this._el("input", { type: "date", value: recurrenceStartDate });
    const recurrenceStartDateWrap = this._el("div", { className: "field-wrap" }, [
      recurrenceStartDateInput,
      this._el("span", { textContent: this._t("rec_start_date_lbl") }),
    ]);
    const recurrenceTimeInput = this._el("input", { type: "time", value: recurrenceTime });
    const recurrenceTimeWrap = this._el("div", { className: "field-wrap" }, [
      recurrenceTimeInput,
      this._el("span", { textContent: this._t("rec_time") }),
    ]);
    const recurrenceDateTimeRow = this._el("div", { className: "due-input-row" }, [
      recurrenceStartDateWrap,
      recurrenceTimeWrap,
    ]);

    // End condition
    const recurrenceEndSelect = this._el("select", {});
    for (const [val, key] of [["none", "rec_end_never"], ["date", "rec_end_date"], ["count", "rec_end_count"]]) {
      const opt = this._el("option", { value: val, textContent: this._t(key) });
      if (val === recurrenceEndType) opt.selected = true;
      recurrenceEndSelect.appendChild(opt);
    }
    const recurrenceEndWrap = this._el("div", { className: "sel-wrap" }, [
      recurrenceEndSelect,
      this._el("span", { textContent: this._t("rec_end") }),
    ]);

    const recurrenceEndDateInput = this._el("input", { type: "date", value: recurrenceEndDate });
    const recurrenceEndDateWrap = this._el("div", { className: "due-input-row single" }, [
      this._el("div", { className: "field-wrap" }, [
        recurrenceEndDateInput,
        this._el("span", { textContent: this._t("rec_end_date_lbl") }),
      ]),
    ]);

    const recurrenceMaxCountInput = this._el("input", { type: "number", value: recurrenceMaxCount !== null ? recurrenceMaxCount : "" });
    recurrenceMaxCountInput.min = 1;
    recurrenceMaxCountInput.max = 999;
    const spinUp2 = this._el("button", { className: "spin-btn spin-up", textContent: "\u25b4", type: "button" });
    const spinDown2 = this._el("button", { className: "spin-btn spin-down", textContent: "\u25be", type: "button" });
    spinUp2.addEventListener("click", () => {
      const v = Math.min(999, (parseInt(recurrenceMaxCountInput.value) || 1) + 1);
      recurrenceMaxCountInput.value = v;
      recurrenceMaxCountInput.dispatchEvent(new Event("change"));
    });
    spinDown2.addEventListener("click", () => {
      const v = Math.max(1, (parseInt(recurrenceMaxCountInput.value) || 1) - 1);
      recurrenceMaxCountInput.value = v;
      recurrenceMaxCountInput.dispatchEvent(new Event("change"));
    });
    const recRemainingSpan = this._el("span", { className: "rec-remaining" });
    if (recurrenceRemainingCount !== null) {
      recRemainingSpan.textContent = this._t("rec_remaining", recurrenceRemainingCount);
    }
    const recMaxCountWrap = this._el("div", { className: "field-wrap inline" }, [
      recurrenceMaxCountInput,
      this._el("span", { textContent: this._t("rec_max_count_lbl") }),
      this._el("div", { className: "spin-btns" }, [spinUp2, spinDown2]),
    ]);
    const recurrenceCountRow = this._el("div", { className: "recurrence-input-row" }, [recMaxCountWrap, recRemainingSpan]);

    const applyRowVisibility = (mode, unit) => {
      recurrenceIntervalRow.style.display = mode === "interval" ? "" : "none";
      recurrenceWeekdayRow.style.display = mode === "weekdays" ? "" : "none";
      // Hide time column for hours mode; use .single CSS class (not inline style) for iOS reliability
      const hideTime = !(mode === "weekdays" || (mode === "interval" && unit !== "hours"));
      recurrenceTimeWrap.style.display = hideTime ? "none" : "";
      recurrenceDateTimeRow.classList.toggle("single", hideTime);
    };
    applyRowVisibility(recurrenceType, recurrenceUnit);

    const applyEndTypeVisibility = (endType) => {
      recurrenceEndDateWrap.style.display = endType === "date" ? "" : "none";
      recurrenceCountRow.style.display = endType === "count" ? "" : "none";
    };
    applyEndTypeVisibility(recurrenceEndType);

    const applyEnabledState = (enabled) => {
      recurrenceModeSelect.disabled = !enabled;
      recurrenceValueInput.disabled = !enabled;
      recurrenceUnitSelect.disabled = !enabled;
      spinUp.disabled = !enabled;
      spinDown.disabled = !enabled;
      weekdayCheckboxes.forEach(cb => { cb.disabled = !enabled; });
      recurrenceStartDateInput.disabled = !enabled;
      recurrenceTimeInput.disabled = !enabled;
      recurrenceEndSelect.disabled = !enabled;
      recurrenceEndDateInput.disabled = !enabled;
      recurrenceMaxCountInput.disabled = !enabled;
      spinUp2.disabled = !enabled;
      spinDown2.disabled = !enabled;
    };
    applyEnabledState(recurrenceEnabled);

    const saveWeekdays = () => {
      const selected = weekdayCheckboxes.map((cb, i) => cb.checked ? i : -1).filter(i => i >= 0);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_weekdays: selected,
      })?.then(() => this._loadAllTasks());
    };

    const saveInterval = () => {
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      recurrenceValueInput.value = val;
      applyRowVisibility(recurrenceModeSelect.value, recurrenceUnitSelect.value);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
      })?.then(() => this._loadAllTasks());
    };

    const saveStartDate = () => {
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_start_date: recurrenceStartDateInput.value || null,
      })?.then(() => this._loadAllTasks());
    };

    const saveRecurrenceTime = () => {
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_time: recurrenceTimeInput.value || null,
      })?.then(() => this._loadAllTasks());
    };

    const saveEndCondition = () => {
      const endType = recurrenceEndSelect.value;
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_end_type: endType,
        recurrence_end_date: endType === "date" ? (recurrenceEndDateInput.value || null) : null,
        recurrence_max_count: endType === "count" ? (parseInt(recurrenceMaxCountInput.value) || null) : null,
      })?.then(() => this._loadAllTasks());
    };

    recSwitch.addEventListener("change", () => {
      const enabled = recSwitch.checked;
      applyEnabledState(enabled);
      const mode = recurrenceModeSelect.value;
      const val = Math.max(1, Math.min(365, parseInt(recurrenceValueInput.value) || 1));
      const selected = weekdayCheckboxes.map((cb, i) => cb.checked ? i : -1).filter(i => i >= 0);
      const endType = recurrenceEndSelect.value;
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_enabled: enabled,
        recurrence_type: mode,
        recurrence_value: val,
        recurrence_unit: recurrenceUnitSelect.value,
        recurrence_weekdays: selected,
        recurrence_start_date: recurrenceStartDateInput.value || null,
        recurrence_time: recurrenceTimeInput.value || null,
        recurrence_end_type: endType,
        recurrence_end_date: endType === "date" ? (recurrenceEndDateInput.value || null) : null,
        recurrence_max_count: endType === "count" ? (parseInt(recurrenceMaxCountInput.value) || null) : null,
      })?.then(() => this._loadAllTasks());
    });

    recurrenceModeSelect.addEventListener("change", () => {
      const mode = recurrenceModeSelect.value;
      applyRowVisibility(mode, recurrenceUnitSelect.value);
      this._callWs("home_tasks/update_task", {
        list_id: listId,
        task_id: task.id,
        recurrence_type: mode,
      })?.then(() => this._loadAllTasks());
    });

    recurrenceValueInput.addEventListener("change", saveInterval);
    recurrenceUnitSelect.addEventListener("change", saveInterval);
    weekdayCheckboxes.forEach(cb => cb.addEventListener("change", saveWeekdays));
    recurrenceStartDateInput.addEventListener("change", saveStartDate);
    recurrenceTimeInput.addEventListener("change", saveRecurrenceTime);
    recurrenceEndSelect.addEventListener("change", () => { applyEndTypeVisibility(recurrenceEndSelect.value); saveEndCondition(); });
    recurrenceEndDateInput.addEventListener("change", saveEndCondition);
    recurrenceMaxCountInput.addEventListener("change", saveEndCondition);

    const recurrenceSection = this._el("div", { className: "detail-section" }, [
      recurrenceToggleRow,
      recurrenceModeWrap,
      recurrenceIntervalRow,
      recurrenceWeekdayRow,
      recurrenceDateTimeRow,
      recurrenceEndWrap,
      recurrenceEndDateWrap,
      recurrenceCountRow,
    ]);

    // Assigned person section
    const personSelect = this._el("select", {});
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
      })?.then(() => this._loadAllTasks());
    });
    const personWrap = this._el("div", { className: "sel-wrap no-label" }, [personSelect]);
    const personSection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("assigned_to") }),
      personWrap,
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
          })?.then(() => this._loadAllTasks());
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
          })?.then(() => this._loadAllTasks());
        }
        tagInput.value = "";
      }
    });
    const tagInputWrap = this._el("div", { className: "field-wrap" }, [
      tagInput,
      this._el("span", { textContent: this._t("add_tag").replace("+ ", "") }),
    ]);
    tagSectionChildren.push(tagInputWrap);
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
      })?.then(() => this._loadAllTasks());
    };
    for (let ri = 0; ri < taskReminders.length; ri++) {
      const offset = taskReminders[ri];
      const sel = this._el("select", {});
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
        title: this._t("remove_reminder"),
      });
      removeBtn.addEventListener("click", () => {
        const updated = taskReminders.filter((_, i) => i !== ri);
        _rebuildReminders(updated);
      });
      const remSelWrap = this._el("div", { className: "sel-wrap" }, [
        sel,
        this._el("span", { textContent: this._t("reminder") }),
      ]);
      reminderSectionChildren.push(this._el("div", { className: "reminder-row" }, [remSelWrap, removeBtn]));
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

    // History section
    const taskHistory = (task.history || []).slice().reverse();
    const histContent = this._el("div", { className: "history-list" });
    if (taskHistory.length === 0) {
      histContent.appendChild(this._el("p", { className: "history-empty", textContent: this._t("history_empty") }));
    } else {
      const fieldNames = {
        title: this._t("hist_title"),
        due_date: this._t("due_date"),
        due_time: this._t("due_time_lbl"),
        priority: this._t("priority"),
        assigned_person: this._t("assigned_to"),
        tags: this._t("tags"),
        notes: this._t("notes"),
        recurrence_enabled: this._t("recurrence"),
      };
      const fmtPriority = (v) => v != null ? [this._t("pri_low"), this._t("pri_medium"), this._t("pri_high")][v - 1] || String(v) : "\u2013";
      const fmtPerson = (v) => {
        if (!v) return "\u2013";
        return this._hass?.states?.[v]?.attributes?.friendly_name || v;
      };
      const fmtVal = (v, field) => {
        if (v == null) return "\u2013";
        if (field === "priority") return fmtPriority(v);
        if (field === "assigned_person") return fmtPerson(v);
        if (field === "tags") return Array.isArray(v) ? (v.join(", ") || "\u2013") : String(v);
        return String(v);
      };
      for (const entry of taskHistory) {
        const row = this._el("div", { className: "history-entry" });
        const ts = new Date(entry.ts);
        const tsStr = ts.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
        let icon = "\u2022", text = "";
        if (entry.action === "created") {
          icon = "\u2605"; text = this._t("history_created");
        } else if (entry.action === "completed") {
          icon = "\u2713"; text = this._t("history_completed");
        } else if (entry.action === "reopened") {
          icon = "\u21BA"; text = entry.by === "recurrence" ? this._t("history_reset") : this._t("history_reopened");
        } else if (entry.action === "updated") {
          const lbl = fieldNames[entry.field] || entry.field;
          if (entry.field === "recurrence_enabled") {
            text = `${lbl}: ${entry.to ? this._t("recurrence_enabled") : this._t("history_disabled")}`;
          } else if (entry.from !== undefined || entry.to !== undefined) {
            text = `${lbl}: ${fmtVal(entry.from, entry.field)} \u2192 ${fmtVal(entry.to, entry.field)}`;
          } else {
            text = `${lbl} ${this._t("history_changed")}`;
          }
          icon = "\u270e";
        }
        const byLabel = entry.by && entry.by !== "recurrence"
          ? ` \u00b7 ${entry.by === "user" ? this._t("hist_by_user") : entry.by}`
          : "";
        row.appendChild(this._el("span", { className: "history-icon", textContent: icon }));
        row.appendChild(this._el("span", { className: "history-text", textContent: text + byLabel }));
        row.appendChild(this._el("span", { className: "history-ts", textContent: tsStr }));
        histContent.appendChild(row);
      }
    }
    const historySection = this._el("div", { className: "detail-section" }, [
      this._el("label", { className: "detail-label", textContent: this._t("history") }),
      histContent,
    ]);

    const details = [];
    if (col.show_notes !== false) details.push(notesSection);
    if ((col.show_sub_tasks ?? col.show_sub_items) !== false) details.push(subSection);
    if (col.show_assigned_person !== false) details.push(personSection);
    if (col.show_priority !== false) details.push(prioritySection);
    if (col.show_tags !== false) details.push(tagSection);
    if (col.show_due_date !== false) details.push(dateSection);
    if (col.show_reminders !== false) details.push(reminderSection);
    if (col.show_recurrence !== false) details.push(recurrenceSection);
    if (col.show_history) details.push(historySection);
    details.push(actions);
    return this._el("div", { className: "task-details" }, details);
  }

  _buildSubTask(taskId, sub, colIdx) {
    const isEditing = this._editingSubTaskId === sub.id;

    const handle = this._el("span", {
      className: "sub-drag-handle",
      textContent: "\u2237",
      title: this._t("drag_handle"),
    });

    const checkbox = this._el("input", { type: "checkbox", checked: sub.completed });
    checkbox.addEventListener("change", () =>
      this._toggleSubTask(taskId, sub.id, sub.completed, colIdx)
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
        if (e.key === "Enter") {
          e.preventDefault();
          this._editingSubTaskId = null;  // clear BEFORE calling so blur skips
          this._updateSubTaskTitle(taskId, sub.id, titleEl.value, colIdx);
        } else if (e.key === "Escape") { this._editingSubTaskId = null; this._render(); }
      });
      titleEl.addEventListener("blur", () => {
        if (this._editingSubTaskId === sub.id) this._updateSubTaskTitle(taskId, sub.id, titleEl.value, colIdx);
      });
      setTimeout(() => { titleEl.focus(); titleEl.select(); }, 0);
    } else {
      let subCls = "sub-title";
      if (sub.completed) subCls += " completed";
      titleEl = this._el("span", { className: subCls, textContent: sub.title });
      titleEl.addEventListener("dblclick", () => {
        this._editingSubTaskId = sub.id;
        this._render();
      });
    }

    const deleteBtn = this._el("button", {
      className: "delete-sub-btn",
      title: this._t("delete_sub"),
      textContent: "\u00D7",
    });
    deleteBtn.addEventListener("click", () => this._deleteSubTask(taskId, sub.id, colIdx));

    const subEl = this._el("div", { className: "sub-task" }, [handle, label, titleEl, deleteBtn]);
    subEl.draggable = true;
    subEl.dataset.subTaskId = sub.id;

    subEl.addEventListener("dragstart", (e) => {
      this._draggedSubTaskId = sub.id;
      e.dataTransfer.effectAllowed = "move";
      subEl.classList.add("dragging");
    });
    subEl.addEventListener("dragend", () => this._finishSubDrag(taskId, colIdx));
    subEl.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (!this._draggedSubTaskId || this._draggedSubTaskId === sub.id) return;
      const draggedEl = this.shadowRoot.querySelector(`.sub-task[data-sub-task-id="${CSS.escape(this._draggedSubTaskId)}"]`);
      this._liveMoveSubTask(draggedEl, subEl, e.clientY);
    });
    subEl.addEventListener("drop", (e) => { e.preventDefault(); this._finishSubDrag(taskId, colIdx); });

    handle.addEventListener("touchstart", (e) => {
      if (e.touches.length !== 1) return;
      const touch = e.touches[0];
      this._subTouchStartTimer = setTimeout(() => {
        this._draggedSubTaskId = sub.id;
        subEl.classList.add("dragging");
        const rect = subEl.getBoundingClientRect();
        const clone = subEl.cloneNode(true);
        clone.style.cssText = `position:fixed;top:${rect.top}px;left:${rect.left}px;width:${rect.width}px;z-index:1000;opacity:0.85;pointer-events:none;box-shadow:0 4px 12px rgba(0,0,0,0.3);background:var(--todo-bg,#fff);border-radius:4px;border:1px solid var(--todo-primary,#03a9f4);`;
        this.shadowRoot.appendChild(clone);
        this._subTouchClone = clone;
        this._subTouchOffsetY = touch.clientY - rect.top;
      }, 150);
    }, { passive: true });

    const onSubTouchMove = (e) => {
      if (!this._draggedSubTaskId) {
        clearTimeout(this._subTouchStartTimer);
        this._subTouchStartTimer = null;
        return;
      }
      e.preventDefault();
      const touch = e.touches[0];
      if (this._subTouchClone) this._subTouchClone.style.top = `${touch.clientY - this._subTouchOffsetY}px`;
      if (this._subTouchClone) this._subTouchClone.style.display = "none";
      const shadowEl = this.shadowRoot.elementFromPoint(touch.clientX, touch.clientY);
      if (this._subTouchClone) this._subTouchClone.style.display = "";
      const target = shadowEl?.closest(".sub-task");
      if (target && target.dataset.subTaskId && target.dataset.subTaskId !== this._draggedSubTaskId) {
        const draggedEl = this.shadowRoot.querySelector(`.sub-task[data-sub-task-id="${CSS.escape(this._draggedSubTaskId)}"]`);
        this._liveMoveSubTask(draggedEl, target, touch.clientY);
      }
    };
    const onSubTouchEnd = () => {
      clearTimeout(this._subTouchStartTimer);
      this._subTouchStartTimer = null;
      if (this._draggedSubTaskId) this._finishSubDrag(taskId, colIdx);
    };
    handle.addEventListener("touchmove", onSubTouchMove, { passive: false });
    handle.addEventListener("touchend", onSubTouchEnd);
    handle.addEventListener("touchcancel", onSubTouchEnd);

    return subEl;
  }

  // --- Drag & Drop ---

  _getOrderFromDom(colIdx) {
    const taskList = this.shadowRoot.querySelector(`.task-list[data-col-idx="${CSS.escape(String(colIdx))}"]`);
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

  _liveMoveTask(draggedEl, targetEl, clientY) {
    if (!draggedEl || !targetEl || draggedEl === targetEl) return;
    const targetList = targetEl.parentNode;
    if (!targetList) return;

    const siblings = [...targetList.querySelectorAll(".task:not(.dragging)")];
    // Clear any in-progress transforms before FLIP snapshot to avoid stale offsets
    siblings.forEach(el => { el.style.transition = "none"; el.style.transform = ""; });

    // FLIP: snapshot Y positions of non-dragging siblings before move
    const before = new Map(siblings.map(el => [el, el.getBoundingClientRect().top]));

    const targetRect = targetEl.getBoundingClientRect();
    if (clientY < targetRect.top + targetRect.height / 2) {
      targetList.insertBefore(draggedEl, targetEl);
    } else {
      targetList.insertBefore(draggedEl, targetEl.nextSibling);
    }

    // FLIP: animate siblings from their previous position to the new one
    siblings.forEach(el => {
      const dy = (before.get(el) ?? el.getBoundingClientRect().top) - el.getBoundingClientRect().top;
      if (Math.abs(dy) < 1) return;
      el.style.transition = "none";
      el.style.transform = `translateY(${dy}px)`;
      requestAnimationFrame(() => {
        el.style.transition = "transform 0.18s ease";
        el.style.transform = "";
        el.addEventListener("transitionend", () => {
          el.style.transition = "";
          el.style.transform = "";
        }, { once: true });
      });
    });
  }

  _liveMoveSubTask(draggedEl, targetEl, clientY) {
    if (!draggedEl || !targetEl || draggedEl === targetEl) return;
    const list = targetEl.parentNode;
    if (!list) return;

    const siblings = [...list.querySelectorAll(".sub-task:not(.dragging)")];
    // Clear any in-progress transforms before FLIP snapshot
    siblings.forEach(el => { el.style.transition = "none"; el.style.transform = ""; });

    const before = new Map(siblings.map(el => [el, el.getBoundingClientRect().top]));

    const r2 = targetEl.getBoundingClientRect();
    if (clientY < r2.top + r2.height / 2) {
      list.insertBefore(draggedEl, targetEl);
    } else {
      list.insertBefore(draggedEl, targetEl.nextSibling);
    }

    siblings.forEach(el => {
      const dy = (before.get(el) ?? el.getBoundingClientRect().top) - el.getBoundingClientRect().top;
      if (Math.abs(dy) < 1) return;
      el.style.transition = "none";
      el.style.transform = `translateY(${dy}px)`;
      requestAnimationFrame(() => {
        el.style.transition = "transform 0.18s ease";
        el.style.transform = "";
        el.addEventListener("transitionend", () => {
          el.style.transition = "";
          el.style.transform = "";
        }, { once: true });
      });
    });
  }

  _finishSubDrag(taskId, colIdx) {
    const draggedId = this._draggedSubTaskId;
    this._draggedSubTaskId = null;
    this.shadowRoot.querySelectorAll(".sub-task").forEach(el => el.classList.remove("dragging"));
    if (this._subTouchClone) { this._subTouchClone.remove(); this._subTouchClone = null; }
    if (this._subTouchStartTimer) { clearTimeout(this._subTouchStartTimer); this._subTouchStartTimer = null; }
    if (!draggedId) return;
    const subList = this.shadowRoot.querySelector(`.sub-task-list[data-task-id="${CSS.escape(taskId)}"]`);
    if (!subList) return;
    const order = [...subList.querySelectorAll(".sub-task")].map(el => el.dataset.subTaskId).filter(Boolean);
    if (order.length > 1) this._reorderSubTasks(taskId, order, colIdx);
  }

  _finishDrag() {
    const draggedId = this._draggedTaskId;
    const srcColIdx = this._draggedColIdx;

    // Determine which column the dragged element ended up in
    const draggedEl = draggedId
      ? this.shadowRoot.querySelector(`[data-task-id="${CSS.escape(String(draggedId))}"]`)
      : null;
    const currentTaskList = draggedEl?.closest(".task-list");
    const tgtColIdx = currentTaskList !== null && currentTaskList !== undefined && currentTaskList.dataset.colIdx !== undefined
      ? parseInt(currentTaskList.dataset.colIdx, 10)
      : srcColIdx;

    // Clean up
    this._draggedTaskId = null;
    this._draggedColIdx = null;
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

    if (this._pendingRender) this._render();
  }

  _attachDragToTask(taskEl, taskId, colIdx) {
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
      const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${CSS.escape(String(this._draggedTaskId))}"]`);
      this._liveMoveTask(draggedEl, taskEl, e.clientY);
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

    // Touch Events (Mobile) — long-press anywhere on the task row to drag
    taskEl.addEventListener("touchstart", (e) => {
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
        const draggedEl = this.shadowRoot.querySelector(`.task[data-task-id="${CSS.escape(String(this._draggedTaskId))}"]`);
        this._liveMoveTask(draggedEl, target, touch.clientY);
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

    taskEl.addEventListener("touchmove", onTouchMove, { passive: false });
    taskEl.addEventListener("touchend", onTouchEnd);
    taskEl.addEventListener("touchcancel", onTouchEnd);
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
      .multi-columns { display: flex; gap: 0; align-items: stretch; }
      .multi-columns .card-column { flex: 1; min-width: 240px; border-right: 1px solid var(--todo-divider); }
      .multi-columns .card-column:last-child { border-right: none; }
      @media (max-width: 600px) { .multi-columns { flex-direction: column; } .multi-columns .card-column { border-right: none; border-bottom: 1px solid var(--todo-divider); } .multi-columns .card-column:last-child { border-bottom: none; } }
      .card-column.drag-target { outline: 2px dashed var(--todo-primary); outline-offset: -2px; border-radius: var(--todo-radius); }
      .card-column { padding: 16px; }
      .header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; }
      .card-global-title { font-size: 1.25rem; font-weight: 500; color: var(--ha-card-header-color, var(--todo-text)); margin: 0; padding: 16px 16px 0; line-height: 1.2; }
      .title { font-size: 1.25rem; font-weight: 500; color: var(--ha-card-header-color, var(--todo-text)); margin: 0; line-height: 1.2; display: flex; align-items: center; gap: 6px; }
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
      .task-main { display: flex; align-items: center; padding: 10px 12px; gap: 8px; min-height: 44px; cursor: pointer; }
      .task-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
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
        background: rgba(33, 150, 243, 0.15); color: var(--primary-color, #2196f3);
        cursor: pointer; transition: all 0.2s;
      }
      .assigned-badge:hover { opacity: 0.8; }
      .assigned-badge.active { background: var(--primary-color, #2196f3); color: #fff; }
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
      .tag-chips-row { display: flex; align-items: flex-start; gap: 4px; margin-bottom: 12px; }
      .tag-chips-row .tag-chips { flex: 1; margin-bottom: 0; }
      .tag-chip {
        padding: 4px 12px; border: 1px solid rgba(76, 175, 80, 0.3); border-radius: 16px;
        background: transparent; color: var(--success-color, #4caf50); font-size: 12px;
        cursor: pointer; font-family: inherit; transition: all 0.2s;
      }
      .tag-chip:hover { background: rgba(76, 175, 80, 0.1); }
      .tag-chip.active { background: var(--success-color, #4caf50); color: #fff; border-color: var(--success-color, #4caf50); }
      @keyframes chip-pop {
        0%   { transform: scale(0.78); }
        55%  { transform: scale(1.16); }
        100% { transform: scale(1); }
      }
      .chip-anim { animation: chip-pop 0.22s ease-out; }
      .person-chips { display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap; }
      .person-chips-row { display: flex; align-items: flex-start; gap: 4px; margin-bottom: 12px; }
      .person-chips-row .person-chips { flex: 1; margin-bottom: 0; }
      .person-chip {
        padding: 4px 12px; border: 1px solid var(--primary-color, #2196f3); border-radius: 16px;
        background: transparent; color: var(--primary-color, #2196f3); font-size: 12px;
        cursor: pointer; font-family: inherit; transition: all 0.2s;
      }
      .person-chip:hover { background: var(--todo-surface); }
      .person-chip.active { background: var(--primary-color, #2196f3); color: #fff; }
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
      .recurrence-toggle-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
      .recurrence-input-row { display: flex; align-items: flex-end; gap: 8px; }
      .rec-remaining { font-size: 12px; color: var(--secondary-text-color); align-self: center; flex-shrink: 0; }
      .recurrence-prefix { font-size: 13px; color: var(--todo-secondary-text); white-space: nowrap; }
      .recurrence-weekday-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-top: 6px; }
      .weekday-label {
        display: block; font-size: 12px; color: var(--todo-secondary-text); cursor: pointer; user-select: none;
      }
      .weekday-label input[type="checkbox"] { display: none; }
      .weekday-label span {
        display: block; text-align: center; padding: 4px 2px; border-radius: 4px; border: 1px solid var(--todo-divider);
        background: var(--todo-bg); transition: background 0.15s, color 0.15s;
      }
      .weekday-label input[type="checkbox"]:checked + span {
        background: var(--primary-color, #03a9f4); color: #fff; border-color: var(--primary-color, #03a9f4);
      }
      .weekday-label input[type="checkbox"]:disabled + span { opacity: 0.5; cursor: default; }
      .reminder-row { display: flex; gap: 6px; align-items: center; }
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
        cursor: pointer; padding: 4px; border-radius: 4px;
        display: inline-flex; align-items: center; justify-content: center;
        flex-shrink: 0;
      }
      .expand-btn:hover { background: var(--todo-surface); }
      .expand-btn ha-icon { --mdc-icon-size: 18px; transition: transform 0.2s; }
      .expand-btn.expanded ha-icon { transform: rotate(180deg); }
      .task-details {
        padding: 8px 12px 12px 12px; border-top: 1px solid var(--todo-divider);
        display: flex; flex-direction: column; gap: 12px; overflow-x: hidden;
      }
      .detail-section { display: flex; flex-direction: column; gap: 6px; }
      .detail-label {
        font-size: 11px; font-weight: 600; text-transform: uppercase;
        color: var(--todo-secondary-text); letter-spacing: 0.5px;
      }
      .due-input-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; overflow: hidden; }
      .due-input-row .field-wrap { min-width: 0; overflow: hidden; }
      .due-input-row .field-wrap input { padding: 18px 4px 4px 8px; font-size: 13px; }
      .due-input-row .field-wrap input:focus { padding: 17px 3px 3px 7px; }
      .due-input-row .field-wrap > span { left: 8px; font-size: 10px; }
      .field-wrap input[type="date"], .field-wrap input[type="time"] { text-align: left; padding-right: 6px; }
      .field-wrap { position: relative; width: 100%; }
      .due-input-row.single { grid-template-columns: 1fr; }
      .field-wrap input, .field-wrap textarea { width: 100%; box-sizing: border-box; padding: 20px 12px 6px; border: 1px solid var(--outline-color, var(--divider-color, rgba(255,255,255,0.12))); border-radius: 4px; background: var(--mdc-text-field-fill-color, var(--input-fill-color, transparent)); color: var(--primary-text-color); font-size: 0.875rem; font-family: inherit; outline: none; }
      .field-wrap input:focus, .field-wrap textarea:focus { border: 2px solid var(--primary-color); padding: 19px 11px 5px; }
      .field-wrap input:disabled, .field-wrap textarea:disabled { opacity: 0.4; }
      .field-wrap textarea { resize: vertical; min-height: 60px; }
      .field-wrap > span { position: absolute; top: 6px; left: 12px; font-size: 11px; font-weight: 400; color: var(--secondary-text-color); text-transform: none; letter-spacing: 0; pointer-events: none; }
      .field-wrap input:focus ~ span, .field-wrap textarea:focus ~ span { color: var(--primary-color); }
      .field-wrap.inline { flex: 1; width: auto; }
      .field-wrap.inline input { height: 40px; padding: 16px 8px 4px; box-sizing: border-box; }
      .field-wrap.inline input[type="number"] { padding-right: 28px; -moz-appearance: textfield; }
      .field-wrap.inline input[type="number"]::-webkit-inner-spin-button { -webkit-appearance: none; }
      .field-wrap.inline > span { top: 4px; left: 8px; }
      .spin-btns { position: absolute; right: 2px; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; }
      .spin-btn { background: none; border: none; padding: 2px 4px; cursor: pointer; color: var(--secondary-text-color); line-height: 1; font-size: 12px; }
      .spin-btn:hover { color: var(--primary-color); }
      .spin-btn:disabled { opacity: 0.4; cursor: default; }
      .sel-wrap { position: relative; width: 100%; }
      .sel-wrap select { width: 100%; height: 48px; padding: 18px 32px 4px 12px; border: 1px solid var(--outline-color, var(--divider-color, rgba(255,255,255,0.12))); border-radius: 4px; background: var(--mdc-text-field-fill-color, var(--input-fill-color, transparent)); color: var(--primary-text-color); font-size: 0.875rem; font-family: inherit; appearance: none; -webkit-appearance: none; cursor: pointer; outline: none; box-sizing: border-box; }
      .sel-wrap select:focus { border: 2px solid var(--primary-color); padding: 17px 31px 3px 11px; }
      .sel-wrap select:disabled { opacity: 0.4; cursor: default; }
      .sel-wrap > span { position: absolute; top: 6px; left: 12px; font-size: 11px; font-weight: 400; color: var(--secondary-text-color); text-transform: none; letter-spacing: 0; pointer-events: none; }
      .sel-wrap::after { content: "▾"; position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--secondary-text-color); font-size: 16px; line-height: 1; }
      .sel-wrap.inline { flex: 1; width: auto; }
      .sel-wrap.inline select { height: 40px; padding: 14px 28px 4px 10px; }
      .sel-wrap.inline > span { top: 4px; left: 10px; font-size: 10px; }
      .field-wrap.no-label input, .field-wrap.no-label textarea { padding: 10px 12px; }
      .field-wrap.no-label input:focus, .field-wrap.no-label textarea:focus { padding: 9px 11px; }
      .sel-wrap.no-label select { padding: 12px 32px 12px 12px; height: 44px; }
      .sel-wrap.no-label select:focus { padding: 11px 31px 11px 11px; }
      .sub-task-list { display: flex; flex-direction: column; }
      .sub-task { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
      .sub-task.dragging { opacity: 0.4; }
      .sub-drag-handle { cursor: grab; color: var(--todo-disabled); font-size: 14px; padding: 0 2px 0 0; user-select: none; flex-shrink: 0; }
      .sub-drag-handle:active { cursor: grabbing; }
      @media (pointer: coarse) { .sub-drag-handle { padding: 4px 4px 4px 0; font-size: 16px; } }
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
      .history-list { display: flex; flex-direction: column; gap: 0; max-height: 220px; overflow-y: auto; }
      .history-entry { display: grid; grid-template-columns: 18px 1fr auto; align-items: baseline; gap: 6px; padding: 5px 14px 5px 0; border-bottom: 1px solid var(--divider-color, rgba(128,128,128,0.15)); font-size: 12px; }
      .history-entry:last-child { border-bottom: none; }
      .history-icon { color: var(--secondary-text-color); text-align: center; font-size: 11px; }
      .history-text { color: var(--primary-text-color); }
      .history-ts { color: var(--secondary-text-color); white-space: nowrap; font-size: 11px; }
      .history-empty { margin: 0; font-size: 12px; color: var(--secondary-text-color); }
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
      .compact .title { font-size: 1rem; }
      .compact .progress { font-size: 12px; }
      .compact .add-task { margin-bottom: 10px; }
      .compact .add-input { padding: 6px 10px; font-size: 13px; }
      .compact .add-btn { padding: 6px 14px; font-size: 13px; }
      .compact .filters { margin-bottom: 8px; }
      .compact .filter-btn { padding: 4px 12px; font-size: 12px; }
      .compact .tag-chips { margin-bottom: 8px; gap: 3px; }
      .compact .tag-chips-row { margin-bottom: 8px; }
      .compact .tag-chips-row .tag-chips { margin-bottom: 0; }
      .compact .tag-chip { padding: 2px 8px; font-size: 11px; }
      .compact .person-chips { margin-bottom: 8px; gap: 3px; }
      .compact .person-chips-row { margin-bottom: 8px; }
      .compact .person-chips-row .person-chips { margin-bottom: 0; }
      .compact .person-chip { padding: 2px 8px; font-size: 11px; }
      .compact .task-list { gap: 3px; }
      .compact .task-main { padding: 6px 8px; gap: 6px; min-height: 32px; }
      .compact .task-title { font-size: 13px; }
      .compact .task-meta { gap: 4px; }
      .compact .sub-badge, .compact .due-date, .compact .priority-badge, .compact .recurrence-badge,
      .compact .assigned-badge, .compact .tag-badge, .compact .reminder-badge { font-size: 10px; padding: 1px 6px; }
      .compact .checkmark { height: 16px; width: 16px; }
      .compact .checkbox-container input:checked ~ .checkmark::after { width: 4px; height: 7px; }
      .compact .expand-btn { padding: 2px; }
      .compact .expand-btn ha-icon { --mdc-icon-size: 16px; }
      .compact .empty-state { padding: 16px; font-size: 13px; }
      .compact .task-details { padding: 8px 10px; }
    `;
  }

  // --- Card config ---

  disconnectedCallback() {
    if (this._sortCloseHandler) {
      document.removeEventListener("click", this._sortCloseHandler);
      this._sortCloseHandler = null;
    }
    if (this._touchStartTimer) { clearTimeout(this._touchStartTimer); this._touchStartTimer = null; }
    if (this._subTouchStartTimer) { clearTimeout(this._subTouchStartTimer); this._subTouchStartTimer = null; }
  }

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
    this._sectionOpen = {};     // { translationKey: bool } — persists across re-renders
  }

  _t(key, ...args) {
    let lang = (this._hass && this._hass.language) || "en";
    if (lang === "nb" || lang === "nn") lang = "no";
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
    this._config = { ...config };

    // Clamp active tab
    if (this._editorTab >= this._config.columns.length) {
      this._editorTab = this._config.columns.length - 1;
    }

    if (this._listsLoaded && !this._firing) {
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
  }

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; }
      .editor { display: flex; flex-direction: column; gap: 0; padding: 16px 0; }
      .editor-card-title-row { margin-bottom: 12px; }
      .editor-tabs-row {
        display: flex; align-items: center;
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
        margin-bottom: 0;
      }
      .editor-tabs { display: flex; gap: 0; align-items: center; flex: 1; }
      .editor-tab {
        min-width: 40px; height: 40px; padding: 0 14px;
        border: none; border-bottom: 3px solid transparent;
        background: transparent; cursor: pointer; font-size: 14px; font-weight: 500;
        font-family: inherit; color: var(--secondary-text-color);
        display: flex; align-items: center; justify-content: center;
        transition: color 0.15s, border-color 0.15s;
      }
      .editor-tab.active { color: var(--primary-color); border-bottom: 3px solid var(--primary-color); }
      .editor-tab:hover:not(.active) { color: var(--primary-text-color); background: var(--secondary-background-color); }
      .editor-tab-add {
        width: 36px; height: 36px; border-radius: 50%; border: none;
        background: transparent; cursor: pointer;
        display: inline-flex; align-items: center; justify-content: center;
        color: var(--secondary-text-color); flex-shrink: 0; padding: 0; margin-left: 4px;
        transition: background 0.15s, color 0.15s;
      }
      .editor-tab-add:hover { background: var(--secondary-background-color); color: var(--primary-color); }
      .editor-col-controls {
        display: flex; gap: 0; align-items: center;
        padding: 4px 0 8px; margin-bottom: 8px;
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
      }
      .icon-btn {
        width: 36px; height: 36px; border-radius: 50%; border: none;
        background: transparent; cursor: pointer;
        display: inline-flex; align-items: center; justify-content: center;
        color: var(--secondary-text-color); flex-shrink: 0; padding: 0;
        transition: background 0.15s, color 0.15s;
      }
      .icon-btn:hover:not(:disabled) { background: var(--secondary-background-color); }
      .icon-btn.active { color: var(--primary-color); }
      .icon-btn.del { color: var(--error-color, #db4437); }
      .icon-btn:disabled { opacity: 0.3; cursor: default; }
      .icon-btn-spacer { flex: 1; }
      .toggle-grid { display: grid; grid-template-columns: 1fr 1fr; column-gap: 16px; }
      .visual-editor { display: flex; flex-direction: column; gap: 8px; }
      .field { display: flex; flex-direction: column; gap: 6px; }
      details { border: 1px solid var(--divider-color, rgba(255,255,255,0.12)); border-radius: 8px; overflow: hidden; }
      summary { display: flex; align-items: center; gap: 8px; padding: 12px 16px; cursor: pointer; font-size: 14px; font-weight: 500; color: var(--primary-text-color); user-select: none; list-style: none; }
      summary::-webkit-details-marker { display: none; }
      .sum-chevron { margin-left: auto; display: inline-flex; transition: transform 0.2s; color: var(--secondary-text-color); }
      details[open] .sum-chevron { transform: rotate(180deg); }
      .section-content { display: flex; flex-direction: column; gap: 16px; padding: 16px 16px; border-top: 1px solid var(--divider-color, rgba(255,255,255,0.12)); }
      label { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: 0.5px; }
      ha-textfield { width: 100%; }
      ha-icon-picker { width: 100%; }
      ha-select { width: 100%; }
      .hint { font-size: 12px; color: var(--secondary-text-color); font-style: italic; margin-top: 2px; }
      .toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; min-height: 40px; }
      .toggle-label { font-size: 14px; color: var(--primary-text-color); }
      ha-yaml-editor { display: block; }
    `;
    root.appendChild(style);

    const cols = this._config.columns;
    const activeTab = Math.min(this._editorTab, cols.length - 1);

    // Global card title input (above tabs)
    const cardTitleInput = document.createElement("ha-textfield");
    cardTitleInput.label = this._t("ed_card_title");
    cardTitleInput.placeholder = this._t("ed_card_title_placeholder");
    cardTitleInput.value = this._config.title || "";
    cardTitleInput.style.width = "100%";
    cardTitleInput.addEventListener("change", (e) => {
      this._config = { ...this._config, title: e.target.value || undefined };
      this._fireChanged();
    });
    const cardTitleRow = this._el("div", { className: "editor-card-title-row" }, [cardTitleInput]);

    // Tab bar (tabs on left, + on right)
    const tabsEl = this._el("div", { className: "editor-tabs" });
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
      tabsEl.appendChild(tab);
    }
    const addTabBtn = document.createElement("button");
    addTabBtn.className = "editor-tab-add";
    addTabBtn.title = this._t("ed_add_column");
    const _plusIcon = document.createElement("ha-icon");
    _plusIcon.setAttribute("icon", "mdi:plus");
    _plusIcon.style.setProperty("--mdc-icon-size", "20px");
    addTabBtn.appendChild(_plusIcon);
    addTabBtn.addEventListener("click", () => {
      this._clearCodeState();
      const newCols = [...cols, {}];
      this._config = { ...this._config, columns: newCols };
      this._editorTab = newCols.length - 1;
      this._fireChanged();
      this._render();
    });
    const tabsRow = this._el("div", { className: "editor-tabs-row" }, [tabsEl, addTabBtn]);

    // Column controls using ha-icon-button
    const isCodeMode = this._editorCodeMode[activeTab] === true;
    const controls = this._el("div", { className: "editor-col-controls" });

    const makeIconBtn = (icon, label, cls, handler, disabled = false) => {
      const btn = document.createElement("button");
      btn.className = "icon-btn" + (cls ? " " + cls : "");
      btn.title = label;
      btn.disabled = disabled;
      const haIcon = document.createElement("ha-icon");
      haIcon.setAttribute("icon", icon);
      haIcon.style.setProperty("--mdc-icon-size", "20px");
      btn.appendChild(haIcon);
      btn.addEventListener("click", handler);
      return btn;
    };

    controls.appendChild(makeIconBtn(
      "mdi:code-braces",
      isCodeMode ? this._t("ed_visual_editor") : this._t("ed_code_editor"),
      isCodeMode ? "active" : "",
      () => {
        this._editorCodeMode[activeTab] = !isCodeMode;
        this._render();
      }
    ));
    const _btnSpacer = document.createElement("div");
    _btnSpacer.className = "icon-btn-spacer";
    controls.appendChild(_btnSpacer);

    // Left/right arrows always visible; disabled when not applicable
    controls.appendChild(makeIconBtn("mdi:arrow-left", this._t("ed_move_left"), "", () => {
      this._clearCodeState();
      const newCols = [...cols];
      [newCols[activeTab - 1], newCols[activeTab]] = [newCols[activeTab], newCols[activeTab - 1]];
      this._config = { ...this._config, columns: newCols };
      this._editorTab = activeTab - 1;
      this._fireChanged();
      this._render();
    }, cols.length < 2 || activeTab === 0));
    controls.appendChild(makeIconBtn("mdi:arrow-right", this._t("ed_move_right"), "", () => {
      this._clearCodeState();
      const newCols = [...cols];
      [newCols[activeTab], newCols[activeTab + 1]] = [newCols[activeTab + 1], newCols[activeTab]];
      this._config = { ...this._config, columns: newCols };
      this._editorTab = activeTab + 1;
      this._fireChanged();
      this._render();
    }, cols.length < 2 || activeTab === cols.length - 1));

    if (cols.length > 1) {
      controls.appendChild(makeIconBtn("mdi:content-copy", this._t("ed_duplicate"), "", () => {
        this._clearCodeState();
        const newCols = [...cols];
        newCols.splice(activeTab + 1, 0, { ...cols[activeTab] });
        this._config = { ...this._config, columns: newCols };
        this._editorTab = activeTab + 1;
        this._fireChanged();
        this._render();
      }));
      controls.appendChild(makeIconBtn("mdi:delete", this._t("ed_delete_column"), "del", () => {
        this._clearCodeState();
        const newCols = cols.filter((_, i) => i !== activeTab);
        this._config = { ...this._config, columns: newCols };
        this._editorTab = Math.min(activeTab, newCols.length - 1);
        this._fireChanged();
        this._render();
      }));
    }

    // Tab content
    const tabContent = isCodeMode
      ? this._buildCodeEditor(activeTab)
      : this._buildVisualEditor(activeTab);

    const editor = this._el("div", { className: "editor" }, [cardTitleRow, tabsRow, controls, tabContent]);
    root.appendChild(editor);
  }

  _buildCodeEditor(tabIdx) {
    const col = this._config.columns[tabIdx] || {};
    const editor = document.createElement("ha-yaml-editor");
    editor.defaultValue = col;
    editor.addEventListener("value-changed", (e) => {
      const val = e.detail.value;
      if (val !== undefined && typeof val === "object" && !Array.isArray(val)) {
        const { type: _t, ...stripped } = val;  // strip stray type key
        const newCols = [...this._config.columns];
        newCols[tabIdx] = stripped;
        this._config = { ...this._config, columns: newCols };
        this._fireChanged();
      }
    });
    return editor;
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
    const listSelect = document.createElement("ha-select");
    listSelect.label = this._t("ed_list");
    listSelect.style.width = "100%";
    if (!col.list_id) {
      const emptyItem = document.createElement("mwc-list-item");
      emptyItem.setAttribute("value", "");
      emptyItem.selected = true;
      emptyItem.textContent = "\u2014";
      listSelect.appendChild(emptyItem);
    }
    for (const l of this._lists) {
      const item = document.createElement("mwc-list-item");
      item.setAttribute("value", l.id);
      if (l.id === col.list_id) item.selected = true;
      item.textContent = l.name;
      listSelect.appendChild(item);
    }
    listSelect.addEventListener("selected", () => updateCol({ list_id: listSelect.value || undefined }));

    // Title input
    const titleInput = document.createElement("ha-textfield");
    titleInput.label = this._t("ed_title");
    titleInput.placeholder = this._t("ed_title_placeholder");
    titleInput.value = col.title || "";
    titleInput.style.width = "100%";
    titleInput.addEventListener("change", (e) => updateCol({ title: e.target.value || undefined }));

    // Icon picker
    const iconPicker = document.createElement("ha-icon-picker");
    iconPicker.label = this._t("ed_icon");
    iconPicker.value = col.icon || "";
    iconPicker.addEventListener("value-changed", (e) => updateCol({ icon: e.detail.value || undefined }));

    // Default filter select
    const filterSelect = document.createElement("ha-select");
    filterSelect.label = this._t("ed_default_filter");
    filterSelect.style.width = "100%";
    for (const [val, key] of [["all", "filter_all"], ["open", "filter_open"], ["done", "filter_done"]]) {
      const item = document.createElement("mwc-list-item");
      item.setAttribute("value", val);
      if ((col.default_filter || "all") === val) item.selected = true;
      item.textContent = this._t(key);
      filterSelect.appendChild(item);
    }
    filterSelect.addEventListener("selected", () => updateCol({ default_filter: filterSelect.value }));

    // Default sort select
    const sortSelect = document.createElement("ha-select");
    sortSelect.label = this._t("ed_default_sort");
    sortSelect.style.width = "100%";
    for (const [val, key] of [
      ["manual", "sort_manual"], ["due", "sort_due"], ["priority", "sort_priority"],
      ["title", "sort_title"], ["person", "sort_person"],
    ]) {
      const item = document.createElement("mwc-list-item");
      item.setAttribute("value", val);
      if ((col.default_sort || "manual") === val) item.selected = true;
      item.textContent = this._t(key);
      sortSelect.appendChild(item);
    }
    sortSelect.addEventListener("selected", () => updateCol({ default_sort: sortSelect.value }));

    // Toggle helper — uses ha-switch for native HA look
    const makeToggle = (_id, labelKey, configKey, defaultOn = true) => {
      const checked = defaultOn ? col[configKey] !== false : col[configKey] === true;
      const sw = document.createElement("ha-switch");
      sw.checked = checked;
      sw.setAttribute("aria-label", this._t(labelKey));
      sw.addEventListener("change", () => updateCol({ [configKey]: sw.checked }));
      return this._el("div", { className: "toggle-row" }, [
        this._el("span", { className: "toggle-label", textContent: this._t(labelKey) }),
        sw,
      ]);
    };

    const hint = this._el("span", { className: "hint", textContent: this._t("ed_hint") });

    const makeSection = (sectionId, icon, titleKey, nodes, defaultOpen = true) => {
      const det = document.createElement("details");
      const isOpen = sectionId in this._sectionOpen ? this._sectionOpen[sectionId] : defaultOpen;
      if (isOpen) det.open = true;
      const sum = document.createElement("summary");
      const ico = document.createElement("ha-icon");
      ico.setAttribute("icon", icon);
      ico.style.cssText = "--mdc-icon-size:20px;width:20px;height:20px;flex-shrink:0;";
      const chevWrap = document.createElement("span");
      chevWrap.className = "sum-chevron";
      const chev = document.createElement("ha-icon");
      chev.setAttribute("icon", "mdi:chevron-down");
      chev.style.cssText = "--mdc-icon-size:20px;width:20px;height:20px;";
      chevWrap.appendChild(chev);
      sum.appendChild(ico);
      sum.appendChild(document.createTextNode(this._t(titleKey)));
      sum.appendChild(chevWrap);
      det.appendChild(sum);
      const content = document.createElement("div");
      content.className = "section-content";
      for (const n of nodes) if (n) content.appendChild(n);
      det.appendChild(content);

      sum.addEventListener("click", (e) => {
        e.preventDefault();
        if (det.open) {
          // Animate close: fix current height, then transition to 0
          content.style.height = content.scrollHeight + "px";
          content.style.overflow = "hidden";
          requestAnimationFrame(() => {
            content.style.transition = "height 0.2s ease-in";
            content.style.height = "0";
            content.addEventListener("transitionend", () => {
              det.open = false;
              content.style.cssText = "";
              this._sectionOpen[sectionId] = false;
            }, { once: true });
          });
        } else {
          det.open = true;
          const h = content.scrollHeight;
          content.style.cssText = "height:0;overflow:hidden;";
          requestAnimationFrame(() => {
            content.style.transition = "height 0.25s ease-out";
            content.style.height = h + "px";
            content.addEventListener("transitionend", () => {
              content.style.cssText = "";
              this._sectionOpen[sectionId] = true;
            }, { once: true });
          });
        }
      });

      return det;
    };

    return this._el("div", { className: "visual-editor" }, [
      this._el("div", { className: "field" }, [listSelect, hint]),
      makeSection("view", "mdi:eye", "ed_sec_view", [
        this._el("div", { className: "field" }, [titleInput]),
        this._el("div", { className: "field" }, [iconPicker]),
        this._el("div", { className: "toggle-grid" }, [
          makeToggle("show-title", "ed_show_title", "show_title", true),
          makeToggle("show-progress", "ed_show_progress", "show_progress", true),
          makeToggle("auto-delete", "ed_auto_delete", "auto_delete_completed", false),
          makeToggle("show-sort", "ed_show_sort", "show_sort", true),
          makeToggle("compact", "ed_compact", "compact", false),
        ]),
        this._el("div", { className: "field" }, [filterSelect]),
        this._el("div", { className: "field" }, [sortSelect]),
      ]),
      makeSection("config", "mdi:tune", "ed_sec_display", [
        this._el("div", { className: "toggle-grid" }, [
          makeToggle("show-notes", "ed_show_notes", "show_notes", true),
          makeToggle("show-sub-tasks", "ed_show_sub_items", "show_sub_tasks", true),
          makeToggle("show-person", "ed_show_person", "show_assigned_person", true),
          makeToggle("show-priority", "ed_show_priority", "show_priority", true),
          makeToggle("show-tags", "ed_show_tags", "show_tags", true),
          makeToggle("show-due-date", "ed_show_due_date", "show_due_date", true),
          makeToggle("show-reminders", "ed_show_reminders", "show_reminders", true),
          makeToggle("show-recurrence", "ed_show_recurrence", "show_recurrence", true),
          makeToggle("show-history", "ed_show_history", "show_history", false),
        ]),
      ], false),
    ]);
  }

  _fireChanged() {
    // dispatchEvent is synchronous in browsers; HA calls setConfig() within this call,
    // so _firing is still true when setConfig runs. This guard would break if HA ever
    // processes config-changed asynchronously (e.g. via microtask).
    this._firing = true;
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    }));
    this._firing = false;
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
  description: "A feature-rich todo list with drag & drop, sub-tasks, notes, and due dates.",
  preview: true,
});
