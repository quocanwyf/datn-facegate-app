"""Chỉ thao tác đường dẫn tương đối bên trong HUB_DATA_DIR."""
from pathlib import Path
from app.config import get_settings


def data_path(relative):
    root = get_settings().hub_data_dir.resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError('Đường dẫn dữ liệu không hợp lệ')
    return target


def write_private(relative, content):
    target = data_path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(content)


def delete_private(paths):
    errors = []
    for relative in paths:
        try:
            target = data_path(relative)
            target.unlink(missing_ok=True)
            # Chỉ xóa thư mục cha nếu rỗng, không xóa đệ quy.
            try:
                target.parent.rmdir()
            except OSError:
                pass
        except (OSError, ValueError):
            errors.append(relative)
    if errors:
        raise OSError('Chưa xóa xong các file sinh trắc')
