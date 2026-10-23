"""Local management: HTTPS status and separately granted allowlisted applications."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from secure_store import DPAPI
from secure_protocol import Store, validate_lan
from secure_tls import create_identity, fingerprint, server_context
from secure_http import StatusServer
from secure_startup import private_profile
from secure_apps import APPS, AppRegistry, AppDispatcher, launch_allowed

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.runtime' / 'secure-agent'
RUN_NAME = 'LoneSmartRoomSecureAgent'


def startup_command():
    executable = Path(sys.executable).with_name('pythonw.exe')
    if not executable.exists():
        executable = Path(sys.executable)
    return subprocess.list2cmdline([str(executable), str(Path(__file__).resolve()), 'serve'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    initialize = sub.add_parser('init')
    initialize.add_argument('--host', required=True)
    initialize.add_argument('--network', required=True)
    initialize.add_argument('--port', type=int, default=8776)
    for command in ('serve', 'pair', 'devices', 'install-startup', 'remove-startup'):
        sub.add_parser(command)
    sub.add_parser('revoke').add_argument('device')
    for permission in ('grant-apps', 'revoke-apps'):
        command = sub.add_parser(permission)
        command.add_argument('device')
        command.add_argument('--apps', nargs='+', choices=sorted(APPS), required=True)
    sub.add_parser('app-permissions').add_argument('device')
    args = parser.parse_args()
    protector = DPAPI()
    config_file = STATE / 'config.dpapi'
    if args.command == 'init':
        validate_lan(args.host, args.network)
        if not 1024 <= args.port <= 65535:
            parser.error('Invalid port')
        if config_file.exists():
            parser.error('Already initialized; no implicit certificate rotation')
        create_identity(STATE, args.host, protector)
        config_file.write_bytes(protector.seal(json.dumps({'host': args.host, 'network': args.network, 'port': args.port}).encode()))
        print('Identidade criada; HTTPS somente para status. Configure o firewall Privado antes de uso na LAN.')
        return
    config = json.loads(protector.open(config_file.read_bytes()))
    validate_lan(config['host'], config['network'])
    store = Store(STATE / 'devices.db', protector)
    if args.command == 'pair':
        code, expires = store.begin_pairing()
        payload = {'url': f"https://{config['host']}:{config['port']}", 'network': config['network'],
                   'sha256': fingerprint(STATE), 'code': code, 'expires': expires}
        # Only explicit local pairing prints this short-lived credential. Never log it.
        print('Servidor:', payload['url'])
        print('SHA-256 do certificado:', payload['sha256'])
        print('No Android, use Parear e copie SOMENTE este código diretamente desta tela Windows confiável:')
        print('LSR2.' + base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('='))
    elif args.command == 'devices':
        for device, label, revoked in store.devices():
            print(device, label, 'revogado' if revoked else 'status autorizado')
    elif args.command == 'revoke':
        print('Revogado.' if store.revoke(args.device) else 'Dispositivo não encontrado.')
    elif args.command in ('grant-apps', 'revoke-apps', 'app-permissions'):
        registry = AppRegistry(store)
        if args.command != 'app-permissions':
            registry.set_permission(args.device, args.apps, args.command == 'grant-apps')
        print('Aplicativos autorizados:', ', '.join(registry.permissions(args.device)) or 'nenhum')
    elif args.command in ('install-startup', 'remove-startup'):
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE) as key:
            if args.command == 'install-startup':
                winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, startup_command())
            else:
                try:
                    winreg.DeleteValue(key, RUN_NAME)
                except FileNotFoundError:
                    pass
        print('Inicialização por login configurada; independente do Electron.')
    elif args.command == 'serve':
        # Login can precede network availability. Wait without opening a listener.
        while True:
            try:
                while not private_profile(config['host']):
                    time.sleep(10)
                with StatusServer((config['host'], config['port']), server_context(STATE, protector), store,
                                  config['network'], private_guard=lambda: private_profile(config['host'])) as server:
                    # Bind succeeds before startup recovery, so a second serve
                    # process cannot invalidate work owned by the active listener.
                    server.apps = AppDispatcher(AppRegistry(store), launch_allowed,
                                                lambda: private_profile(config['host']))
                    worker = threading.Thread(target=server.serve_forever, daemon=True)
                    worker.start()
                    try:
                        while worker.is_alive() and private_profile(config['host']):
                            time.sleep(5)
                    finally:
                        server.shutdown()
                        worker.join(timeout=6)
                        server.apps.close()
            except KeyboardInterrupt:
                return


if __name__ == '__main__':
    sys.exit(main())
