/**
 * Unit tests for the pure helper methods on HomeTasksCard.
 *
 * These don't render anything — they just instantiate the element and
 * call individual methods directly with crafted input.
 *
 * We freeze the jsdom realm's `window.Date` to noon UTC of a known
 * date so the local-vs-UTC date arithmetic in _isDueDateToday /
 * _formatDueDate is deterministic regardless of the host timezone.
 */
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { loadCard, makeMockHass } from './setup.mjs';

// Pick noon UTC so all major timezones are still on the same calendar day.
const FROZEN_NOW = '2027-06-15T12:00:00Z';

async function makeCard() {
  // force=true so this realm gets a frozen Date — separate from the
  // cached realm used by other test files.
  const { HomeTasksCard } = await loadCard({ force: true, frozenNow: FROZEN_NOW });
  const card = new HomeTasksCard();
  card.setConfig({ columns: [{}] });
  card.hass = makeMockHass();
  return card;
}


// With FROZEN_NOW = 2027-06-15T12:00:00Z, "today" is 2027-06-15 in any
// timezone (since noon UTC is the same calendar day everywhere).

describe('_isDueDateOverdue', () => {
  test('returns false for empty input', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateOverdue(null), false);
    assert.equal(card._isDueDateOverdue(''), false);
    assert.equal(card._isDueDateOverdue(undefined), false);
  });

  test('returns false for today', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateOverdue('2027-06-15'), false);
  });

  test('returns false for future date', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateOverdue('2099-01-01'), false);
  });

  test('returns true for past date', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateOverdue('2000-01-01'), true);
  });

  test('returns true for yesterday', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateOverdue('2027-06-14'), true);
  });
});


describe('_isDueDateToday', () => {
  test('returns false for empty input', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateToday(null), false);
    assert.equal(card._isDueDateToday(''), false);
  });

  test('returns true only for today\'s ISO date', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateToday('2027-06-15'), true);
    assert.equal(card._isDueDateToday('2000-01-01'), false);
    assert.equal(card._isDueDateToday('2099-01-01'), false);
  });
});


// With FROZEN_NOW = 2027-06-15, "within 7 days" means 2027-06-15 .. 2027-06-22.
describe('_isDueDateWithinDays', () => {
  test('returns false for empty input', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateWithinDays(null, 7), false);
    assert.equal(card._isDueDateWithinDays('', 7), false);
  });

  test('returns true for today', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateWithinDays('2027-06-15', 0), true);
    assert.equal(card._isDueDateWithinDays('2027-06-15', 7), true);
  });

  test('returns true for date within range', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateWithinDays('2027-06-18', 7), true);  // 3 days ahead
    assert.equal(card._isDueDateWithinDays('2027-06-22', 7), true);  // exactly 7 days
  });

  test('returns false for date beyond range', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateWithinDays('2027-06-23', 7), false); // 8 days ahead
    assert.equal(card._isDueDateWithinDays('2099-01-01', 7), false);
  });

  test('returns false for past dates', async () => {
    const card = await makeCard();
    assert.equal(card._isDueDateWithinDays('2027-06-14', 7), false); // yesterday
    assert.equal(card._isDueDateWithinDays('2000-01-01', 7), false);
  });
});


describe('_getSubTaskProgress', () => {
  test('returns null when there are no sub_items', async () => {
    const card = await makeCard();
    assert.equal(card._getSubTaskProgress({}), null);
    assert.equal(card._getSubTaskProgress({ sub_items: [] }), null);
  });

  test('formats as "done/total"', async () => {
    const card = await makeCard();
    assert.equal(
      card._getSubTaskProgress({ sub_items: [
        { id: 'a', completed: true },
        { id: 'b', completed: false },
        { id: 'c', completed: true },
      ] }),
      '2/3'
    );
  });

  test('handles all-done', async () => {
    const card = await makeCard();
    assert.equal(
      card._getSubTaskProgress({ sub_items: [
        { id: 'a', completed: true },
        { id: 'b', completed: true },
      ] }),
      '2/2'
    );
  });

  test('handles none-done', async () => {
    const card = await makeCard();
    assert.equal(
      card._getSubTaskProgress({ sub_items: [
        { id: 'a', completed: false },
      ] }),
      '0/1'
    );
  });
});


