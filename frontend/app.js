// ============================================================
// Configuration
// When running locally: API is on the same origin (localhost:8000)
// FastAPI serves this JS file AND handles API requests.
// So we use a relative base URL — works both locally and in Docker.
// ============================================================

const API_BASE = '/api';   // Nginx proxies /api/* → FastAPI


// ============================================================
// State — all runtime data lives here
// ============================================================

const state = {
  token:      null,   // JWT string, stored in localStorage
  user:       null,   // { id, username, email }
  tasks:      [],     // full task list from server
  categories: [],     // full category list from server
  filter: {
    status:     'all', // 'all' | 'todo' | 'in_progress' | 'done'
    priority:   '',    // '' | 'low' | 'medium' | 'high'
    categoryId: '',    // '' | ObjectId string
  },
};


// ============================================================
// API helper
// Wraps fetch() to:
//   - prepend API_BASE to every URL
//   - attach Authorization header when token exists
//   - parse JSON response
//   - throw a descriptive error on non-2xx responses
// ============================================================

async function api(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };

  if (state.token) {
    headers['Authorization'] = 'Bearer ' + state.token;
  }

  const options = { method, headers };

  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(API_BASE + path, options);

  // 204 No Content — no body to parse
  if (response.status === 204) return null;

  const data = await response.json();

  if (!response.ok) {
    // FastAPI validation errors come as { detail: [...] }
    // Other errors come as { detail: "string" }
    const message = Array.isArray(data.detail)
      ? data.detail.map(e => e.msg).join(', ')
      : (data.detail || 'Unknown error');
    throw new Error(message);
  }

  return data;
}


// ============================================================
// Auth helpers — token is persisted in localStorage so the
// user stays logged in after page refresh
// ============================================================

function saveToken(token) {
  state.token = token;
  localStorage.setItem('taskflow_token', token);
}

function clearToken() {
  state.token = null;
  localStorage.removeItem('taskflow_token');
}

function loadTokenFromStorage() {
  const stored = localStorage.getItem('taskflow_token');
  if (stored) state.token = stored;
}


// ============================================================
// Toast notification
// Shows a small message at the bottom-right that fades out.
// ============================================================

let toastTimer = null;

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = 'toast toast--' + type;
  toast.classList.remove('hidden');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 3000);
}


// ============================================================
// Screen switching
// ============================================================

function showAuthScreen() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('app-screen').classList.add('hidden');
}

function showAppScreen() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('app-screen').classList.remove('hidden');
}


// ============================================================
// Auth: Login
// ============================================================

async function handleLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errorEl  = document.getElementById('login-error');

  errorEl.classList.add('hidden');

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields.';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    // OAuth2 login expects form-encoded data, not JSON
    const formData = new URLSearchParams();
    formData.append('username', email);   // FastAPI OAuth2 uses "username" field
    formData.append('password', password);

    const response = await fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    saveToken(data.access_token);
    await initApp();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
}


// ============================================================
// Auth: Register
// ============================================================

