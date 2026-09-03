'use strict';

/* Same quadrant keys/labels/colors as the desktop app (main.py QUADRANT_META),
 * so tasks.json exported here can be opened by the PySide6 app and vice versa. */
const QUADRANT_META = {
  urgent_important:     { title: 'Do First',  sub: 'Urgent & Important',        accent: '#F87171' },
  important_not_urgent: { title: 'Schedule',  sub: 'Important · Not Urgent',    accent: '#52525B' },
  urgent_not_important: { title: 'Delegate',  sub: 'Urgent · Not Important',    accent: '#FB923C' },
  neither:               { title: 'Eliminate', sub: 'Not Urgent · Not Important', accent: '#A78BFA' },
};
const QUADRANT_KEYS = Object.keys(QUADRANT_META);
const STORAGE_KEY = 'eisenhower_state';
const FONT_KEY = 'eisenhower_font_sizes';
const FILE_NAME_KEY = 'eisenhower_file_name';

/* ── State ─────────────────────────────────────────────────────────── */

function emptyState() {
  const s = { deleted_history: [] };
  QUADRANT_KEYS.forEach((k) => (s[k] = []));
  return s;
}

function normalizeTask(t) {
  if (typeof t === 'string') return { text: t, due: null, tag: null, note: null };
  return {
    text: t.text || '',
    due: t.due || null,
    tag: t.tag || null,
    note: t.note || null,
  };
}

function loadState() {
  let raw;
  try {
    raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
  } catch {
    raw = null;
  }
  const s = emptyState();
  if (raw && typeof raw === 'object') {
    QUADRANT_KEYS.forEach((k) => {
      if (Array.isArray(raw[k])) s[k] = raw[k].filter((t) => t != null).map(normalizeTask).filter((t) => t.text);
    });
    if (Array.isArray(raw.deleted_history)) {
      s.deleted_history = raw.deleted_history.map((t) => ({ ...normalizeTask(t), key: t.key || 'neither' }));
    }
  }
  return s;
}

let state = loadState();
let fontSizes = loadFontSizes();