describe('_buildSortComparator', () => {
  async function cardWithSort(sortBy) {
    const card = await makeCard();
    card._columns[0].sortBy = sortBy;
    return card;
  }

  test('manual sort uses sort_order', async () => {
    const card = await cardWithSort('manual');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { sort_order: 2 },
      { sort_order: 0 },
      { sort_order: 1 },
    ];
    tasks.sort(cmp);
    assert.deepEqual(tasks.map(t => t.sort_order), [0, 1, 2]);
  });

  test('priority sort puts highest first, missing last', async () => {
    const card = await cardWithSort('priority');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { priority: 1 },
      { priority: null },
      { priority: 3 },
      { priority: 2 },
    ];
    tasks.sort(cmp);
    assert.deepEqual(tasks.map(t => t.priority), [3, 2, 1, null]);
  });

  test('title sort is case-insensitive A→Z', async () => {
    const card = await cardWithSort('title');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { title: 'Banana' },
      { title: 'apple' },
      { title: 'Cherry' },
    ];
    tasks.sort(cmp);
    assert.deepEqual(tasks.map(t => t.title), ['apple', 'Banana', 'Cherry']);
  });

  test('due sort puts earliest first, undated last', async () => {
    const card = await cardWithSort('due');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { due_date: '2027-06-01' },
      { due_date: null },
      { due_date: '2027-01-15' },
      { due_date: '2027-03-10', due_time: '14:00' },
    ];
    tasks.sort(cmp);
    assert.deepEqual(tasks.map(t => t.due_date), [
      '2027-01-15', '2027-03-10', '2027-06-01', null,
    ]);
  });

  test('due sort with same date orders by time', async () => {
    const card = await cardWithSort('due');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { due_date: '2027-06-01', due_time: '14:00' },
      { due_date: '2027-06-01', due_time: '09:00' },
      { due_date: '2027-06-01' },  // no time → sorts as 00:00
    ];
    tasks.sort(cmp);
    assert.deepEqual(
      tasks.map(t => t.due_time ?? null),
      [null, '09:00', '14:00']
    );
  });

  test('person sort puts unassigned at the end', async () => {
    const card = await cardWithSort('person');
    const cmp = card._buildSortComparator(0);
    const tasks = [
      { assigned_person: 'person.charlie' },
      { assigned_person: null },
      { assigned_person: 'person.alice' },
    ];
    tasks.sort(cmp);
    assert.deepEqual(
      tasks.map(t => t.assigned_person),
      ['person.alice', 'person.charlie', null]
    );
  });
});


describe('_formatDueDate', () => {
  test('returns empty string for no date', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate(null), '');
    assert.equal(card._formatDueDate(''), '');
  });

  test('returns "Today" for today', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate('2027-06-15'), 'Today');
  });

  test('returns "Tomorrow" for tomorrow', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate('2027-06-16'), 'Tomorrow');
  });

  test('returns "Yesterday" for yesterday', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate('2027-06-14'), 'Yesterday');
  });

  test('returns "In 2 days" for +2 days (EN translation)', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate('2027-06-17'), 'In 2 days');
  });

  test('returns "2 days ago" for -2 days (EN translation)', async () => {
    const card = await makeCard();
    assert.equal(card._formatDueDate('2027-06-13'), '2 days ago');
  });

  test('returns formatted day+month for further dates same year', async () => {
    const card = await makeCard();
    const result = card._formatDueDate('2027-08-20');
    // Result is like "20. Aug" — must contain the day number
    assert.match(result, /^20\.\s/);
    // Same year → no year suffix
    assert.doesNotMatch(result, /\s\d{2}$/);
  });

  test('returns formatted day+month+year for different year', async () => {
    const card = await makeCard();
    const result = card._formatDueDate('2029-03-10');
    assert.match(result, /^10\.\s.+\s29$/);  // "10. Mar 29"
  });
});


// Timezone regression tests are in separate files (test_tz_*.mjs) because
// V8 caches TZ data per isolate, so changing process.env.TZ between tests
// in the same file doesn't take effect. Each test_tz_*.mjs sets its TZ
// once at module top level before any Date instance is created.