async function handleRegister() {
  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const errorEl  = document.getElementById('register-error');

  errorEl.classList.add('hidden');

  if (!username || !email || !password) {
    errorEl.textContent = 'Please fill in all fields.';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    await api('POST', '/auth/register', { username, email, password });
    showToast('Account created! Please sign in.');
    showPanel('login');
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
}


// ============================================================
// Auth: Logout
// ============================================================

function handleLogout() {
  clearToken();
  state.user       = null;
  state.tasks      = [];
  state.categories = [];
  showAuthScreen();
}


// ============================================================
// Show login or register panel
// ============================================================

function showPanel(name) {
  document.getElementById('login-panel').classList.toggle('hidden', name !== 'login');
  document.getElementById('register-panel').classList.toggle('hidden', name !== 'register');
}


// ============================================================
// App initialization — runs after login
// Fetches user profile, tasks, categories, then renders
// ============================================================

async function initApp() {
  try {
    const [user, tasks, categories] = await Promise.all([
      api('GET', '/auth/me'),
      api('GET', '/tasks/'),
      api('GET', '/categories/'),
    ]);

    state.user       = user;
    state.tasks      = tasks;
    state.categories = categories;

    renderUserInfo();
    renderCategoryNav();
    renderTaskCategoryOptions();
    renderTasks();
    showAppScreen();
  } catch (err) {
    // Token may be expired — force logout
    clearToken();
    showAuthScreen();
  }
}


// ============================================================
// Render: user info in sidebar
// ============================================================

function renderUserInfo() {
  const { username, email } = state.user;
  document.getElementById('user-name').textContent   = username;
  document.getElementById('user-email').textContent  = email;
  document.getElementById('user-avatar').textContent = username.charAt(0).toUpperCase();
}


// ============================================================
// Render: category list in sidebar
// ============================================================

function renderCategoryNav() {
  const nav = document.getElementById('category-nav');

  // Remove old category items (keep the label)
  nav.querySelectorAll('.nav-item').forEach(el => el.remove());

  state.categories.forEach(cat => {
    const a = document.createElement('a');
    a.href = '#';
    a.className = 'nav-item';
    if (state.filter.categoryId === cat.id) a.classList.add('active');
    a.dataset.categoryId = cat.id;
    a.innerHTML = `
      <span class="nav-icon" style="color:${cat.color}">&#9632;</span>
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${cat.name}</span>
    `;
    a.addEventListener('click', e => {
      e.preventDefault();
      setFilter({ categoryId: cat.id, status: 'all' });
    });
    nav.appendChild(a);
  });
}


// ============================================================
// Render: category options in task modal <select>
// ============================================================

function renderTaskCategoryOptions() {
  const select = document.getElementById('task-category');
  // Keep the first "None" option, remove the rest
  while (select.options.length > 1) select.remove(1);

  state.categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value       = cat.id;
    opt.textContent = cat.name;
    select.appendChild(opt);
  });
}


// ============================================================
// Render: task list
// Applies current filter before rendering
// ============================================================

function renderTasks() {
  const list     = document.getElementById('task-list');
  const empty    = document.getElementById('empty-state');
  const { status, priority, categoryId } = state.filter;

  // Apply filters
  let filtered = state.tasks.filter(task => {
    if (status !== 'all'  && task.status   !== status)     return false;
    if (priority          && task.priority !== priority)    return false;
    if (categoryId        && task.category_id !== categoryId) return false;
    return true;
  });

  // Update count badges in sidebar
  document.getElementById('count-all').textContent      = state.tasks.length;
  document.getElementById('count-todo').textContent     = state.tasks.filter(t => t.status === 'todo').length;
  document.getElementById('count-progress').textContent = state.tasks.filter(t => t.status === 'in_progress').length;
  document.getElementById('count-done').textContent     = state.tasks.filter(t => t.status === 'done').length;

  // Update count label in toolbar
  document.getElementById('task-count-label').textContent =
    filtered.length === 1 ? '1 task' : filtered.length + ' tasks';

  // Clear current list
  list.innerHTML = '';

  if (filtered.length === 0) {
    list.classList.add('hidden');
    empty.classList.remove('hidden');
    return;
  }

  list.classList.remove('hidden');
  empty.classList.add('hidden');

  filtered.forEach(task => {
    list.appendChild(buildTaskCard(task));
  });
}


// ============================================================
// Build a single task card DOM element
// ============================================================

function buildTaskCard(task) {
  const card = document.createElement('div');
  card.className = 'task-card' + (task.status === 'done' ? ' is-done' : '');
  card.dataset.id = task.id;

  // Due date display
  let dueHtml = '';
  if (task.due_date) {
    const due     = new Date(task.due_date);
    const today   = new Date();
    const overdue = due < today && task.status !== 'done';
    const label   = due.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    dueHtml = `<span class="task-due${overdue ? ' overdue' : ''}">${overdue ? '! ' : ''}${label}</span>`;
  }

  // Category badge
  let catHtml = '';
  if (task.category_id) {
    const cat = state.categories.find(c => c.id === task.category_id);
    if (cat) {
      catHtml = `<span class="badge badge--cat" style="--cat-color:${cat.color}22;color:${cat.color}">${cat.name}</span>`;
    }
  }

  // Status label map
  const statusLabel = { todo: 'To do', in_progress: 'In progress', done: 'Done' };

  card.innerHTML = `
    <div class="task-stripe task-stripe--${task.priority}"></div>
    <div class="task-body">
      <div class="task-title">${escapeHtml(task.title)}</div>
      <div class="task-meta">
        <span class="badge badge--${task.status}">${statusLabel[task.status]}</span>
        <span class="badge badge--${task.priority}">${task.priority}</span>
        ${catHtml}
        ${dueHtml}
      </div>
    </div>
    <div class="task-actions">
      <button class="btn-icon btn-edit" title="Edit">&#9998;</button>
      <button class="btn-icon btn-danger btn-delete" title="Delete">&#10005;</button>
    </div>
  `;

  card.querySelector('.btn-edit').addEventListener('click', () => openTaskModal(task));
  card.querySelector('.btn-delete').addEventListener('click', () => handleDeleteTask(task.id));

  return card;
}


