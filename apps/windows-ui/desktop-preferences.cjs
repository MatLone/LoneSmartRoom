'use strict';
// Visual state only. Fixed local filename; never accepts paths or credentials from IPC.
const fs = require('node:fs');
const path = require('node:path');
const MAX_BYTES = 8192;
const validBounds = value => Boolean(value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === 'height,width,x,y' &&
  ['x','y','width','height'].every(k => Number.isSafeInteger(value[k])) &&
  Math.abs(value.x) <= 1000000 && Math.abs(value.y) <= 1000000 &&
  value.width > 0 && value.width <= 32768 && value.height > 0 && value.height <= 32768);
const defaults = () => ({schema: 1, mode: 'dashboard', bounds: {dashboard: null, widget: null},
  dashboardMaximized: false, minimizeToTray: false});
function normalize(value) {
  if (!value || Array.isArray(value) || typeof value !== 'object' ||
      Object.keys(value).sort().join(',') !== 'bounds,dashboardMaximized,minimizeToTray,mode,schema' ||
      value.schema !== 1 || !['dashboard','widget'].includes(value.mode) ||
      typeof value.dashboardMaximized !== 'boolean' || typeof value.minimizeToTray !== 'boolean' ||
      !value.bounds || Array.isArray(value.bounds) || Object.keys(value.bounds).sort().join(',') !== 'dashboard,widget' ||
      !['dashboard','widget'].every(m => value.bounds[m] === null || validBounds(value.bounds[m]))) return null;
  return JSON.parse(JSON.stringify(value));
}
function createStore(userData, io = fs) {
  const file = path.join(userData, 'desktop-window-state.json');
  let status = 'default', writeAllowed = true;
  function load() {
    try {
      const stat = io.lstatSync(file);
      if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_BYTES) throw Error('Invalid visual state');
      const value = normalize(JSON.parse(io.readFileSync(file, 'utf8')));
      if (!value) throw Error('Invalid visual schema');
      writeAllowed = true;status = 'loaded';return value;
    } catch (error) {
      writeAllowed = error.code === 'ENOENT';status = writeAllowed ? 'default' : 'invalid';return defaults();
    }
  }
  function save(value) {
    const clean = normalize(value);
    if (!clean) throw new TypeError('Invalid visual state');
    // Unknown/corrupt existing data stays intact for diagnosis or future migration.
    if (!writeAllowed) {status = 'unavailable';return false;}
    const data = JSON.stringify(clean) + '\n';
    if (Buffer.byteLength(data) > MAX_BYTES) throw Error('Visual state too large');
    const temporary = file + '.' + process.pid + '.tmp';
    let fd, created = false;
    try {
      io.mkdirSync(userData, {recursive: true});
      try {const s = io.lstatSync(file);if (!s.isFile() || s.isSymbolicLink()) throw Error('Unsafe visual state target');}
      catch (error) {if (error.code !== 'ENOENT') throw error;}
      fd = io.openSync(temporary, 'wx', 0o600);created = true;
      io.writeFileSync(fd, data, 'utf8');io.fsyncSync(fd);io.closeSync(fd);fd = undefined;
      io.renameSync(temporary, file);status = 'saved';return true;
    } catch {status = 'unavailable';return false;}
    finally {
      if (fd !== undefined) try {io.closeSync(fd);} catch {}
      // Only remove the temporary file created by this call, never user data.
      if (created) try {io.unlinkSync(temporary);} catch (error) {if (error.code !== 'ENOENT') status = 'unavailable';}
    }
  }
  return {load, save, get status() {return status;}};
}
module.exports = {MAX_BYTES, validBounds, defaults, normalize, createStore};
