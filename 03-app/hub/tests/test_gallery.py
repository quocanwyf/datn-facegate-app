import os
import uuid
import pytest
from sqlalchemy import create_engine
import torch
from app.recog.gallery import Gallery, NoGallery, RecognitionUnavailable, gallery_query
from app.config import get_settings


def test_failed_reload_disables_recognition_and_empty_is_distinct():
    gallery = Gallery(torch.device('cpu'))
    with pytest.raises(RecognitionUnavailable):
        gallery.top1(None)
    assert gallery.reload(lambda: []) == 0
    assert gallery.ready and gallery.size == 0
    with pytest.raises(NoGallery):
        gallery.top1(None)
    def failed():
        raise OSError('DB không khả dụng')
    with pytest.raises(RecognitionUnavailable):
        gallery.reload(failed)
    assert not gallery.ready
    with pytest.raises(RecognitionUnavailable):
        gallery.top1(None)


def test_gallery_loads_real_seed_database_without_fabricated_templates():
    url = os.environ.get('T03_TEST_DATABASE_URL', get_settings().database_url.get_secret_value())
    engine = create_engine(url.replace('postgresql+asyncpg:', 'postgresql+psycopg:'), hide_parameters=True)
    gallery = Gallery(torch.device('cpu'))
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            model = connection.scalar(text('SELECT id FROM recognition_model WHERE is_active'))
            company = connection.scalar(text('SELECT id FROM company'))
            count = gallery.reload(lambda: connection.execute(gallery_query(model, company)).all())
        assert count == 0 and gallery.ready
        print(f'gallery_real_db_rows={count}; ready={gallery.ready}; no_demo_templates_created=true')
    finally:
        engine.dispose()
