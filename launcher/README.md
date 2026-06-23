# FeintSignal Launcher

A native **Windows desktop control panel** (WPF) for FeintSignal. It launches the backend
(FastAPI) and frontend (Vite) **silently in the background**, opens the dashboard as a Brave fullscreen
app window, runs the pipeline, and shows live status — no terminal required.

Mirrors the FeintTrade / FeintSupplyCo launcher convention.

## Install the desktop app

Run once from the project root:

```powershell
npm run install-launcher
```

That creates two Desktop + Start Menu shortcuts:
- **FeintSignal** — the control panel ([`fs-app.ps1`](fs-app.ps1)): buttons + live status.
- **FeintSignal Dashboard** — opens the dashboard straight into a **Brave fullscreen app window**, starting the backend + frontend silently if needed ([`fs-terminal.ps1`](fs-terminal.ps1)).

To launch without shortcuts:

```powershell
npm run app        # control panel
npm run terminal   # dashboard in Brave fullscreen
npm run browser:test
```

## What the control panel does

- **Live status bar** — Backend (up/down :8765), Frontend (up/down :5173), Readiness (FEINTCON level, pulled live from the API), Discord (send ON/OFF), plus a Refresh button.
- **Dashboard & Stack** — Open Dashboard, Start Stack, Start Backend, Start Frontend, Stop All.
- **Pipeline & Data** — Seed Mock Data, Run Pipeline Now, Run Tests, API Docs.
- **Background Automation** — Install / Remove the hidden hourly updater (Task Scheduler).
- **Files & Tools** — open `launcher.log`, the data folder, the project folder, `.env.example`, or the classic terminal menu.

### How "silent" works

- The backend is started with **`pythonw.exe`** (from `.venv`) with output redirected to ignored files under `logs/`.
- The frontend dev server is started in a **hidden** PowerShell (`-WindowStyle Hidden`) with redirected logs.
- The desktop shortcut runs PowerShell **`-STA -WindowStyle Hidden`**, so only the app window shows.
- "Run" buttons (Seed / Pipeline / Tests) intentionally open a **visible** window so you can watch output.

### Browser launch behavior

- URL-opening launcher actions prefer Brave with `--new-window --start-fullscreen`.
- The dashboard keeps a dedicated app-window profile under `%LOCALAPPDATA%\FeintSignalTerminal`.
- If Brave is unavailable, the helper logs a warning and falls back to the default browser.
- Optional overrides: `FEINT_BROWSER_PATH`, `FEINT_BROWSER`, and `FEINT_BROWSER_MODE`.
- Supported modes: `fullscreen` (default), `maximized`, `normal`, and explicit `kiosk`.

Example:

```powershell
$env:FEINT_BROWSER_MODE="fullscreen"
$env:FEINT_BROWSER_PATH="C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```

## Background automation (always-on)

```powershell
.\scripts\install-autostart.ps1 -Install                 # hidden hourly pipeline updater
.\scripts\install-autostart.ps1 -Install -StartBackendAtLogon
.\scripts\install-autostart.ps1 -Uninstall
```

This registers Scheduled Tasks through a hidden PowerShell wrapper with redirected Python output (and optionally starts the
backend at logon). It only runs the **local** deterministic pipeline against mock data — it does **not**
enable live research, LLM calls, or Discord sending.

## Uninstall

Delete the shortcut files:
- `%USERPROFILE%\Desktop\FeintSignal.lnk`, `FeintSignal Dashboard.lnk`
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\FeintSignal*.lnk`

And remove the background tasks: `.\scripts\install-autostart.ps1 -Uninstall`.

## Notes

- Uses WPF built into Windows — no extra dependencies. If WPF can't load, it falls back to the text
  menu ([`fs-menu.ps1`](fs-menu.ps1)), also reachable via the **Terminal Menu** button.
- Requires the backend `.venv` (`py -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt`).
  The frontend installs its own `node_modules` on first launch if missing.
- If `fs.ico` is missing, [`generate-icon.ps1`](generate-icon.ps1) recreates it during install.
- FEINTCON is an internal FeintSignal readiness indicator — not official DEFCON.
