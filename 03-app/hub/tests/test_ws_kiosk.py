"""Double giao thức theo ws-protocol §3; không giả lập dữ liệu nhận dạng trong DB."""
import asyncio
from types import SimpleNamespace
from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from app.main import create_app
from app.errors import ApiError
from app.recog.runtime import FrameError
from app.recog.worker import Busy


class FakeService:
    def __init__(self):
        self.device = SimpleNamespace(id=uuid4())
        self.revoked = False
        self.mode = 'state'
        self.calls = 0
        self.events = []
        self.discarded = False

    async def authenticate(self, token, version=None):
        if self.revoked:
            raise ApiError(401,'DEVICE_REVOKED','Thiết bị đã bị thu hồi.')
        if token != 'test-device-token':
            raise ApiError(401,'TOKEN_INVALID','Token không hợp lệ.')
        return self.device

    async def config(self, device):
        return {'type':'config','gate':{'id':str(uuid4()),'name':'Cửa kiểm thử','mode':'ACCESS_ONLY'},
                'research_banner':'Kiểm giao thức','max_fps':4,'frame_long_side':640,'jpeg_quality':80,'result_display_sec':3,'server_time':'2026-11-15T00:00:00+07:00'}

    async def frame(self, connection_id, token, header, data):
        self.calls += 1
        if self.mode == 'busy':
            raise Busy('Queue đầy')
        if self.mode in ('MODEL_NOT_VERIFIED','RECOGNITION_UNAVAILABLE','FRAME_DECODE_FAILED','SESSION_EXPIRED','OPERATION_INCOMPLETE'):
            raise FrameError(self.mode,'Lỗi kiểm thử')
        if self.mode == 'NO_GALLERY':
            return {'type':'state','state':'NO_GALLERY'}
        await asyncio.sleep(.05)
        if header['mode'] == 'enroll':
            if self.calls < 5:
                return {'type':'enroll_progress','accepted':self.calls,'total':5}
            return {'type':'enroll_done','profile_id':str(uuid4()),'profile_status':'PENDING_REVIEW','duplicate_warning':False}
        if self.calls == 3:
            return {'type':'result','result':'OK','door':'OPEN','employee':{'name':'Double giao thức','code':'TEST'},'attendance':{'kind':'NONE'},'message':'Kiểm giao thức'}
        return {'type':'state','state':'CHECKING','frames_in_window':self.calls}

    async def discard(self, connection_id):
        self.discarded = True


@pytest.fixture
def service_client():
    app, service = create_app(), FakeService()
    app.state.kiosk_service = service
    with TestClient(app) as client:
        yield service, client
    assert service.discarded or service.calls == 0


def auth(ws):
    ws.send_json({'type':'auth','device_token':'test-device-token','app_version':'test'})
    assert ws.receive_json()['type'] == 'config'


def frame(ws, seq, mode='recognize'):
    header = {'type':'frame','seq':seq,'mode':mode}
    if mode == 'enroll':
        header.update(enroll_session_id=str(uuid4()),employee_id=str(uuid4()))
    ws.send_json(header)
    ws.send_bytes(b'protocol-double-no-image-data')


def assert_no_face_payload(message):
    forbidden = {'image','image_url','image_path','snapshot_path','crop','png','jpeg','vector','embedding','samples'}
    if isinstance(message,dict):
        assert not forbidden.intersection(message)
        for value in message.values():
            assert_no_face_payload(value)
    elif isinstance(message,list):
        for value in message:
            assert_no_face_payload(value)


@pytest.mark.parametrize('first', [{'type':'ping'},{'type':'auth','device_token':'wrong'},{'type':'auth'}])
def test_auth_invalid_or_missing(service_client,first):
    _,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        ws.send_json(first)
        assert ws.receive_json()['code'] == 'TOKEN_INVALID'
        assert ws.receive()['code'] == 4401


def test_auth_timeout(service_client):
    _,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        assert ws.receive_json()['code'] == 'AUTH_TIMEOUT'
        assert ws.receive()['code'] == 4401


def test_stop_wait_result_and_duplicate_seq(service_client):
    service,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        auth(ws)
        for seq in (1,2,3):
            frame(ws,seq)
            response=ws.receive_json()
            assert response['seq'] == seq
            assert_no_face_payload(response)
        assert response['type'] == 'result' and response['result'] == 'OK'
        frame(ws,2)
        ws.send_json({'type':'ping'})
        assert ws.receive_json() == {'type':'pong'}
        assert service.calls == 3


def test_overlapping_frame_busy(service_client):
    service,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        auth(ws)
        frame(ws,1); frame(ws,2)
        responses=[ws.receive_json(),ws.receive_json()]
        assert any(r.get('seq') == 2 and r.get('state') == 'BUSY' for r in responses)
        assert service.calls == 1


@pytest.mark.parametrize('mode', ['busy','MODEL_NOT_VERIFIED','RECOGNITION_UNAVAILABLE','FRAME_DECODE_FAILED','SESSION_EXPIRED','OPERATION_INCOMPLETE','NO_GALLERY'])
def test_frame_error_frees_seq_and_no_gallery_creates_no_event(service_client,mode):
    service,client=service_client
    service.mode=mode
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        auth(ws); frame(ws,42)
        response=ws.receive_json()
        assert response['seq'] == 42
        assert_no_face_payload(response)
        if mode in ('busy','NO_GALLERY'):
            assert response['state'] == ('BUSY' if mode == 'busy' else mode)
        else:
            assert response['type'] == 'error' and response['code'] == mode
        assert not service.events


def test_enroll_five_frames_protocol_done_without_images(service_client):
    _,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        auth(ws)
        for seq in range(1,6):
            frame(ws,seq,'enroll')
            response=ws.receive_json()
            assert_no_face_payload(response)
            if seq < 5:
                assert response['seq'] == seq and response['accepted'] == seq
        assert response['type'] == 'enroll_done' and response['profile_status'] == 'PENDING_REVIEW'


def test_revoked_mid_connection(service_client):
    service,client=service_client
    with client.websocket_connect('/api/v1/ws/kiosk') as ws:
        auth(ws)
        service.revoked=True
        ws.send_json({'type':'ping'})
        assert ws.receive_json()['code'] == 'DEVICE_REVOKED'
        assert ws.receive()['code'] == 4401
