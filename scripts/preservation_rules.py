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
    new = b'''gear:'<path stroke-linejoin="bevel" d="M9.836 4.923 L10.514 2.617 L13.486 2.617 L14.164 4.923 L15.474 5.466 L17.584 4.314 L19.686 6.416 L18.534 8.526 L19.077 9.836 L21.383 10.514 L21.383 13.486 L19.077 14.164 L18.534 15.474 L19.686 17.584 L17.584 19.686 L15.474 18.534 L14.164 19.077 L13.486 21.383 L10.514 21.383 L9.836 19.077 L8.526 18.534 L6.416 19.686 L4.314 17.584 L5.466 15.474 L4.923 14.164 L2.617 13.486 L2.617 10.514 L4.923 9.836 L5.466 8.526 L4.314 6.416 L6.416 4.314 L8.526 5.466 Z"/><circle cx="12" cy="12" r="3.1"/>' '''.rstrip()
    if source.count(old) != 1:
        raise ValueError('Expected unique legacy gear definition')
    return source.replace(old, new, 1)
