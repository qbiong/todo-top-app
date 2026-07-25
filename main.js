const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const DATA_FILE = path.join(app.getPath('userData'), 'todos.json');

let mainWindow;

function toggleWindow() {
  if (mainWindow?.isMinimized()) { mainWindow.restore(); mainWindow.focus(); }
  else if (mainWindow?.isVisible()) { mainWindow.minimize(); }
  else { mainWindow?.show(); mainWindow?.focus(); }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 320,
    height: 500,
    frame: false,
    transparent: false,
    resizable: true,
    alwaysOnTop: true,
    skipTaskbar: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  mainWindow.setAlwaysOnTop(true, 'floating');

  // Electron frameless 窗口默认显示任务栏图标
  // (skipTaskbar: false 保持默认行为)

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  globalShortcut.register('CommandOrControl+Shift+T', toggleWindow);
});

app.on('before-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ── Data persistence ──────────────────────────────────────────

function loadTodos() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
    }
  } catch (e) {
    console.error('Failed to load todos:', e);
  }
  return [];
}

function saveTodos(todos) {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(todos, null, 2), 'utf-8');
  } catch (e) {
    console.error('Failed to save todos:', e);
  }
}

// IPC handlers
ipcMain.handle('todos:load', () => loadTodos());
ipcMain.handle('todos:save', (_event, todos) => {
  saveTodos(todos);
  return true;
});

// Window control
ipcMain.on('window:minimize', () => mainWindow?.minimize());
ipcMain.on('window:close', () => mainWindow?.close());
