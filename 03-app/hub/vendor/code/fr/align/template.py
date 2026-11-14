"""Template 5 điểm ArcFace (112×112) và phép biến đổi similarity — CHÉP NGUYÊN từ insightface.

Nguồn: deepinsight/insightface ``python-package/insightface/utils/face_align.py`` (master c6c3af7b, 05/11/2026),
bản gốc lưu ở ``third_party/insightface_ijb/face_align.py``. Cùng toạ độ với ``Embedding.src`` trong
``recognition/arcface_torch/eval_ijbc.py`` (template 96×112 + 8 px theo trục x) — tức là đúng kiểu căn chỉnh
của dữ liệu train ``faces_webface_112x112`` (CASIA bản insightface) và các file .bin.

Thứ tự 5 điểm (theo ảnh, nhìn từ phía người xem):
  0 = mắt bên TRÁI ảnh (mắt phải của người), 1 = mắt bên PHẢI ảnh, 2 = đầu mũi,
  3 = khoé miệng bên trái ảnh, 4 = khoé miệng bên phải ảnh.
Sửa so với bản gốc: bỏ tham số ``mode`` không dùng; ``norm_crop`` trả thêm ma trận M (giống norm_crop2).
"""
import cv2
import numpy as np
from skimage import transform as trans

arcface_dst = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
     [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32)
ARCFACE_DST = arcface_dst


def estimate_norm(lmk, image_size=112):
    assert lmk.shape == (5, 2)
    assert image_size % 112 == 0 or image_size % 128 == 0
    if image_size % 112 == 0:
        ratio = float(image_size) / 112.0
        diff_x = 0
    else:
        ratio = float(image_size) / 128.0
        diff_x = 8.0 * ratio
    dst = arcface_dst * ratio
    dst[:, 0] += diff_x
    tform = trans.SimilarityTransform()
    tform.estimate(lmk, dst)
    M = tform.params[0:2, :]
    return M


def norm_crop(img, landmark, image_size=112):
    M = estimate_norm(np.asarray(landmark, dtype=np.float32), image_size)
    warped = cv2.warpAffine(img, M, (image_size, image_size), borderValue=0.0)
    return warped, M
