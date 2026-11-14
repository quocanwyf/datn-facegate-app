"""Nạp nguyên seed.sql; chỉ dùng trên DB demo mới migrate."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from app.config import ROOT, get_settings


def main():
    url = get_settings().database_url.get_secret_value().replace('postgresql+asyncpg:', 'postgresql:')
    with psycopg.connect(url) as connection:
        connection.execute((ROOT / '03-app/db/seed.sql').read_text(encoding='utf-8'))
    print('Đã nạp seed.sql; không tạo sự kiện, ngày công hay khuôn mặt.')


if __name__ == '__main__':
    main()
