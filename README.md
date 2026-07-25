# 置顶待办 · Todo Top App

Windows 桌面始终置顶的轻量级待办清单应用。支持 **Electron** 和 **Python/tkinter** 两种实现。

## 功能

- 始终置顶 — 窗口悬浮在桌面最前方，方便随时查看
- 添加/标记完成/删除待办事项
- 一键清除已完成事项
- 待办数量徽章
- 暗色主题

## 截图

| Electron 版本 | Python 版本 |
|:---:|:---:|
| ![Electron](screenshots/electron.png) | ![Python](screenshots/python.png) |

## 快速开始

### Electron 版本

```bash
npm start
```

> ⚠️ 首次启动会自动下载 Electron 二进制文件，请确保网络畅通。

### Python 版本

```bash
python todo-app.py
```

或双击 `启动待办.bat`。

> Python 3.13+ 必需，零外部依赖。

## 项目结构

```
todo-top-app/
├── main.js                    # Electron 主进程
├── preload.js                 # Electron IPC 桥接
├── package.json               # npm 配置
├── renderer/
│   ├── index.html             # Electron 渲染进程 (HTML)
│   ├── app.js                 # 前端逻辑
│   └── styles.css             # 暗色主题样式
├── todo-app.py                # Python/tkinter 版本
├── todo_app_store.py          # Python 数据持久化
└── 启动待办.bat               # Windows 快捷启动脚本
```

## 数据存储

两种版本均使用本地 JSON 文件持久化数据：

| 版本 | 存储路径 |
|------|---------|
| Electron | `%APPDATA%/todo-top-app/todos.json` |
| Python | `%APPDATA%/.todo-top-app/todos.json` |

## 技术栈

- **Electron 版本**: Electron 33+, Node.js, 原生 DOM API
- **Python 版本**: Python 3.13+, tkinter, ctypes (Windows DWM)

## 许可证

ISC