function loadFontSizes() {
  try {
    const raw = JSON.parse(localStorage.getItem(FONT_KEY) || 'null');
    if (raw && typeof raw === 'object') return raw;
  } catch { /* ignore */ }
  const d = {};
  QUADRANT_KEYS.forEach((k) => (d[k] = 12));
  return d;
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function saveFontSizes() {
  localStorage.setItem(FONT_KEY, JSON.stringify(fontSizes));
}

/* ── Helpers ───────────────────────────────────────────────────────── */

function todayStr() {
  const d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function isOverdue(due) {
  return !!due && due <= todayStr();
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/* ── Rendering ─────────────────────────────────────────────────────── */

const quadrantsEl = document.getElementById('quadrants');
let quadrantListEls = {};

function buildQuadrantSkeleton() {
  quadrantsEl.innerHTML = '';
  quadrantListEls = {};
  QUADRANT_KEYS.forEach((key) => {
    const meta = QUADRANT_META[key];
    const card = document.createElement('section');
    card.className = 'quadrant';
    card.dataset.quadrant = key;

    const header = document.createElement('div');
    header.className = 'quadrant__header';
    header.style.background = meta.accent;

    const row = document.createElement('div');
    row.className = 'quadrant__row';
    row.innerHTML = `
      <span class="quadrant__title">${meta.title}</span>
      <span class="quadrant__count" data-role="count">0</span>
      <button type="button" class="quadrant__fontbtn" data-role="dec" aria-label="Reducir texto">−</button>
      <button type="button" class="quadrant__fontbtn" data-role="inc" aria-label="Aumentar texto">+</button>
    `;
    const sub = document.createElement('div');
    sub.className = 'quadrant__sub';
    sub.textContent = meta.sub;

    header.appendChild(row);
    header.appendChild(sub);

    const list = document.createElement('div');
    list.className = 'quadrant__list';
    list.dataset.quadrant = key;
    list.style.fontSize = fontSizes[key] + 'px';

    row.querySelector('[data-role="dec"]').addEventListener('click', () => adjustFont(key, -1));
    row.querySelector('[data-role="inc"]').addEventListener('click', () => adjustFont(key, 1));

    card.appendChild(header);
    card.appendChild(list);
    quadrantsEl.appendChild(card);
    quadrantListEls[key] = list;
  });
}

function adjustFont(key, delta) {
  const next = Math.min(20, Math.max(8, (fontSizes[key] || 12) + delta));
  fontSizes[key] = next;
  quadrantListEls[key].style.fontSize = next + 'px';
  saveFontSizes();
}

function taskLabel(task) {
  const parts = [];
  if (task.tag) parts.push(`<span class="task__chip">${escapeHtml(task.tag)}</span>`);
  if (task.due) {
    const overdueClass = isOverdue(task.due) ? ' task__chip--overdue' : '';
    parts.push(`<span class="task__chip${overdueClass}">${escapeHtml(task.due)}</span>`);
  }
  if (task.note) parts.push('<span class="task__note-flag">📝</span>');
  return parts.length ? `<div class="task__meta">${parts.join('')}</div>` : '';
}

function render() {
  QUADRANT_KEYS.forEach((key) => {
    const list = quadrantListEls[key];
    const tasks = state[key];
    list.innerHTML = '';
    const card = list.closest('.quadrant');
    card.querySelector('[data-role="count"]').textContent = String(tasks.length);

    if (!tasks.length) {
      const empty = document.createElement('div');
      empty.className = 'quadrant__empty';
      empty.textContent = 'Sin tareas';
      list.appendChild(empty);
      return;
    }

    tasks.forEach((task, index) => {
      const el = document.createElement('div');
      el.className = 'task';
      el.dataset.index = String(index);
      el.innerHTML = `<span class="task__text">${escapeHtml(task.text)}</span>${taskLabel(task)}`;
      list.appendChild(el);
    });
  });
  updateDeletedButton();
}

/* ── Add task ──────────────────────────────────────────────────────── */

const addForm = document.getElementById('addForm');
const taskInput = document.getElementById('taskInput');
const urgentCheck = document.getElementById('urgentCheck');
const importantCheck = document.getElementById('importantCheck');
const tagInput = document.getElementById('tagInput');
const dateCheck = document.getElementById('dateCheck');
const dueInput = document.getElementById('dueInput');

dateCheck.addEventListener('change', () => {
  dueInput.disabled = !dateCheck.checked;
  if (dateCheck.checked && !dueInput.value) dueInput.value = todayStr();
});

addForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = taskInput.value.trim();
  if (!text) return;

  const urgent = urgentCheck.checked;
  const important = importantCheck.checked;
  let key;
  if (urgent && important) key = 'urgent_important';
  else if (important) key = 'important_not_urgent';
  else if (urgent) key = 'urgent_not_important';
  else key = 'neither';

  const tag = tagInput.value.trim() || null;
  const due = dateCheck.checked ? dueInput.value || null : null;

  state[key].push({ text, due, tag, note: null });
  saveState();
  render();

  addForm.reset();
  dueInput.disabled = true;
  dueInput.value = '';
});

/* ── Action sheet (per-task menu) ─────────────────────────────────── */

const actionSheet = document.getElementById('actionSheet');
const actionSheetTitle = document.getElementById('actionSheetTitle');
const moveTargets = document.getElementById('moveTargets');
let sheetTarget = null; // { key, index }

function openActionSheet(key, index) {
  const task = state[key][index];
  if (!task) return;
  sheetTarget = { key, index };
  actionSheetTitle.textContent = task.text;

  actionSheet.querySelector('[data-action="due-clear"]').hidden = !task.due;
  actionSheet.querySelector('[data-action="tag-clear"]').hidden = !task.tag;
  actionSheet.querySelector('[data-action="note-clear"]').hidden = !task.note;

  moveTargets.innerHTML = '';
  QUADRANT_KEYS.filter((k) => k !== key).forEach((k) => {
    const btn = document.createElement('button');
    btn.className = 'sheet__item';
    btn.textContent = `${QUADRANT_META[k].title} — ${QUADRANT_META[k].sub}`;
    btn.addEventListener('click', () => moveTask(key, index, k));
    moveTargets.appendChild(btn);
  });

  actionSheet.showModal();
}

function closeActionSheet() {
  if (actionSheet.open) actionSheet.close();
  sheetTarget = null;
}

function moveTask(fromKey, index, toKey) {
  const [task] = state[fromKey].splice(index, 1);
  if (task) state[toKey].push(task);
  saveState();
  render();
  closeActionSheet();
}

actionSheet.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn || !sheetTarget) return;
  const { key, index } = sheetTarget;
  const task = state[key][index];
  if (!task) return closeActionSheet();

  switch (btn.dataset.action) {
    case 'due':
      openDueDialog(key, index, task.due);
      break;
    case 'due-clear':
      task.due = null;
      saveState();
      render();
      closeActionSheet();
      break;
    case 'tag':
      openTagDialog(key, index, task.tag);
      break;
    case 'tag-clear':
      task.tag = null;
      saveState();
      render();
      closeActionSheet();
      break;
    case 'note':
      openNoteDialog(key, index, task.note);
      break;
    case 'note-clear':
      task.note = null;
      saveState();
      render();
      closeActionSheet();
      break;
    case 'delete':
      deleteTask(key, index);
      closeActionSheet();
      break;
    case 'cancel':
      closeActionSheet();
      break;
  }
});
actionSheet.addEventListener('cancel', closeActionSheet); // hardware back / ESC

