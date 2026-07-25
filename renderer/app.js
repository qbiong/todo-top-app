// ── State ─────────────────────────────────────────────────────
let todos = [];

// ── DOM Refs ──────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const elList = $('#todo-list');
const elInput = $('#todo-input');
const elAddBtn = $('#add-btn');
const elBadge = $('#count-badge');
const elDoneCount = $('#done-count');
const elClearDone = $('#clear-done-btn');

// ── Render ────────────────────────────────────────────────────
function render() {
  const pending = todos.filter((t) => !t.done);
  const done = todos.filter((t) => t.done);

  elBadge.textContent = pending.length;
  elDoneCount.textContent = done.length;
  elClearDone.style.display = done.length === 0 ? 'none' : '';

  if (todos.length === 0) {
    elList.innerHTML = `
      <li class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 11l3 3L22 4"/>
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>
        <p>没有待办事项<br>输入内容开始添加</p>
      </li>`;
    return;
  }

  elList.innerHTML = [...pending, ...done]
    .map(
      (t) => `
    <li class="todo-item${t.done ? ' done' : ''}" data-id="${t.id}">
      <label class="todo-check">
        <input type="checkbox" ${t.done ? 'checked' : ''}>
        <span class="checkmark"></span>
      </label>
      <span class="todo-text">${escapeHtml(t.text)}</span>
      <button class="todo-delete" title="删除">×</button>
    </li>`
    )
    .join('');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Save ──────────────────────────────────────────────────────
function save() {
  window.todoAPI.save(todos).catch(console.error);
}

// ── Actions ───────────────────────────────────────────────────
function addTodo(text) {
  text = text.trim();
  if (!text) return;

  todos.push({
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    text,
    done: false,
    createdAt: Date.now(),
  });

  render();
  save();
  elInput.value = '';
  elInput.focus();
}

function toggleTodo(id) {
  const todo = todos.find((t) => t.id === id);
  if (todo) {
    todo.done = !todo.done;
    render();
    save();
  }
}

function deleteTodo(id) {
  todos = todos.filter((t) => t.id !== id);
  render();
  save();
}

function clearDone() {
  const hadDone = todos.some((t) => t.done);
  if (!hadDone) return;
  todos = todos.filter((t) => !t.done);
  render();
  save();
}

// ── Event Delegation ─────────────────────────────────────────
elList.addEventListener('click', (e) => {
  const item = e.target.closest('.todo-item');
  if (!item) return;
  const id = item.dataset.id;

  // Delete button
  if (e.target.closest('.todo-delete')) {
    deleteTodo(id);
    return;
  }
});

elList.addEventListener('change', (e) => {
  const checkbox = e.target.closest('.todo-check input');
  if (!checkbox) return;
  const item = checkbox.closest('.todo-item');
  if (item) toggleTodo(item.dataset.id);
});

// ── Input Events ─────────────────────────────────────────────
elInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') addTodo(elInput.value);
});

elAddBtn.addEventListener('click', () => addTodo(elInput.value));

// ── Quick Actions ────────────────────────────────────────────
elClearDone.addEventListener('click', clearDone);

// ── Titlebar Controls ────────────────────────────────────────
$('#min-btn').addEventListener('click', () => {
  // 窗口最小化通过 preload 暴露
  window.todoAPI?.minimize?.();
});

$('#close-btn').addEventListener('click', () => {
  window.todoAPI?.close?.();
});

// ── Load on Start ────────────────────────────────────────────
async function init() {
  try {
    todos = await window.todoAPI.load();
  } catch (e) {
    console.error('Load failed:', e);
    todos = [];
  }
  render();
}

init();
