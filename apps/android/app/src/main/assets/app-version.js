'use strict';
(() => {
  const label = document.getElementById('platformLabel');
  let platform = window.LoneAppInfo ? 'Android' : 'Widget Windows 11';
  const version = Promise.resolve().then(() => window.LoneAppInfo
    ? window.LoneAppInfo.getVersionName() : window.loneDesktop?.getVersion())
    .then(value => typeof value === 'string' && /^[0-9][0-9A-Za-z.+_-]{0,63}$/.test(value) ? value : null)
    .catch(() => null);
  const render = name => {
    platform = name;
    version.then(value => { label.textContent = `${platform} · ${value ? 'Versão ' + value : 'Versão indisponível'}`; });
  };
  window.loneVersion = Object.freeze({render});
  render(platform);
})();
