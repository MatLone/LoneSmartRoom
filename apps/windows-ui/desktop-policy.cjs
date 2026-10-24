'use strict';
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const entryUrl = pathToFileURL(path.join(__dirname, 'index.html')).href;
const resources = new Set([
  'index.html', 'desktop.css', 'desktop.js', 'app-version.js',
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
module.exports = {entryUrl, trustedSender, validMode, allowedResource, clampBounds, initialBounds};
