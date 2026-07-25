const { app, BrowserWindow, globalShortcut, ipcMain, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
let tray;

const DATA_FILE = path.join(app.getPath('userData'), 'todos.json');

let mainWindow;
let _isQuitting = false;

// ── 系统托盘 ──────────────────────────────────────────
function makeTrayBuffer() {
  const zlib = require('zlib');
  const S = 16;
  const raw = Buffer.alloc(S * (S * 4 + 1));
  for (let y = 0; y < S; y++) {
    raw[y * (S * 4 + 1)] = 0;
    for (let x = 0; x < S; x++) {
      const p = y * (S * 4 + 1) + 1 + x * 4;
      raw[p] = 0x7c; raw[p + 1] = 0x5c; raw[p + 2] = 0xfc; raw[p + 3] = 0xff;
    }
  }
  const deflated = zlib.deflateSync(raw, { level: 9 });
  const tbl = new Int32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    tbl[i] = c;
  }
  const crc32 = (b) => { let c = -1; for (let i = 0; i < b.length; i++) c = tbl[(c ^ b[i]) & 0xFF] ^ (c >>> 8); return (c ^ -1) >>> 0; };
  const ck = (t, d) => { const tb = Buffer.from(t, 'ascii'), db = Buffer.concat([tb, d]); const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const cr = Buffer.alloc(4); cr.writeUInt32BE(crc32(db)); return Buffer.concat([l, tb, d, cr]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(S, 0); ihdr.writeUInt32BE(S, 4); ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = ihdr[11] = ihdr[12] = 0;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), ck('IHDR', ihdr), ck('IDAT', deflated), ck('IEND', Buffer.alloc(0))]);
}

function toggleWindow() {
  if (mainWindow?.isVisible()) { mainWindow.hide(); }
  else { mainWindow?.show(); mainWindow?.focus(); }
}

function createTray() {
  tray = new Tray(nativeImage.createFromBuffer(makeTrayBuffer(), { width: 16, height: 16 }));
  tray.setToolTip('置顶待办');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: '打开 / 隐藏', click: toggleWindow },
    { type: 'separator' },
    { label: '退出', click: () => { _isQuitting = true; app.quit(); } },
  ]));
  tray.on('click', toggleWindow);
}

// ── Alt+Tab 隐藏 (Windows) ────────────────────────────
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
  createTray();
  globalShortcut.register('CommandOrControl+Shift+T', toggleWindow);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  _isQuitting = true;
  globalShortcut.unregisterAll();
  if (tray) { tray.destroy(); tray = null; }
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
ipcMain.on('window:minimize', () => mainWindow?.hide());
ipcMain.on('window:close', () => { _isQuitting = true; mainWindow?.close(); });
