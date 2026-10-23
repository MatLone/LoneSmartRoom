"""Lone Smart Room Agent v1.5 (Python stdlib).

Runs in the signed-in user's session so it can launch Steam, without admin privileges.
Authenticated HMAC LAN commands. NEVER forward this service to the internet.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
AGENT_VERSION = '1.5.0'
APP_DIR = Path(os.environ.get('APPDATA', str(Path.home()))) / 'LoneSmartRoom'
CFG = APP_DIR / 'agent_config.json'
ALLOWED = {'sleep', 'restart', 'shutdown', 'steam', 'cs2', 'cancel_shutdown'}
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_NAME = 'LoneSmartRoomAgent'


def init_config() -> dict:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if CFG.exists():
        cfg = json.loads(CFG.read_text(encoding='utf-8'))
        validate_config(cfg)
        return cfg
    cfg = {
        'listen_ip': '172.31.250.8',
        'allowed_network': '172.31.250.0/24',
        'port': PORT,
        'secret_hex': secrets.token_hex(32),
    }
    write_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    ip = ipaddress.ip_address(cfg['listen_ip'])
    net = ipaddress.ip_network(cfg['allowed_network'], strict=False)
    if ip.version != 4 or not ip.is_private or ip not in net:
        raise ValueError('O IP de escuta deve ser IPv4 privado, contido na rede autorizada.')
    if not (1024 <= int(cfg['port']) <= 65535):
        raise ValueError('Porta de escuta inválida.')
    key = bytes.fromhex(cfg['secret_hex'])
    if len(key) != 32:
        raise ValueError('A chave de autenticação precisa ter 32 bytes.')


def write_config(cfg: dict) -> None:
    validate_config(cfg)
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with CFG.open('w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
    try:
        os.chmod(CFG, 0o600)
    except OSError:
        pass


def canonical(timestamp: str, nonce: str, method: str, path: str, body: bytes) -> bytes:
    return (f'{timestamp}\n{nonce}\n{method}\n{path}\n'.encode('ascii') + body)


class AgentState:
    def __init__(self, cfg: dict, executor=None):
        self.cfg = cfg
        self.network = ipaddress.ip_network(cfg['allowed_network'], strict=False)
        self.key = bytes.fromhex(cfg['secret_hex'])
        self.used_nonces: dict[str, float] = {}
        self.lock = threading.Lock()
        self.executor = executor or execute_action

    def authenticate(self, headers, method: str, path: str, body: bytes) -> bool:
        timestamp = headers.get('X-Lone-Timestamp', '')
        nonce = headers.get('X-Lone-Nonce', '')
        signature = headers.get('X-Lone-Signature', '')
        if not timestamp.isdecimal() or not (12 <= len(nonce) <= 64) or not all(c in '0123456789abcdef' for c in nonce):
            return False
        if not (len(signature) == 64 and all(c in '0123456789abcdef' for c in signature)):
            return False
        now = time.time()
        if abs(now - int(timestamp)) > 90:
            return False
        expected = hmac.new(self.key, canonical(timestamp, nonce, method, path, body), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        with self.lock:
            if nonce in self.used_nonces:
                return False
            # Periodic eviction bounds the nonce cache.
            for old, seen in list(self.used_nonces.items()):
                if seen < now - 180:
                    del self.used_nonces[old]
            self.used_nonces[nonce] = now
        return True


def execute_action(action: str) -> str:
    if sys.platform != 'win32':
        raise RuntimeError('Ações de sistema disponíveis somente no Windows.')
    if action == 'steam':
        os.startfile('steam://open/main')
        return 'Pedido para abrir Steam enviado.'
    if action == 'cs2':
        os.startfile('steam://rungameid/730')
        return 'Pedido para abrir Counter-Strike 2 enviado.'
    if action == 'shutdown':
        subprocess.run(['shutdown.exe', '/s', '/t', '15'], check=True, timeout=5)
        return 'Desligamento agendado para daqui a 15 segundos. Salve seus arquivos.'
    if action == 'restart':
        subprocess.run(['shutdown.exe', '/r', '/t', '15'], check=True, timeout=5)
        return 'Reinicialização agendada para daqui a 15 segundos.'
    if action == 'cancel_shutdown':
        subprocess.run(['shutdown.exe', '/a'], check=True, timeout=5)
        return 'Desligamento ou reinicialização cancelado.'
    if action == 'sleep':
        # Respond before suspending the network connection. Some machines may hibernate,
        # depending on their Windows sleep/hibernation policy.
        import ctypes
        def suspend():
            try:
                ctypes.windll.powrprof.SetSuspendState(False, False, False)
            except Exception as exc:
                print('Falha ao suspender:', exc, file=sys.stderr)
        threading.Timer(1.2, suspend).start()
        return 'Suspensão solicitada; a rede poderá desconectar.'
    raise ValueError('Ação não autorizada.')


def make_handler(state: AgentState):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'LoneAgent/1.5'
        sys_version = ''

        def log_message(self, fmt, *args):
            # No credentials or full requests are logged.
            pass

        def respond(self, code, payload):
            raw = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def handle_request(self, method):
            try:
                remote = ipaddress.ip_address(self.client_address[0])
                if remote not in state.network:
                    return self.respond(403, {'ok':False,'message':'Endereço de origem não autorizado.'})
                if self.path not in ('/v1/status', '/v1/action'):
                    return self.respond(404, {'ok':False,'message':'Rota desconhecida.'})
                if self.path == '/v1/status' and method != 'GET':
                    return self.respond(405, {'ok':False,'message':'Método não permitido.'})
                if self.path == '/v1/action' and method != 'POST':
                    return self.respond(405, {'ok':False,'message':'Método não permitido.'})
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    return self.respond(400, {'ok':False,'message':'Tamanho inválido.'})
                if size < 0 or size > 2048:
                    return self.respond(413, {'ok':False,'message':'Requisição muito grande.'})
                body = self.rfile.read(size) if size else b''
                if not state.authenticate(self.headers, method, self.path, body):
                    return self.respond(401, {'ok':False,'message':'Chave inválida, relógio fora de sincronia ou comando repetido.'})
                if method == 'GET':
                    return self.respond(200, {'ok':True,'status':'online','version':AGENT_VERSION})
                try:
                    data = json.loads(body)
                except (ValueError, UnicodeDecodeError):
                    return self.respond(400, {'ok':False,'message':'JSON inválido.'})
                action = data.get('action') if isinstance(data, dict) else None
                if action not in ALLOWED:
                    return self.respond(403, {'ok':False,'message':'Comando não permitido.'})
                if action in ('sleep','restart','shutdown') and data.get('confirmed') is not True:
                    return self.respond(400, {'ok':False,'message':'Confirmação obrigatória.'})
                try:
                    message = state.executor(action)
                    return self.respond(200, {'ok':True,'action':action,'message':message})
                except Exception:
                    return self.respond(500, {'ok':False,'message':'Falha ao executar no Windows; consulte o agente.'})
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self): self.handle_request('GET')
        def do_POST(self): self.handle_request('POST')
    return Handler


def install_autostart():
    if sys.platform != 'win32':
        raise RuntimeError('Configure o início automático no Windows.')
    import winreg
    exe = Path(sys.executable)
    invisible = exe.with_name('pythonw.exe')
    if invisible.exists(): exe = invisible
    command = subprocess.list2cmdline([str(exe), str(Path(__file__).resolve()), '--serve'])
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, command)
    return command


def remove_autostart():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        try: winreg.DeleteValue(key, RUN_NAME)
        except FileNotFoundError: pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--show-key', action='store_true')
    args = parser.parse_args()
    if args.uninstall:
        remove_autostart(); print('Inicialização automática desativada.'); return
    cfg = init_config()
    if args.install:
        command = install_autostart()
        print('Inicialização automática instalada para quando você entrar no Windows.')
        print('Agente:', command)
        print('Endereço:', f"http://{cfg['listen_ip']}:{cfg['port']}")
        print('Chave de pareamento (não compartilhe):', cfg['secret_hex'])
        print('Depois, execute INICIAR_AGENTE.bat ou entre novamente no Windows.')
    elif args.show_key:
        print('Endereço:', f"{cfg['listen_ip']}:{cfg['port']}")
        print('Chave de pareamento (não compartilhe):', cfg['secret_hex'])
    elif args.serve:
        server = ThreadingHTTPServer((cfg['listen_ip'], cfg['port']), make_handler(AgentState(cfg)))
        server.daemon_threads = True
        print(f"Lone Smart Room Agent v{AGENT_VERSION} ouvindo somente em {cfg['listen_ip']}:{cfg['port']} (rede {cfg['allowed_network']})")
        try: server.serve_forever(poll_interval=.4)
        except KeyboardInterrupt: pass
        finally: server.server_close()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
