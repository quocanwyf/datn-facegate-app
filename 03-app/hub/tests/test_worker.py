import asyncio
from concurrent.futures import CancelledError
import threading
import time
import httpx
from fastapi import FastAPI
import pytest
from app.recog.worker import InferenceWorker, Busy


@pytest.mark.asyncio
async def test_busy_queue_and_event_loop_latency():
    started, release = threading.Event(), threading.Event()
    owner_threads = []
    def busy(payload):
        owner_threads.append(threading.get_ident())
        started.set()
        assert release.wait(10)
        return payload
    worker = InferenceWorker({'infer': busy})
    try:
        await asyncio.wrap_future(worker.ready)
        first = worker.submit('infer', 'first', device_id='tablet')
        assert await asyncio.to_thread(started.wait, 5)
        second = worker.submit('infer', 'second', device_id='tablet')
        third = worker.submit('infer', 'third', device_id='tablet')
        with pytest.raises(Busy):
            await asyncio.wrap_future(worker.submit('infer', 'overflow', device_id='tablet'))
        app = FastAPI()
        @app.get('/ping')
        async def ping():
            return {'ok': True}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            before = time.perf_counter()
            response = await client.get('/ping')
            elapsed = (time.perf_counter() - before) * 1000
        assert response.status_code == 200
        print(f'endpoint_latency_ms={elapsed:.6f}; worker_busy=true')
        assert elapsed < 50
        release.set()
        assert await asyncio.wrap_future(first) == 'first'
        assert await asyncio.wrap_future(second) == 'second'
        assert await asyncio.wrap_future(third) == 'third'
        assert len(set(owner_threads)) == 1 and owner_threads[0] != threading.get_ident()
    finally:
        release.set()
        await asyncio.to_thread(worker.close)


def test_initializer_error_and_shutdown():
    def broken():
        raise ValueError('Model chưa xác minh')
    worker = InferenceWorker(initializer=broken)
    try:
        with pytest.raises(ValueError):
            worker.submit('infer', None).result(timeout=3)
    finally:
        worker.close()
    with pytest.raises(RuntimeError):
        worker.submit('infer', None).result()
