const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('todoAPI', {
  load: () => ipcRenderer.invoke('todos:load'),
  save: (todos) => ipcRenderer.invoke('todos:save', todos),
  minimize: () => ipcRenderer.send('window:minimize'),
  close: () => ipcRenderer.send('window:close'),
});
