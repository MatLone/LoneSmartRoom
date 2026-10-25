"""Mock-only pipe security/lifecycle tests. No native library or sensor operation."""
import ctypes as ct
import json
import struct
import threading
import unittest
from unittest.mock import Mock, patch

from monitoring.collector import Collector
from monitoring.ipc import LocalReadService, LocalAccessPolicy, PeerEvidence
from monitoring.pipe_protocol import CLIENT_RIGHTS, descriptor, frame, length, pipe_name, request, same_peer
from monitoring.pipe_server import PipeServer
from monitoring.winpipe import WindowsPipeApi, Overlapped, SecurityAttributes
from monitoring.windows_basic import basic_catalog
from monitoring_fakes import FakeClock
from pipe_fixture import FixtureProvider
from monitoring.development_collector import create_basic_collector

SID = 'S-1-5-21-100000000-200000000-300000000-1001'
IDENTITY = dict(pid=12, created=12345, sid=SID, session=1, image='c:\\python\\python.exe', elevated=False)


class ProtocolTests(unittest.TestCase):
    def test_pipe_names_only_fixed_local_development_namespace(self):
        self.assertEqual(pipe_name('a'*32), '\\\\.\\pipe\\LoneSmartRoom.Monitoring.Dev.v1.'+'a'*32)
        for value in ('server\\pipe', 'x'*32, 'a'*31, 'A'*32, None, 12, '../escape'):
            with self.assertRaises(ValueError): pipe_name(value)

    def test_descriptor_protected_account_only_no_create_instance_right(self):
        self.assertEqual(descriptor(SID), 'O:'+SID+'G:'+SID+'D:P(A;;0x00120183;;;'+SID+')')
        self.assertFalse(CLIENT_RIGHTS & 4)
        self.assertFalse(CLIENT_RIGHTS & 0x40000)  # no WRITE_DAC to client via this ACE.
        for value in ('Everyone',SID+'(A;;GA;;;WD)',None):
            with self.assertRaises(ValueError): descriptor(value)

    def test_frame_limits_and_header(self):
        self.assertEqual(frame(b'a',256), b'\0\0\0\1a')
        self.assertEqual(length(struct.pack('!I',256),256),256)
        for payload in (b'',b'x'*257,'a'):
            with self.assertRaises(ValueError):frame(payload,256)
        for header in (b'',b'123',struct.pack('!I',0),struct.pack('!I',257),struct.pack('!I',2**32-1)):
            with self.assertRaises(ValueError):length(header,256)

    def test_only_exact_read_requests(self):
        for op in ('snapshot','capabilities'):self.assertEqual(request(json.dumps({'v':1,'op':op}).encode())['op'],op)
        for raw in (b'{"v":true,"op":"snapshot"}',b'{"v":1,"op":"stop"}',b'{"v":1,"op":"snapshot","path":"cmd.exe"}',
                    b'{"v":1,"v":1,"op":"snapshot"}',b'{"v":NaN,"op":"snapshot"}',b'[]',b'\xff',b'x'*257):
            with self.assertRaises((ValueError,TypeError)):request(raw)

    def test_pid_creation_owner_session_image_and_no_elevation(self):
        self.assertTrue(same_peer(IDENTITY,IDENTITY))
        for key in IDENTITY:
            altered={**IDENTITY,key:True if key=='elevated' else 'changed'}
            self.assertFalse(same_peer(altered,IDENTITY),key)

    def test_native_abi(self):
        self.assertEqual(ct.sizeof(Overlapped),32)
        self.assertEqual(ct.sizeof(SecurityAttributes),24)


class NativeMockTests(unittest.TestCase):
    def setUp(self):
        self.api=WindowsPipeApi.__new__(WindowsPipeApi)
        self.api.k=Mock();self.api.a=Mock();self.api.own=IDENTITY
        self.api.k.CloseHandle.return_value=1

    def test_create_first_instance_explicit_acl_remote_reject_no_inheritance(self):
        self.api.a.ConvertStringSecurityDescriptorToSecurityDescriptorW.return_value=1
        self.api.k.CreateNamedPipeW.return_value=45
        self.assertEqual(self.api.create_server(pipe_name('a'*32)),45)
        args=self.api.k.CreateNamedPipeW.call_args.args
        self.assertEqual(args[1],3|0x40000000|0x00080000)
        self.assertEqual(args[2],8);self.assertEqual(args[3],1)
        self.assertFalse(args[-1]._obj.inherit)
        self.api.k.LocalFree.assert_called_once()

    def test_endpoint_occupied_fails_and_descriptor_freed(self):
        self.api.a.ConvertStringSecurityDescriptorToSecurityDescriptorW.return_value=1
        self.api.k.CreateNamedPipeW.return_value=ct.c_void_p(-1).value
        with self.assertRaises(OSError):self.api.create_server(pipe_name('a'*32))
        self.api.k.LocalFree.assert_called_once()

    def test_client_native_rights_and_server_attestation_before_return(self):
        self.api.k.CreateFileW.return_value=34;self.api.peer=Mock()
        with patch('monitoring.winpipe.time.monotonic',return_value=0):
            self.assertEqual(self.api.connect(pipe_name('a'*32),1,IDENTITY,10,threading.Event()),34)
        self.assertEqual(self.api.k.CreateFileW.call_args.args[1],CLIENT_RIGHTS)
        self.api.peer.assert_called_once()
        self.api.peer.side_effect=PermissionError('no')
        with patch('monitoring.winpipe.time.monotonic',return_value=0),self.assertRaises(PermissionError):
            self.api.connect(pipe_name('a'*32),1,IDENTITY,10,threading.Event())
        self.api.k.CloseHandle.assert_called_with(34)

    def test_token_read_and_revert_even_if_close_fails(self):
        self.api.a.ImpersonateNamedPipeClient.return_value=1
        self.api.a.RevertToSelf.return_value=1
        def opened(thread,access,own,ptr):ptr._obj.value=20;return 1
        def level(token,info,ptr,size,out):ptr._obj.value=1;return 1
        self.api.a.OpenThreadToken.side_effect=opened;self.api.a.GetTokenInformation.side_effect=level
        self.api.token_identity=Mock(return_value={k:IDENTITY[k] for k in ('sid','session','elevated')})
        self.assertEqual(self.api.client_token(4),PeerEvidence(SID,1,True,False))
        self.api.a.RevertToSelf.assert_called_once()
        self.api.close=Mock(side_effect=OSError('close'))
        with self.assertRaises(OSError):self.api.client_token(4)
        self.assertEqual(self.api.a.RevertToSelf.call_count,2)

    def test_failed_impersonation_denied_no_service_work(self):
        self.api.a.ImpersonateNamedPipeClient.return_value=0
        with self.assertRaises(OSError):self.api.client_token(4)
        self.api.a.OpenThreadToken.assert_not_called()

    def test_revert_failure_fatal(self):
        self.api.a.ImpersonateNamedPipeClient.return_value=1
        self.api.a.OpenThreadToken.return_value=0;self.api.a.RevertToSelf.return_value=0
        with self.assertRaises(RuntimeError):self.api.client_token(4)

    def test_pending_timeout_cancels_and_waits_before_freeing(self):
        self.api.k.CreateEventW.return_value=8;self.api.k.ReadFile.return_value=0
        stop=threading.Event();stop.set()
        with patch('monitoring.winpipe.ct.get_last_error',return_value=997),self.assertRaises(TimeoutError):
            self.api._io(4,'read',ct.create_string_buffer(4),4,10,stop)
        self.api.k.CancelIoEx.assert_called_once()
        self.assertTrue(self.api.k.GetOverlappedResult.call_args.args[-1])
        self.api.k.CloseHandle.assert_called_with(8)


class ServiceTransportTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock();specs=basic_catalog(('C:\\','D:\\'))
        self.collector=Collector(specs,[FixtureProvider(specs)],clock=self.clock);self.collector.step()
        self.api=Mock();self.api.own=IDENTITY;self.stop=threading.Event()
        self.server=PipeServer(self.api,self.collector,'a'*32,34,IDENTITY,self.stop)

    def test_new_endpoint_only_once_and_close_idempotent(self):
        self.api.create_server.return_value=99;self.server.open();self.server.close();self.server.close()
        self.api.close.assert_called_once_with(99)

    def test_request_never_triggers_provider_read(self):
        before=self.collector.cache.sample_count
        for _ in range(4):
            response=json.loads(self.server.service.handle(b'{"v":1,"op":"snapshot"}',PeerEvidence(SID,1,True,False)))
            self.assertTrue(response['ok']);self.assertTrue(response['snapshot']['contains_simulated'])
        self.assertEqual(self.collector.cache.sample_count,before)
        self.assertEqual(json.loads(self.server.service.handle(b'{"v":1,"op":"snapshot"}',PeerEvidence(SID,1,True,False)))['error'],'rate_limited')

    def test_access_denied_before_read_cache(self):
        for peer in (PeerEvidence(SID,2,True,False),PeerEvidence(SID,1,True,True),PeerEvidence(SID,1,False,False),PeerEvidence('S-1-5-18',1,True,False)):
            self.assertEqual(json.loads(self.server.service.handle(b'{"v":1,"op":"snapshot"}',peer))['error'],'access_denied')

    def test_stop_prevents_snapshot_and_resources_released(self):
        self.collector.stop(1)
        answer=json.loads(self.server.service.handle(b'{"v":1,"op":"snapshot"}',PeerEvidence(SID,1,True,False)))
        self.assertEqual(answer['error'],'collector_stopped')

    def test_disconnected_client_rejected_then_loop_stops_cleanly(self):
        self.server.handle=88;self.api.alive.return_value=True
        def accept(*args):self.stop.set()
        self.api.accept.side_effect=accept;self.api.peer.side_effect=PermissionError('denied')
        self.server.serve();self.assertEqual(self.server.counts['rejected'],1)
        self.api.read_frame.assert_not_called();self.api.close.assert_called_once_with(88)


class BasicHostTests(unittest.TestCase):
    def test_native_pdh_initialized_before_collection_not_merely_provider_construction(self):
        sensors=Mock();sensors.fixed_volumes.return_value=('C:\\','D:\\','E:\\')
        collector=create_basic_collector(sensors)
        sensors.open_disk_query.assert_called_once_with(('C:\\','D:\\'))
        sensors.disk_counters.assert_not_called()
        self.assertEqual(collector.state,'created')
        self.assertEqual(len(collector.cache.specs),21)
        self.assertTrue(collector.stop(1).clean)
        sensors.close_disk_query.assert_called_once()

    def test_no_authorized_volumes_never_opens_pdh(self):
        sensors=Mock();sensors.fixed_volumes.return_value=('E:\\',)
        collector=create_basic_collector(sensors);self.assertEqual(len(collector.cache.specs),5)
        self.assertTrue(collector.stop(1).clean)
        sensors.open_disk_query.assert_not_called();sensors.close_disk_query.assert_not_called()

    def test_partial_host_construction_releases_query(self):
        sensors=Mock();sensors.fixed_volumes.return_value=('C:\\',)
        with patch('monitoring.development_collector.Collector',side_effect=ValueError('fixture')):
            with self.assertRaises(ValueError):create_basic_collector(sensors)
        sensors.close_disk_query.assert_called_once()


if __name__=='__main__':unittest.main()
