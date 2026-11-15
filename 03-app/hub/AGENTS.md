# AGENTS.md — Hub (FastAPI + PyTorch + PostgreSQL)

Đọc thêm skill `hub-rules`, `api-contract`, `kiosk-ws-protocol`, `cham-cong-vn` (`.agents/skills/`).

## Stack
Python 3.11+ · FastAPI + Uvicorn · Pydantic v2 · SQLAlchemy 2 (async, asyncpg) + Alembic · PostgreSQL 16 · PyTorch (CPU khi dev, CUDA + fp16 trên laptop An) · OpenCV (`cv2.FaceDetectorYN`) · APScheduler · argon2-cffi · PyJWT · openpyxl · pytest + httpx.

## Cấu trúc (đặc tả §2.2)
```
hub/
  app/
    main.py            # tạo app, startup: cổng kiểm mô hình → nạp gallery → khởi động worker + scheduler
    config.py          # pydantic-settings, đọc .env
    api/               # router theo tag của openapi.yaml; ws_kiosk.py, ws_monitor.py
    auth/              # JWT, RBAC + phạm vi phòng ban, device token, PIN
    recog/             # model_loader.py, detector.py, liveness.py, embedder.py, gallery.py, decision.py, worker.py
    biz/               # attendance.py (recompute_day, finalize_day), access.py, requests.py, enrollment.py, face_data.py, export_excel.py
    db/                # models.py, session.py
    jobs/              # scheduler.py
  alembic/
  vendor/              # CHỈ ĐỌC — bản sao code thực nghiệm + MANIFEST.sha256
  scripts/             # check_env.py, parity_*.py, gen_thresholds.py, kiosk_sim.py
  tests/
```

## Lệnh (PowerShell, trong `03-app/hub`)
```powershell
py -3.13 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt            # torch CPU khi dev
copy ..\..\.env.example ..\..\.env         # rồi sửa DATABASE_URL
alembic upgrade head; python scripts\seed.py   # nạp 03-app/db/seed.sql
uvicorn app.main:app --host 0.0.0.0 --port 8000
pytest -q
```

## Luật bắt buộc
1. **Không chạy PyTorch trong event loop.** Mọi suy luận (YuNet, MiniFASNet, backbone) đi qua `recog/worker.py`: một thread worker + hàng đợi; endpoint/WS chỉ `await` future.
2. **Trích feature chỉ bằng `evaltest.features.extract_features`** (vendor), input `torch.uint8 (N,3,112,112) RGB`. `norm_crop` trả `(warped_bgr, M)` → phải unpack và `cv2.cvtColor(BGR2RGB)` → `transpose(2,0,1)`. Không tự viết lại tiền xử lý.
3. **Nạp mô hình qua cổng 4 bước** (đặc tả §4.1): sha256 file = manifest → strip_map nối tới `meta.sha256` → `load_backbone(..., row=<dòng manifest>, expected_sha=…)` → `t_eq30` khớp. Sai → dừng phần nhận dạng (log rõ lý do), giữ API health chẩn đoán degraded/model_verified=false; không mở cửa/ghi công bằng mặt.
4. **`DATN_CODE_DIR` = `hub/vendor/code`** phải được đặt trước `import evaltest.features`.
5. Ngưỡng lấy từ bảng `threshold_profile` / `gate.custom_threshold`, **không hard-code** 0,4233 trong code.
6. `recognition_event` **chỉ INSERT** (DB có trigger chặn). Xử lý cảnh báo ghi vào `event_handling`.
7. `attendance_day` chỉ thay đổi qua `recompute_day()` / `finalize_day()` / sửa tay có lý do — không cập nhật rải rác.
8. Kiểm quyền ở server theo bảng quyền đặc tả §6 (vai trò + phạm vi phòng ban). Người duyệt ≠ người gửi; không sửa ngày công của chính mình; chấm hộ: người chấm ≠ NV và NV phải `MANUAL`.
9. Model SQLAlchemy + Alembic phải **tương đương `03-app/db/schema.sql`** (gồm CHECK, EXCLUDE, trigger, partial unique). Kiểm bằng `03-app/db/test_constraints.sql` (44/44) trên DB tạo bởi Alembic.
10. Lỗi trả đúng dạng `Error` của openapi (`code` máy đọc + `message` tiếng Việt).
11. Không lưu khung hình đầy đủ; chỉ lưu ảnh mẫu đã căn chỉnh (đăng ký) và crop của UNKNOWN/SPOOF.
