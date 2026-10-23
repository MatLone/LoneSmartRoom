"""Opt-in live status-only check. Test credentials stay in memory and are revoked."""
import hashlib
import http.client
import ipaddress
import json
from pathlib import Path
import secrets
import ssl
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent/windows'))
from secure_store import DPAPI
from secure_protocol import Store, validate_lan
from secure_tls import fingerprint


def main():
    state = ROOT / '.runtime/secure-agent'
    protector = DPAPI()
    config = json.loads(protector.open((state / 'config.dpapi').read_bytes()))
    validate_lan(config['host'], config['network'])
    firewall = json.loads((ROOT / '.cache/validation/secure-firewall.json').read_text(encoding='utf-8-sig'))
    if (not firewall['success'] or firewall['profile'] != 'Private' or firewall['interface'] != 'Ethernet'
            or str(firewall['localPort']) != str(config['port']) or firewall['edgeTraversal'] != 'Block'
            or ipaddress.ip_network(firewall['remoteAddress']) != ipaddress.ip_network(config['network'])
            or firewall['localAddress'] != config['host']):
        raise RuntimeError('Firewall receipt does not match the authorized LAN')
    context = ssl.create_default_context(cafile=str(state / 'server.crt'))
    store = Store(state / 'devices.db', protector)
    code, label = secrets.token_urlsafe(24), 'LSR local JVM probe ' + secrets.token_hex(6)
    digest = hashlib.sha256(code.encode()).hexdigest()
    report = {'physicalAndroidTest': False, 'apkInstalled': False, 'powerActionExecuted': False,
              'routerChanged': False, 'testCredentialRevoked': False}
    # Preserve any pairing window the user may already be using.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM pairing WHERE expires>?', (int(time.time()),)).fetchone():
            raise RuntimeError('An active user pairing window exists; no test code was issued')
        db.execute('INSERT INTO pairing VALUES (?,?)', (digest, int(time.time()) + 180))
    try:
        connection = http.client.HTTPSConnection(config['host'], config['port'], timeout=15, context=context)
        try:
            connection.request('POST', '/v2/pair', json.dumps({'code': code, 'label': label}),
                               {'Content-Type': 'application/json'})
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError('Live HTTPS pairing was rejected')
            device = json.loads(response.read(4096))
            if not device.get('ok'):
                raise RuntimeError('Invalid pairing response')
            report['pairingHttpsPassed'] = True
        finally:
            connection.close()
        jdk = Path('C:/Program Files/Android/Android Studio/jbr/bin')
        output = ROOT / '.cache/tests/lan-probe'
        output.mkdir(parents=True, exist_ok=True)
        kotlin = ROOT / 'apps/android/app/build/tmp/kotlin-classes/debug'
        java = ROOT / 'apps/android/app/build/intermediates/javac/debug/compileDebugJavaWithJavac/classes'
        stdlib = next((ROOT / '.cache/gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.0.21').rglob('kotlin-stdlib-2.0.21.jar'))
        classpath = ';'.join(map(str, (kotlin, java, stdlib)))
        compile_result = subprocess.run([str(jdk/'javac.exe'), '-encoding', 'UTF-8', '-classpath', classpath,
            '-d', str(output), str(ROOT/'tests/LanStatusProbe.java')], capture_output=True, text=True)
        if compile_result.returncode:
            raise RuntimeError('JVM probe compilation failed: ' + compile_result.stderr)

        def run(mode):
            result = subprocess.run([str(jdk/'java.exe'), '-classpath', str(output)+';'+classpath, 'LanStatusProbe',
                config['host'], str(config['port']), fingerprint(state), mode],
                input=device['device_id']+'\n'+device['secret']+'\n', capture_output=True, text=True, timeout=60)
            if result.returncode:
                # Java prints only generic assertions, never request headers or credentials.
                raise RuntimeError('JVM HTTPS probe failed: ' + result.stderr)
            return json.loads(result.stdout)
        report['androidProductionJvm'] = run('active')
        if not store.revoke(device['device_id']):
            raise RuntimeError('Temporary device revocation failed')
        report['androidProductionJvm'].update(run('revoked'))
        report['success'] = True
    finally:
        # Even an interrupted response cannot leave an authorized test identity.
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE devices SET revoked=1 WHERE label=?', (label,))
            db.execute('DELETE FROM pairing WHERE hash=?', (digest,))
            active = db.execute('SELECT 1 FROM devices WHERE label=? AND revoked=0', (label,)).fetchone()
        report['testCredentialRevoked'] = active is None
        (ROOT / '.cache/validation/secure-lan-probe.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
