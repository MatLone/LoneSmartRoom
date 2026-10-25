'use strict';
// Dependency-injected native window/Tray lifecycle. No agent or execution APIs.
function createController({app, screen, Tray, Menu, policy, store, createWindow, icon, version,
  metadata = {}, beforeExit=null, schedule = setTimeout, cancel = clearTimeout}) {
  let preferences = store.load(), mode = preferences.mode, win = null, tray = null;
  let timer = null, switching = false, exiting = false, hiddenToTray = false;
  let exitRequested=false;
  let persistenceAvailable = store.status !== 'invalid';
  const live = () => win && !win.isDestroyed();
  const trayAlive = () => Boolean(tray && !tray.isDestroyed());
  const areas = () => screen.getAllDisplays().map(d => d.workArea);
  const restoredBounds = next => {
    const saved = preferences.bounds[next];
    const primary = screen.getPrimaryDisplay().workArea;
    return saved ? policy.restoreBounds(saved, areas(), primary) : policy.initialBounds(next, primary);
  };
  function state() {
    if (!live()) return null;
    const [width, height] = win.getContentSize();
    return {...metadata, mode, maximized: win.isMaximized(), width, height, trayAvailable: trayAlive(), hiddenToTray,
      persistenceAvailable, communication: 'not-integrated', operationalActionsAvailable: false};
  }
  function publish() {
    if (live() && win.webContents.mainFrame.url === policy.entryUrl) win.webContents.send('window:state', state());
  }
  function capture() {
    if (!live() || switching || win.isMinimized()) return;
    const bounds = win.getNormalBounds();
    if (policy.validBounds(bounds)) preferences.bounds[mode] = {...bounds};
    preferences.mode = mode;
    if (mode === 'dashboard') preferences.dashboardMaximized = win.isMaximized();
  }
  function flush() {
    if (timer !== null) {cancel(timer);timer = null;}
    capture();persistenceAvailable = store.save(preferences);return persistenceAvailable;
  }
  function changed() {
    if (switching || exiting) return;
    capture();if (timer !== null) cancel(timer);
    timer = schedule(() => {timer = null;persistenceAvailable = store.save(preferences);publish();}, 180);
    timer?.unref?.();publish();
  }
  function ensureVisibleBounds() {
    if (!live()) return;
    const bounds = win.getNormalBounds();
    const valid = policy.restoreBounds(bounds, areas(), screen.getPrimaryDisplay().workArea);
    if (['x','y','width','height'].some(k => valid[k] !== bounds[k])) {
      switching = true;const maximized = win.isMaximized();
      try {if (maximized) win.unmaximize();win.setBounds(valid);if (maximized && mode === 'dashboard') win.maximize();}
      finally {switching = false;}
      changed();
    }
  }
  function restoreCurrent() {
    if (exiting || !live()) return;
    hiddenToTray = false;
    if (win.isMinimized()) win.restore();
    ensureVisibleBounds();win.show();win.focus();publish();
  }
  function setMode(next) {
    if (!policy.validMode(next)) throw new TypeError('Invalid window mode');
    if (!live() || exiting) return null;
    if (next === mode) return state();
    capture();switching = true;
    try {
      if (win.isMaximized()) win.unmaximize();
      mode = next;preferences.mode = next;win.setBounds(restoredBounds(next));
      if (next === 'dashboard' && preferences.dashboardMaximized) win.maximize();
    } finally {switching = false;}
    changed();return state();
  }
  function showMode(next) {setMode(next);restoreCurrent();}
  function hideToTray() {
    if (exiting || !live()) return false;
    if (!trayAlive()) {restoreCurrent();return false;}
    flush();hiddenToTray = true;win.hide();publish();return true;
  }
  function destroyTray() {try {if (trayAlive()) tray.destroy();} catch {} finally {tray = null;}}
  function quit() {
    if (exiting) return;
    if(beforeExit){
      if(exitRequested)return;
      exitRequested=true;
      Promise.resolve().then(beforeExit).then(ok=>{
        exitRequested=false;
        if(!ok){restoreCurrent();return;}
        exiting=true;try{flush();}finally{destroyTray();app.quit();}
      },()=>{exitRequested=false;restoreCurrent();});return;
    }
    exiting = true;try {flush();} finally {destroyTray();app.quit();}
  }
  function beforeQuit(event) {if(event?.defaultPrevented)return;exiting = true;flush();destroyTray();}
  function makeTray() {
    try {
      tray = new Tray(icon);tray.setToolTip('Lone Smart Room · ' + version);
      tray.setContextMenu(Menu.buildFromTemplate([
        {id: 'dashboard', label: 'Abrir dashboard', click: () => showMode('dashboard')},
        {id: 'widget', label: 'Modo Widget', click: () => showMode('widget')},
        {type: 'separator'}, {id: 'exit', label: 'Sair', click: quit}
      ]));
      tray.on('click', restoreCurrent);tray.on('double-click', restoreCurrent);
    } catch {destroyTray();}
  }
  function start() {
    if (live() || exiting) return;
    const initial = restoredBounds(mode);
    win = createWindow(initial);
    for (const event of ['resize','move','maximize','unmaximize','restore']) win.on(event, changed);
    win.on('close', event=>{
      // X still exits; it waits for our own monitoring components, never hides to Tray.
      if(beforeExit&&!exiting){event.preventDefault();quit();}else flush();
    });
    win.on('closed', () => {win = null;});
    win.once('ready-to-show', () => {
      // The first Windows show can adjust non-client geometry for the monitor DPI.
      // Reapply validated outer bounds after that transition to prevent size drift.
      switching = true;
      try {
        if (!hiddenToTray) win.show();
        win.setBounds(initial);
        if (mode === 'dashboard' && preferences.dashboardMaximized) win.maximize();
      } finally {switching = false;}
      publish();
    });
    makeTray();
    screen.on('display-removed', ensureVisibleBounds);screen.on('display-metrics-changed', ensureVisibleBounds);
    app.on('before-quit', beforeQuit);
  }
  return {start, state, setMode, restoreCurrent, hideToTray, quit, flush,
    minimize: () => {if (live()) win.minimize();},
    close: () => {if (live()) win.close();},
    toggleMaximize: () => {if (live() && mode === 'dashboard') {if (win.isMaximized()) win.unmaximize();else win.maximize();}return state();},
    get window() {return win;}};
}
module.exports = {createController};
