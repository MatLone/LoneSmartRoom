"""Narrow, explicitly reviewed changes to preserved presentation sources.

Legacy app.js permits only two version labels; the Android manifest permits
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
        return version_only_update(source)
    if path == 'apps/windows-ui/main.cjs':
        old = b'app.whenReady().then(()=>{'
        return source.replace(old, old + newline + b"  ipcMain.handle('widget:version',()=>app.getVersion());", 1)
    if path == 'apps/windows-ui/preload.cjs':
        old = b"contextBridge.exposeInMainWorld('loneDesktop',{"
        return source.replace(old, old + newline + b"  getVersion:()=>ipcRenderer.invoke('widget:version'),", 1)
    return source
