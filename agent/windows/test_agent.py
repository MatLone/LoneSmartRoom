import importlib.util
from pathlib import Path
import hashlib
import hmac
from http.server import ThreadingHTTPServer
import json
import secrets
import threading
import time
import urllib.error
import urllib.request

spec = importlib.util.spec_from_file_location('agent', Path(__file__).with_name('agent.py'))
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


def request(path, method, body, key, nonce=None, time_offset=0, sig_override=None):
    stamp = str(int(time.time()) + time_offset)
    nonce = nonce or secrets.token_hex(16)
    canon = agent.canonical(stamp, nonce, method, path, body)
    signature = sig_override or hmac.new(key, canon, hashlib.sha256).hexdigest()
    headers = {'X-Lone-Timestamp': stamp, 'X-Lone-Nonce':nonce, 'X-Lone-Signature':signature}
    if method == 'POST': headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(base+path, data=(body if method=='POST' else None), method=method, headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=3) as result:
            return result.status,json.loads(result.read())
    except urllib.error.HTTPError as err:
        return err.code,json.loads(err.read())


if __name__ == '__main__':
    key=bytes.fromhex('1a'*32)
    cfg={'listen_ip':'127.0.0.1','allowed_network':'127.0.0.0/8','port':8889,'secret_hex':key.hex()}
    acts=[]
    state=agent.AgentState(cfg, executor=lambda act: acts.append(act) or f'Executado: {act}')
    server=ThreadingHTTPServer(('127.0.0.1',0),agent.make_handler(state))
    base='http://127.0.0.1:'+str(server.server_port)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        assert request('/v1/status','GET',b'',key)[0]==200
        assert request('/v1/status','GET',b'',key,sig_override='0'*64)[0]==401
        assert request('/v1/status','GET',b'',key,time_offset=-180)[0]==401
        nonce=secrets.token_hex(16)
        assert request('/v1/status','GET',b'',key,nonce=nonce)[0]==200
        assert request('/v1/status','GET',b'',key,nonce=nonce)[0]==401
        assert request('/v1/action','POST',b'{"action":"cmd"}',key)[0]==403
        assert request('/v1/action','POST',b'{"action":"shutdown"}',key)[0]==400
        assert request('/v1/action','POST',b'{"action":"steam"}',key)[0]==200
        assert request('/v1/action','POST',b'{"action":"shutdown","confirmed":true}',key)[0]==200
        assert acts==['steam','shutdown']
        print('PASS: status autenticado, chave incorreta, expiração, anti-replay, allowlist, confirmação e execução mock')
    finally:
        server.shutdown();server.server_close()
