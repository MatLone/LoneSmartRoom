"""Narrow, explicitly reviewed changes to preserved presentation sources.

Legacy app.js permits two version labels and one exact gear outline; the Android manifest permits
only the native icon resource references. All other baseline bytes, including
WoL settings, event bindings, permissions and packet callbacks, are preserved.
"""


def version_only_update(source):
    replacements = (
        (b'''$('#platformLabel').innerHTML='Android <b class="small-dot">\xc2\xb7</b> Vers\xc3\xa3o 1.4' ''',
         b"window.loneVersion.render('Android')"),
        (b'''$('#platformLabel').innerHTML=remote.mobile?'Pr\xc3\xa9via Android <b class="small-dot">\xc2\xb7</b> Vers\xc3\xa3o 1.4':'Widget Windows 11 <b class="small-dot">\xc2\xb7</b> Vers\xc3\xa3o 1.4' ''',
         b"window.loneVersion.render(remote.mobile?'Pr\xc3\xa9via Android':'Widget Windows 11')"),
    )
    for old, new in replacements:
        old = old.rstrip()
        if source.count(old) != 1:
            raise ValueError('Expected unique legacy version-label fragment')
        source = source.replace(old, new)
    return source


def reviewed_version_update(path, source):
    newline = b'\r\n' if b'\r\n' in source else b'\n'
    if path == 'apps/android/app/src/main/AndroidManifest.xml':
        return source.replace(b'android:icon="@drawable/ic_launcher"',
                              b'android:icon="@mipmap/ic_launcher"' + newline
                              + b'        android:roundIcon="@mipmap/ic_launcher_round"', 1)
    if path.endswith('/app.js'):
        return gear_only_update(version_only_update(source))
    if path == 'apps/windows-ui/main.cjs':
        old = b'app.whenReady().then(()=>{'
        return source.replace(old, old + newline + b"  ipcMain.handle('widget:version',()=>app.getVersion());", 1)
    if path == 'apps/windows-ui/preload.cjs':
        old = b"contextBridge.exposeInMainWorld('loneDesktop',{"
        return source.replace(old, old + newline + b"  getVersion:()=>ipcRenderer.invoke('widget:version'),", 1)
    return source


def gear_only_update(source):
    """Permit exactly the static legacy gear artwork; never handlers or actions."""
    old = b'''gear:'<circle cx="12" cy="12" r="3"/><path d="M19 13.5a1.6 1.6 0 0 0 .3 1.8l.1.1-1.8 3.1-.2-.1a1.6 1.6 0 0 0-1.7.6l-.1.2h-3.6l-.1-.2a1.6 1.6 0 0 0-1.7-.6l-.2.1-1.8-3.1.1-.1a1.6 1.6 0 0 0 .3-1.8V12a1.6 1.6 0 0 0-.3-1.8l-.1-.1L11 7l.2.1a1.6 1.6 0 0 0 1.7-.6l.1-.2h3.6l.1.2a1.6 1.6 0 0 0 1.7.6l.2-.1 1.8 3.1-.1.1a1.6 1.6 0 0 0-.3 1.8Z"/>' '''.rstrip()
    new = b'''gear:'<path d="M9.384 5.185 L10.368 2.743 L13.632 2.743 L14.616 5.185 L16.594 6.327 L19.201 5.958 L20.833 8.785 L19.210 10.858 L19.210 13.142 L20.833 15.215 L19.201 18.042 L16.594 17.673 L14.616 18.815 L13.632 21.257 L10.368 21.257 L9.384 18.815 L7.406 17.673 L4.799 18.042 L3.167 15.215 L4.790 13.142 L4.790 10.858 L3.167 8.785 L4.799 5.958 L7.406 6.327 Z"/><circle cx="12" cy="12" r="3"/>' '''.rstrip()
    if source.count(old) != 1:
        raise ValueError('Expected unique legacy gear definition')
    return source.replace(old, new, 1)