function deleteTask(key, index) {
  const [task] = state[key].splice(index, 1);
  if (task) {
    state.deleted_history.unshift({ ...task, key });
  }
  saveState();
  render();
}

/* ── Due date dialog ───────────────────────────────────────────────── */

const dueDialog = document.getElementById('dueDialog');
const dueDialogInput = document.getElementById('dueDialogInput');
let dueDialogTarget = null;

function openDueDialog(key, index, current) {
  dueDialogTarget = { key, index };
  dueDialogInput.value = current || todayStr();
  closeActionSheet();
  dueDialog.showModal();
}

document.getElementById('dueDialogOk').addEventListener('click', () => {
  if (dueDialogTarget) {
    const { key, index } = dueDialogTarget;
    const task = state[key][index];
    if (task) task.due = dueDialogInput.value || null;
    saveState();
    render();
  }
  dueDialog.close();
});

/* ── Tag dialog ────────────────────────────────────────────────────── */

const tagDialog = document.getElementById('tagDialog');
const tagDialogInput = document.getElementById('tagDialogInput');
let tagDialogTarget = null;

function openTagDialog(key, index, current) {
  tagDialogTarget = { key, index };
  tagDialogInput.value = current || '';
  closeActionSheet();
  tagDialog.showModal();
  setTimeout(() => tagDialogInput.focus(), 50);
}

document.getElementById('tagDialogOk').addEventListener('click', () => {
  if (tagDialogTarget) {
    const { key, index } = tagDialogTarget;
    const task = state[key][index];
    if (task) task.tag = tagDialogInput.value.trim() || null;
    saveState();
    render();
  }
  tagDialog.close();
});

/* ── Note dialog ───────────────────────────────────────────────────── */

const noteDialog = document.getElementById('noteDialog');
const noteDialogInput = document.getElementById('noteDialogInput');
let noteDialogTarget = null;

function openNoteDialog(key, index, current) {
  noteDialogTarget = { key, index };
  noteDialogInput.value = current || '';
  closeActionSheet();
  noteDialog.showModal();
  setTimeout(() => noteDialogInput.focus(), 50);
}

document.getElementById('noteDialogOk').addEventListener('click', () => {
  if (noteDialogTarget) {
    const { key, index } = noteDialogTarget;
    const task = state[key][index];
    if (task) task.note = noteDialogInput.value.trim() || null;
    saveState();
    render();
  }
  noteDialog.close();
});

/* Generic close for [data-close] buttons */
document.querySelectorAll('[data-close]').forEach((btn) => {
  btn.addEventListener('click', () => document.getElementById(btn.dataset.close).close());
});

/* ── Deleted history ───────────────────────────────────────────────── */

const deletedBtn = document.getElementById('deletedBtn');
const deletedDialog = document.getElementById('deletedDialog');
const deletedList = document.getElementById('deletedList');

function updateDeletedButton() {
  const n = state.deleted_history.length;
  deletedBtn.textContent = n ? `Borradas (${n})` : 'Borradas';
}

