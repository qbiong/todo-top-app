const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const DATA_FILE = path.join(app.getPath('userData'), 'todos.json');

let mainWindow;

// 从 Alt+Tab 切换器中隐藏 (Windows)
function hideWindowFromAltTab(hwndBuffer) {
  const hwndVal = '0x' + hwndBuffer.readBigUInt64LE(0).toString(16);
  // 写入临时 ps1 文件，避免一切命令行转义问题
  const tmpFile = path.join(require('os').tmpdir(), 'hide-alttab-' + Date.now() + '.ps1');
  fs.writeFileSync(tmpFile,
`$c = 'using System;using System.Runtime.InteropServices;public class W {[DllImport("user32.dll",EntryPoint="SetWindowLongPtr")]public static extern IntPtr S(IntPtr h,int n,IntPtr d);[DllImport("user32.dll",EntryPoint="GetWindowLongPtr")]public static extern IntPtr G(IntPtr h,int n);}'
Add-Type -TypeDefinition $c
$h = [IntPtr]::new(${hwndVal})
$s = [W]::G($h, -20)
[W]::S($h, -20, [IntPtr]::new($s.ToInt64() -bor 128))
Remove-Item -Force '${tmpFile.replace(/\\/g, '\\\\')}'`,
    'utf-8');
  require('child_process').spawnSync(
    'powershell', ['-NoProfile', '-File', tmpFile],
    { timeout: 30000, stdio: 'ignore' }
  );
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

  // 从 Alt+Tab 切换器中隐藏
  if (process.platform === 'win32') {
    try {
      hideWindowFromAltTab(mainWindow.getNativeWindowHandle());
      console.log('Alt+Tab hiding applied successfully');
    } catch (e) { console.warn('Failed to hide from Alt+Tab:', e.message); }
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
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