// ============================================================
// Filter helpers
// ============================================================

function setFilter(updates) {
  Object.assign(state.filter, updates);

  // Update active nav items
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('active');
    if (el.dataset.filter === state.filter.status && !state.filter.categoryId) {
      el.classList.add('active');
    }
    if (el.dataset.categoryId && el.dataset.categoryId === state.filter.categoryId) {
      el.classList.add('active');
    }
  });

  // Update page title
  const titles = { all: 'All tasks', todo: 'To do', in_progress: 'In progress', done: 'Done' };
  if (state.filter.categoryId) {
    const cat = state.categories.find(c => c.id === state.filter.categoryId);
    document.getElementById('page-title').textContent = cat ? cat.name : 'Category';
  } else {
    document.getElementById('page-title').textContent = titles[state.filter.status] || 'Tasks';
  }

  renderTasks();
}


// ============================================================
// Task Modal — open for CREATE or EDIT
// ============================================================

function openTaskModal(task = null) {
  const modal    = document.getElementById('task-modal');
  const titleEl  = document.getElementById('modal-title');
  const errorEl  = document.getElementById('task-modal-error');

  errorEl.classList.add('hidden');

  if (task) {
    // Edit mode: populate form with existing values
    titleEl.textContent = 'Edit task';
    document.getElementById('task-id').value          = task.id;
    document.getElementById('task-title').value       = task.title;
    document.getElementById('task-desc').value        = task.description || '';
    document.getElementById('task-status').value      = task.status;
    document.getElementById('task-priority').value    = task.priority;
    document.getElementById('task-category').value    = task.category_id || '';
    document.getElementById('task-due').value         = task.due_date
      ? task.due_date.substring(0, 10) : '';
  } else {
    // Create mode: reset form
    titleEl.textContent = 'New task';
    document.getElementById('task-id').value       = '';
    document.getElementById('task-title').value    = '';
    document.getElementById('task-desc').value     = '';
    document.getElementById('task-status').value   = 'todo';
    document.getElementById('task-priority').value = 'medium';
    document.getElementById('task-category').value = '';
    document.getElementById('task-due').value      = '';
  }

  modal.classList.remove('hidden');
  document.getElementById('task-title').focus();
}

function closeTaskModal() {
  document.getElementById('task-modal').classList.add('hidden');
}


// ============================================================
// Task CRUD
// ============================================================

