'use strict';
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {validBounds} = require('./desktop-preferences.cjs');
const entryUrl = pathToFileURL(path.join(__dirname, 'index.html')).href;
const resources = new Set([
  'index.html', 'desktop.css', 'desktop.js', 'app-version.js',
  'monitoring-model.js', 'monitoring-renderer.js', 'monitoring.css',
  'hardware-diagnostics.js', 'hardware-diagnostics-renderer.js',
  'diagnostics-contract.js', 'diagnostics-model.js', 'diagnostics-renderer.js', 'diagnostics.css',
  'history-renderer.js','history.css','gamer-session.js','gamer-session-renderer.js','gamer-session.css',
  'audio-session.js',
  'panel.html','panel.css','panel.js',
  'workbench-model.js','workbench-renderer.js','workbench.css',
  'inventory-presentation.js','focused-renderer.js','rgb-renderer.js',
  'assets/brand/logo-horizontal.svg', 'assets/brand/logo-header-small.svg',
  'assets/brand/windows-icon.svg', 'assets/brand/windows-icon.png'
].map(name => pathToFileURL(path.join(__dirname, name)).href));

function trustedSender(event, webContents) {
  return Boolean(webContents && !webContents.isDestroyed() && event.sender === webContents &&
    event.senderFrame === webContents.mainFrame && event.senderFrame?.url === entryUrl);
}
function validMode(value) { return value === 'dashboard' || value === 'widget'; }
function allowedResource(url) { return resources.has(url); }
function clampBounds(bounds, workArea) {
  const width = Math.round(Math.min(Math.max(bounds.width, Math.min(350, workArea.width)), workArea.width));
  const height = Math.round(Math.min(Math.max(bounds.height, Math.min(530, workArea.height)), workArea.height));
  return {width, height,
    x: Math.round(Math.min(Math.max(bounds.x, workArea.x), workArea.x + workArea.width - width)),
    y: Math.round(Math.min(Math.max(bounds.y, workArea.y), workArea.y + workArea.height - height))};
}
function initialBounds(mode, workArea) {
  const width = mode === 'widget' ? 440 : 1360;
  const height = mode === 'widget' ? 820 : 960;
  const size = {width: Math.min(width, workArea.width - 32), height: Math.min(height, workArea.height - 32)};
  return clampBounds({...size,
    x: workArea.x + (mode === 'widget' ? workArea.width - size.width - 18 : (workArea.width - size.width) / 2),
    y: workArea.y + (workArea.height - size.height) / 2}, workArea);
}
function restoreBounds(bounds, workAreas, primary) {
  if (!validBounds(bounds)) return initialBounds('dashboard', primary);
  let selected = primary, overlap = 0;
  for (const area of workAreas) {
    const intersection = Math.max(0, Math.min(bounds.x + bounds.width, area.x + area.width) - Math.max(bounds.x, area.x)) *
      Math.max(0, Math.min(bounds.y + bounds.height, area.y + area.height) - Math.max(bounds.y, area.y));
    if (intersection > overlap) {overlap = intersection;selected = area;}
  }
  return clampBounds(bounds, selected);
}
module.exports = {entryUrl, trustedSender, validMode, allowedResource, clampBounds, initialBounds, restoreBounds, validBounds};
