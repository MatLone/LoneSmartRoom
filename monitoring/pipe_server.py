"""Native transport around the existing cache-only v1 read service. No autostart."""
import json
import time

from .ipc import LocalAccessPolicy, LocalReadService, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, encode
from .pipe_protocol import pipe_name


class PipeServer:
    def __init__(self, api, collector, session, client_handle, client_identity, stop, *, duration=70, simulated=False):
        if type(duration) not in (int, float) or not 1 <= duration <= 75:
            raise ValueError('invalid_development_duration')
        self.api, self.collector, self.stop = api, collector, stop
        self.client_handle, self.client_identity = client_handle, client_identity
        self.duration, self.name = duration, pipe_name(session)
        self.simulated = simulated
        self.service = LocalReadService(collector, LocalAccessPolicy(api.own['sid'], api.own['session']))
        self.handle = None
        self.counts = {'connections': 0, 'responses': 0, 'rejected': 0, 'timeouts': 0}

    def open(self):
        # Retain the same first-instance handle until shutdown; never a name-ownership gap.
        self.handle = self.api.create_server(self.name)
        try: self.api.inspect_dacl(self.handle)
        except Exception:
            self.close(); raise

    def serve(self):
        end = time.monotonic() + self.duration
        try:
            while not self.stop.is_set() and time.monotonic() < end and self.api.alive(self.client_handle):
                connected = False
                try:
                    self.api.accept(self.handle, min(end, time.monotonic()+0.25), self.stop)
                    connected = True; self.counts['connections'] += 1
                    self.api.peer(self.handle, self.client_handle, self.client_identity, server_side=True)
                    deadline = min(end, time.monotonic()+1.5)
                    payload = self.api.read_frame(self.handle, MAX_REQUEST_BYTES, deadline, self.stop)
                    evidence = self.api.client_token(self.handle)
                    response = self.service.handle(payload, evidence)
                    body = json.loads(response)
                    if body.get('ok') and 'transport' in body:
                        body.update(transport='windows_named_pipe_v1',
                                    hardware_inventory='basic_local_volumes', real_providers_included=not self.simulated)
                        response = encode(body)
                    self.api.write_frame(self.handle, response, MAX_RESPONSE_BYTES, deadline, self.stop)
                    # Bounded delivery acknowledgment avoids discarding buffered data on DisconnectNamedPipe.
                    if self.api.read_exact(self.handle, 1, deadline, self.stop) != b'\x06':
                        raise ValueError('invalid_delivery_ack')
                    self.counts['responses'] += 1
                except TimeoutError:
                    if connected: self.counts['timeouts'] += 1
                except (OSError, ValueError):
                    self.counts['rejected'] += 1
                    self.stop.wait(0.02)  # bounded admission work even for same-account invalid clients.
                finally:
                    if connected: self.api.k.DisconnectNamedPipe(self.handle)
        finally:
            self.close()

    def close(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            self.api.close(handle)