async function handleSaveTask() {
  const id       = document.getElementById('task-id').value;
  const title    = document.getElementById('task-title').value.trim();
  const errorEl  = document.getElementById('task-modal-error');

  errorEl.classList.add('hidden');

  if (!title) {
    errorEl.textContent = 'Title is required.';
    errorEl.classList.remove('hidden');
    return;
  }

  const payload = {
    title,
    description:  document.getElementById('task-desc').value.trim() || null,
    status:       document.getElementById('task-status').value,
    priority:     document.getElementById('task-priority').value,
    category_id:  document.getElementById('task-category').value || null,
    due_date:     document.getElementById('task-due').value || null,
  };

  try {
    if (id) {
      // PATCH — update existing task
      const updated = await api('PATCH', '/tasks/' + id, payload);
      // Replace in local state
      const index = state.tasks.findIndex(t => t.id === id);
      if (index !== -1) state.tasks[index] = updated;
      showToast('Task updated');
    } else {
      // POST — create new task
      const created = await api('POST', '/tasks/', payload);
      state.tasks.unshift(created);   // add to beginning of list
      showToast('Task created');
    }

    closeTaskModal();
    renderTasks();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
}

async function handleDeleteTask(taskId) {
  if (!confirm('Delete this task?')) return;

  try {
    await api('DELETE', '/tasks/' + taskId);
    state.tasks = state.tasks.filter(t => t.id !== taskId);
    renderTasks();
    showToast('Task deleted');
  } catch (err) {
    showToast(err.message, 'error');
  }
}


// ============================================================
// Category Modal
// ============================================================

const COLOR_SWATCHES = [
  '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
  '#f59e0b', '#22c55e', '#06b6d4', '#64748b',
];

function openCategoryModal() {
  document.getElementById('cat-name').value  = '';
  document.getElementById('cat-color').value = '#6366f1';
  document.getElementById('cat-modal-error').classList.add('hidden');

  // Render color swatches
  const swatchContainer = document.getElementById('color-swatches');
  swatchContainer.innerHTML = '';
  COLOR_SWATCHES.forEach(color => {
    const swatch = document.createElement('span');
    swatch.className = 'color-swatch' + (color === '#6366f1' ? ' active' : '');
    swatch.style.background = color;
    swatch.addEventListener('click', () => {
      document.getElementById('cat-color').value = color;
      swatchContainer.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
      swatch.classList.add('active');
    });
    swatchContainer.appendChild(swatch);
  });

  document.getElementById('category-modal').classList.remove('hidden');
  document.getElementById('cat-name').focus();
}

function closeCategoryModal() {
  document.getElementById('category-modal').classList.add('hidden');
}

async function handleSaveCategory() {
  const name    = document.getElementById('cat-name').value.trim();
  const color   = document.getElementById('cat-color').value;
  const errorEl = document.getElementById('cat-modal-error');

  errorEl.classList.add('hidden');

  if (!name) {
    errorEl.textContent = 'Name is required.';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const created = await api('POST', '/categories/', { name, color });
    state.categories.push(created);
    renderCategoryNav();
    renderTaskCategoryOptions();
    closeCategoryModal();
    showToast('Category created');
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
}


// ============================================================
// Utility: escape HTML to prevent XSS
// When we render user-supplied text into innerHTML, we must
// escape it so a task title like "<script>alert(1)</script>"
// is displayed as text, not executed as HTML.
// ============================================================

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}


// ============================================================
// Event listeners — wired up after DOM is ready
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {

  // --- Auth screen ---
  document.getElementById('btn-login').addEventListener('click', handleLogin);
  document.getElementById('btn-register').addEventListener('click', handleRegister);
  document.getElementById('go-register').addEventListener('click', e => { e.preventDefault(); showPanel('register'); });
  document.getElementById('go-login').addEventListener('click',    e => { e.preventDefault(); showPanel('login'); });

  // Allow Enter key to submit login/register forms
  document.getElementById('login-password').addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); });
  document.getElementById('reg-password').addEventListener('keydown',   e => { if (e.key === 'Enter') handleRegister(); });

  // --- App screen ---
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Filter nav (status links)
  document.querySelectorAll('.nav-item[data-filter]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      setFilter({ status: el.dataset.filter, categoryId: '' });
    });
  });

  // Priority filter dropdown
  document.getElementById('priority-filter').addEventListener('change', e => {
    setFilter({ priority: e.target.value });
  });

  // New task buttons
  document.getElementById('btn-new-task').addEventListener('click',   () => openTaskModal());
  document.getElementById('btn-empty-new').addEventListener('click',  () => openTaskModal());

  // Task modal
  document.getElementById('modal-close').addEventListener('click',    closeTaskModal);
  document.getElementById('btn-cancel-task').addEventListener('click', closeTaskModal);
  document.getElementById('btn-save-task').addEventListener('click',   handleSaveTask);

  // Category modal
  document.getElementById('btn-add-category').addEventListener('click', openCategoryModal);
  document.getElementById('cat-modal-close').addEventListener('click',  closeCategoryModal);
  document.getElementById('btn-cancel-cat').addEventListener('click',   closeCategoryModal);
  document.getElementById('btn-save-cat').addEventListener('click',     handleSaveCategory);

  // Close modals on overlay click
  document.getElementById('task-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeTaskModal();
  });
  document.getElementById('category-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeCategoryModal();
  });

  // Close modals with Escape key
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeTaskModal();
      closeCategoryModal();
    }
  });

  // --- Startup: check for saved token ---
  loadTokenFromStorage();

  if (state.token) {
    // Token found — try to restore session
    await initApp();
  } else {
    showAuthScreen();
  }
});