function renderDeletedList() {
  deletedList.innerHTML = '';
  if (!state.deleted_history.length) {
    deletedList.innerHTML = '<div class="deleted-empty">No hay tareas borradas</div>';
    return;
  }
  state.deleted_history.forEach((task, i) => {
    const row = document.createElement('div');
    row.className = 'deleted-item';
    const metaParts = [];
    if (task.tag) metaParts.push(task.tag);
    if (task.due) metaParts.push(task.due);
    row.innerHTML = `
      <div class="deleted-item__body">
        <div class="deleted-item__text">${escapeHtml(task.text)}${task.note ? ' 📝' : ''}</div>
        ${metaParts.length ? `<div class="deleted-item__meta">${escapeHtml(metaParts.join(' · '))}</div>` : ''}
      </div>
      <button type="button" class="btn" data-reuse="${i}">Reusar</button>
    `;
    deletedList.appendChild(row);
  });
}

deletedList.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-reuse]');
  if (!btn) return;
  const i = Number(btn.dataset.reuse);
  const task = state.deleted_history[i];
  if (!task) return;
  const targetKey = QUADRANT_KEYS.includes(task.key) ? task.key : 'neither';
  state[targetKey].push({ text: task.text, due: task.due, tag: task.tag, note: task.note });
  state.deleted_history.splice(i, 1);
  saveState();
  render();
  renderDeletedList();
});

deletedBtn.addEventListener('click', () => {
  renderDeletedList();
  deletedDialog.showModal();
});

/* ── Drag to reorder / move between quadrants ─────────────────────── */

const LONG_PRESS_MS = 350;
const MOVE_CANCEL_PX = 12;

let drag = null; // { key, index, pointerId, ghost, timer, startX, startY, moved }

function attachDragHandlers() {
  quadrantsEl.addEventListener('pointerdown', onPointerDown);
}

function onPointerDown(e) {
  if (e.button !== undefined && e.button !== 0) return;
  const taskEl = e.target.closest('.task');
  if (!taskEl) return;
  const list = taskEl.closest('.quadrant__list');
  const key = list.dataset.quadrant;
  const index = Number(taskEl.dataset.index);

  drag = {
    key, index, pointerId: e.pointerId,
    startX: e.clientX, startY: e.clientY,
    taskEl, dragging: false, moved: false,
    ghost: null, overList: null,
  };
  drag.timer = setTimeout(() => beginDrag(e.clientX, e.clientY), LONG_PRESS_MS);

  document.addEventListener('pointermove', onPointerMove);
  document.addEventListener('pointerup', onPointerUp);
  document.addEventListener('pointercancel', onPointerCancel);
}

function beginDrag(clientX, clientY) {
  if (!drag) return;
  drag.dragging = true;
  drag.taskEl.classList.add('task--dragging');
  const ghost = document.createElement('div');
  ghost.className = 'drag-ghost';
  ghost.textContent = drag.taskEl.querySelector('.task__text').textContent;
  document.body.appendChild(ghost);
  drag.ghost = ghost;
  positionGhost(clientX, clientY);
  if (navigator.vibrate) navigator.vibrate(12);
}

function positionGhost(x, y) {
  if (!drag || !drag.ghost) return;
  drag.ghost.style.left = x + 'px';
  drag.ghost.style.top = y + 'px';
}

function onPointerMove(e) {
  if (!drag || e.pointerId !== drag.pointerId) return;
  const dx = e.clientX - drag.startX;
  const dy = e.clientY - drag.startY;

  if (!drag.dragging) {
    if (Math.hypot(dx, dy) > MOVE_CANCEL_PX) {
      clearTimeout(drag.timer);
      drag = null;
      cleanupDragListeners();
    }
    return;
  }

  drag.moved = true;
  e.preventDefault();
  positionGhost(e.clientX, e.clientY);

  document.querySelectorAll('.quadrant__list--dragover').forEach((el) => el.classList.remove('quadrant__list--dragover'));
  const target = document.elementFromPoint(e.clientX, e.clientY);
  const list = target && target.closest('.quadrant__list');
  if (list) {
    list.classList.add('quadrant__list--dragover');
    drag.overList = list;
  } else {
    drag.overList = null;
  }
}

function onPointerUp(e) {
  if (!drag || e.pointerId !== drag.pointerId) return cleanupDragListeners();
  clearTimeout(drag.timer);

  if (drag.dragging) {
    finishDrop(e.clientX, e.clientY);
  } else if (!drag.moved) {
    openActionSheet(drag.key, drag.index);
  }

  teardownDrag();
  cleanupDragListeners();
}

function onPointerCancel() {
  if (drag) clearTimeout(drag.timer);
  teardownDrag();
  cleanupDragListeners();
}

