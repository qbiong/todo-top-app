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

  // 窗口圆角 (Windows 11)
  if (process.platform === 'win32') {
    try {
      const { execSync } = require('child_process');
      const hwndBuf = mainWindow.getNativeWindowHandle();
      const hwndVal = '0x' + hwndBuf.readBigUInt64LE(0).toString(16);
      const tmpFile = path.join(require('os').tmpdir(), 'todo-owner-' + Date.now() + '.ps1');
      // 创建透明所有者窗口, 设置 Alt+Tab 隐藏同时保留任务栏图标
      fs.writeFileSync(tmpFile,
`Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;
public class W {
[DllImport("user32.dll")]public static extern IntPtr CreateWindowExW(int e,string c,string n,int s,int x,int y,int w,int h,IntPtr p,IntPtr m,IntPtr i,IntPtr d);
[DllImport("user32.dll",EntryPoint="SetWindowLongPtr")]public static extern IntPtr S(IntPtr h,int n,IntPtr d);
}
'@
$ow = [W]::CreateWindowExW(0x80,"Static","",0x40000000,0,0,0,0,0,0,0,0)
[W]::S([IntPtr]::new(${hwndVal}),-8,$ow)
Write-Host ('ok ' + \$ow.ToString('x8'))
Remove-Item -Force '${tmpFile.replace(/\\/g, '\\\\')}'`,
        'utf-8');
      execSync('powershell -NoProfile -File ' + tmpFile, { timeout: 10000, stdio: 'pipe' });
    } catch (e) { console.warn('Failed to set owner window:', e.message); }
  }

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