function cleanupDragListeners() {
  document.removeEventListener('pointermove', onPointerMove);
  document.removeEventListener('pointerup', onPointerUp);
  document.removeEventListener('pointercancel', onPointerCancel);
}

function teardownDrag() {
  if (!drag) return;
  drag.taskEl.classList.remove('task--dragging');
  if (drag.ghost) drag.ghost.remove();
  document.querySelectorAll('.quadrant__list--dragover').forEach((el) => el.classList.remove('quadrant__list--dragover'));
  drag = null;
}

function finishDrop(clientX, clientY) {
  const targetList = drag.overList || document.elementFromPoint(clientX, clientY)?.closest('.quadrant__list');
  if (!targetList) return; // dropped outside any quadrant: leave task where it was

  const targetKey = targetList.dataset.quadrant;
  const fromKey = drag.key;
  const fromIndex = drag.index;

  const hoveredTaskEl = document.elementFromPoint(clientX, clientY)?.closest('.task');
  let targetIndex = state[targetKey].length;
  if (hoveredTaskEl && hoveredTaskEl.closest('.quadrant__list') === targetList) {
    const rect = hoveredTaskEl.getBoundingClientRect();
    const before = clientY < rect.top + rect.height / 2;
    targetIndex = Number(hoveredTaskEl.dataset.index) + (before ? 0 : 1);
  }

  const [task] = state[fromKey].splice(fromIndex, 1);
  if (!task) return;
  if (fromKey === targetKey && targetIndex > fromIndex) targetIndex -= 1;
  state[targetKey].splice(targetIndex, 0, task);

  saveState();
  render();
}

/* ── Due date auto-move (Schedule -> Do First once overdue) ───────── */

function checkDueDates() {
  const source = state.important_not_urgent;
  const stillHere = [];
  const moved = [];
  source.forEach((task) => {
    if (task.due && isOverdue(task.due)) moved.push(task);
    else stillHere.push(task);
  });
  if (moved.length) {
    state.important_not_urgent = stillHere;
    state.urgent_important.push(...moved);
    saveState();
    render();
  }
}

/* ── Open file / Export ───────────────────────────────────────────── */
/* Mirrors the desktop app's "Open file": pick a tasks.json, load it, and
 * remember its name (shown in the top bar, like the desktop file_label).
 * Android Chrome has no File System Access API, so we can't keep a live
 * writable handle to that file the way the desktop app does — "Abrir
 * archivo" loads it once into this device's storage, and "Exportar"
 * re-downloads under the same name so opening it again elsewhere stays
 * a one-file round trip. */

const fileLabel = document.getElementById('fileLabel');
let currentFileName = localStorage.getItem(FILE_NAME_KEY) || null;

function updateFileLabel() {
  fileLabel.textContent = currentFileName ? `Archivo: ${currentFileName}` : 'Datos de este dispositivo';
}

document.getElementById('exportBtn').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = currentFileName || 'tasks.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

const importFile = document.getElementById('importFile');
document.getElementById('importBtn').addEventListener('click', () => importFile.click());
importFile.addEventListener('change', async () => {
  const file = importFile.files[0];
  importFile.value = '';
  if (!file) return;
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    if (!confirm(`Esto reemplaza las tareas actuales de este dispositivo por las de "${file.name}". ¿Continuar?`)) return;
    const next = emptyState();
    QUADRANT_KEYS.forEach((k) => {
      if (Array.isArray(data[k])) next[k] = data[k].filter((t) => t != null).map(normalizeTask).filter((t) => t.text);
    });
    if (Array.isArray(data.deleted_history)) {
      next.deleted_history = data.deleted_history.map((t) => ({ ...normalizeTask(t), key: t.key || 'neither' }));
    }
    state = next;
    saveState();
    render();
    currentFileName = file.name;
    localStorage.setItem(FILE_NAME_KEY, currentFileName);
    updateFileLabel();
  } catch (err) {
    alert('No se pudo leer el archivo JSON: ' + err.message);
  }
});

/* ── Init ──────────────────────────────────────────────────────────── */

buildQuadrantSkeleton();
attachDragHandlers();
updateFileLabel();
render();
checkDueDates();
setInterval(checkDueDates, 60_000);

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('service-worker.js').catch(() => { /* offline support best-effort */ });
  });
}
