"""Sinh seed.sql cho bản DEMO (chạy lại được; UUID cố định qua uuid5, mật khẩu/PIN băm argon2id).

    python gen_seed.py > seed.sql

Liêm chính: KHÔNG seed sự kiện nhận dạng, ngày công hay khuôn mặt — các dữ liệu đó chỉ sinh ra khi chạy thật.
Số liệu mô hình/ngưỡng lấy nguyên từ log (đọc ngày 14/11/2026):
  - 02-thuc-nghiem/eval-test/manifest/manifest_24.json (sha256, epoch)
  - 02-thuc-nghiem/eval-test/tools/windows/logs/strip_map_ban_sao.json (sha bản trích)
  - 02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json (meta.t_eq30, thr_DIR@0.01)
  - 02-thuc-nghiem/results/<run>/phien-1/<run>/val.jsonl (thr@far=1e-05 tại epoch best)
Ở M0, gen_thresholds.py đọc lại log và PHẢI ra đúng các giá trị này.
"""
import json
import uuid

from argon2 import PasswordHasher

NS = uuid.UUID("6f1c2a52-6e0b-4d0f-9a51-0d7a1b8c0001")
ph = PasswordHasher()  # argon2id, tham số mặc định của argon2-cffi
DEMO_PASSWORD = "Demo@123"
DEMO_PIN = "2468"


def U(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


out = []
w = out.append
w("-- SEED DỮ LIỆU DEMO — sinh bởi gen_seed.py. Không sửa tay.")
w(f"-- Mật khẩu mọi tài khoản demo: {DEMO_PASSWORD} | PIN Kiosk (HR, Chủ DN): {DEMO_PIN}")
w("-- KHÔNG có sự kiện nhận dạng / ngày công / khuôn mặt: chỉ sinh khi chạy thật (không giả lập kết quả nhận dạng).")
w("BEGIN;")

# ---------- công ty ----------
CO = U("company")
settings = {
    "window_size": 5, "match_min": 3, "unknown_min": 4, "spoof_min": 3,
    "lost_face_sec": 1.0, "iou_reset": 0.3,
    "cooldown_employee_sec": 60, "cooldown_alert_sec": 15, "result_display_sec": 3,
    "max_fps": 4, "frame_long_side": 640, "jpeg_quality": 80,
    "min_face_px": 80, "max_abs_yaw_ratio": 0.35,
    "anti_spoof_enabled": False, "liveness_threshold": None,  # bật ở M7 sau khi hiệu chỉnh L
    "attendance_window_before_h": 3, "attendance_window_after_h": 4,
    "min_checkout_after_checkin_min": 30, "forgot_out_before_end_h": 2,
    "research_banner": "Bản trình diễn nghiên cứu – không dùng thương mại",
}
w(f"INSERT INTO company(id,name,timezone,settings) VALUES ({q(CO)},'Công ty Demo FaceGate','Asia/Ho_Chi_Minh',{q(json.dumps(settings, ensure_ascii=False))}::jsonb);")

# ---------- phòng ban ----------
DEPTS = ["Ban Giám đốc", "Hành chính – Nhân sự", "Kỹ thuật", "Kinh doanh", "Lễ tân – Bảo vệ"]
for d in DEPTS:
    w(f"INSERT INTO department(id,company_id,name) VALUES ({q(U('dept:'+d))},{q(CO)},{q(d)});")

# ---------- nhân viên (tên hư cấu) ----------
EMPS = [
    ("NV001", "Trần Minh Khoa", "Ban Giám đốc"),
    ("NV002", "Nguyễn Thị Thu Hà", "Hành chính – Nhân sự"),
    ("NV003", "Lê Hoàng Phúc", "Hành chính – Nhân sự"),
    ("NV004", "Phạm Ngọc Anh", "Hành chính – Nhân sự"),
    ("NV005", "Đỗ Quang Huy", "Kỹ thuật"),
    ("NV006", "Võ Thanh Tùng", "Kỹ thuật"),
    ("NV007", "Bùi Gia Bảo", "Kỹ thuật"),
    ("NV008", "Hồ Minh Thư", "Kỹ thuật"),
    ("NV009", "Ngô Đức Long", "Kỹ thuật"),
    ("NV010", "Dương Khánh Linh", "Kỹ thuật"),
    ("NV011", "Huỳnh Tấn Phát", "Kỹ thuật"),
    ("NV012", "Lý Bảo Trân", "Kỹ thuật"),
    ("NV013", "Phan Văn Đạt", "Kinh doanh"),
    ("NV014", "Trịnh Mỹ Duyên", "Kinh doanh"),
    ("NV015", "Mai Quốc Việt", "Kinh doanh"),
    ("NV016", "Tạ Hồng Nhung", "Kinh doanh"),
    ("NV017", "Châu Thành Nam", "Kinh doanh"),
    ("NV018", "Lâm Thảo Vy", "Kinh doanh"),
    ("NV019", "Đinh Công Hậu", "Kinh doanh"),
    ("NV020", "Kiều Thị Mai", "Lễ tân – Bảo vệ"),
    ("NV021", "Vương Đình Lộc", "Lễ tân – Bảo vệ"),
    ("NV022", "Cao Nhật Minh", "Kinh doanh"),
    ("NV023", "Hà Phương Uyên", "Kỹ thuật"),
    ("NV024", "Lưu Trọng Nghĩa", "Kỹ thuật"),
]
SPECIAL_STATUS = {"NV019": "SUSPENDED"}      # minh hoạ DENIED_INACTIVE
SPECIAL_METHOD = {"NV022": "MANUAL"}         # minh hoạ người không đồng ý → chấm công hộ
for code, name, dept in EMPS:
    w("INSERT INTO employee(id,company_id,department_id,code,full_name,email,status,attendance_method,joined_at) VALUES "
      f"({q(U('emp:'+code))},{q(CO)},{q(U('dept:'+dept))},{q(code)},{q(name)},{q(code.lower()+'@demo.local')},"
      f"{q(SPECIAL_STATUS.get(code,'ACTIVE'))},{q(SPECIAL_METHOD.get(code,'FACE'))},'2026-01-05');")

# ---------- tài khoản & vai trò ----------
ROLES = {  # code -> [(role, scope_dept)]
    "NV001": [("OWNER", None)],
    "NV002": [("HR", None)],
    "NV005": [("MANAGER", "Kỹ thuật")],
    "NV013": [("MANAGER", "Kinh doanh")],
    "NV020": [("SECURITY", None)],
    "NV021": [("SECURITY", None)],
}
PIN_USERS = {"NV001", "NV002"}
for code, name, dept in EMPS:
    uid = U("user:" + code)
    pin = q(ph.hash(DEMO_PIN)) if code in PIN_USERS else "NULL"
    w("INSERT INTO user_account(id,company_id,email,password_hash,employee_id,must_change_password,kiosk_pin_hash) VALUES "
      f"({q(uid)},{q(CO)},{q(code.lower()+'@demo.local')},{q(ph.hash(DEMO_PASSWORD))},{q(U('emp:'+code))},false,{pin});")
    for role, scope in [("EMPLOYEE", None)] + ROLES.get(code, []):
        w(f"INSERT INTO user_role(user_id,role,scope_department_id) VALUES ({q(uid)},{q(role)},{q(U('dept:'+scope)) if scope else 'NULL'});")

# ---------- mô hình & ngưỡng (từ log) ----------
MODELS = [
    dict(code="V1_S3", name="UniFace + V1 (R18, seed 3, best.pt)",
         manifest_id="r18_uniface_v1_lam0.6_m0.45_s3_e28:best",
         source_path="02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/checkpoints/best.pt",
         source_sha256="120489621accefd7e78da9bd83fe3c6360ad94877e8ac4b9cdfa1038ec8eef88",
         stripped_sha256="b00612f58a5a3d6be9055ce6ff073fdafd3d8071c85ebdaa5462b198f2b1a065",
         epoch=18, t_bs=0.3736472427845001,
         thr_val=0.4232754409313202, thr_strict=0.4657080352306366,
         val_ref="02-thuc-nghiem/results/V1-s3-Hy/phien-1/r18_uniface_v1_lam0.6_m0.45_s3_e28/val.jsonl: results[\"thr@far=1e-05\"] @ epoch 18"),
]
BLUFR = "02-thuc-nghiem/results/2026-11-12_test-blufr-lfw/eval_test/ket_qua_blufr_lfw.json"
for m in MODELS:
    mid = U("model:" + m["code"])
    w("INSERT INTO recognition_model(id,code,name,backbone,manifest_id,source_path,source_sha256,stripped_sha256,epoch,t_bs,alignment_version) VALUES "
      f"({q(mid)},{q(m['code'])},{q(m['name'])},'r18',{q(m['manifest_id'])},{q(m['source_path'])},"
      f"{q(m['source_sha256'])},{q(m['stripped_sha256'])},{m['epoch']},{m['t_bs']!r},"
      "'yunet_2023mar+norm_crop(arcface_dst)+largest_face');")
    w("INSERT INTO threshold_profile(model_id,level,cos_threshold,label,source_ref) VALUES "
      f"({q(mid)},'DEFAULT_VAL',{m['thr_val']!r},'Chọn trên validation (FAR 1e-5)',{q(m['val_ref'])});")
    w("INSERT INTO threshold_profile(model_id,level,cos_threshold,label,source_ref) VALUES "
      f"({q(mid)},'STRICT_TEST',{m['thr_strict']!r},'Hiệu chỉnh trên tập test BLUFR sau khi đã báo cáo kết quả',"
      f"{q(BLUFR + ': mean(ket_qua[' + chr(34) + m['manifest_id'] + chr(34) + '].blufr.per_trial[*][' + chr(34) + 'thr_DIR@0.01' + chr(34) + ']), 10 trial')});")

# ---------- cửa ----------
G_MAIN, G_SRV = U("gate:main"), U("gate:server")
w(f"INSERT INTO gate(id,company_id,name,mode,default_policy,threshold_level) VALUES ({q(G_MAIN)},{q(CO)},'Cửa chính','ATTENDANCE_ACCESS','ALLOW_ALL_ACTIVE','DEFAULT_VAL');")
w(f"INSERT INTO gate(id,company_id,name,mode,default_policy,threshold_level) VALUES ({q(G_SRV)},{q(CO)},'Phòng máy chủ','ACCESS_ONLY','DEPARTMENTS_ONLY','STRICT_TEST');")
for d in ["Kỹ thuật", "Ban Giám đốc"]:
    w(f"INSERT INTO gate_allowed_department(gate_id,department_id) VALUES ({q(G_SRV)},{q(U('dept:'+d))});")

# ---------- ca, phân ca, ngày lễ ----------
S_HC, S_LT = U("shift:hc"), U("shift:lt")
w(f"INSERT INTO shift(id,company_id,name,start_time,end_time,break_start,break_end,grace_in_min,grace_out_min) VALUES ({q(S_HC)},{q(CO)},'Hành chính','08:30','17:30','12:00','13:00',10,10);")
w(f"INSERT INTO shift(id,company_id,name,start_time,end_time,break_start,break_end,grace_in_min,grace_out_min) VALUES ({q(S_LT)},{q(CO)},'Lễ tân – Ca sáng','07:00','15:00','11:00','11:30',5,5);")
for d in ["Ban Giám đốc", "Hành chính – Nhân sự", "Kỹ thuật", "Kinh doanh"]:
    for wd in range(1, 6):
        w(f"INSERT INTO shift_assignment(company_id,shift_id,department_id,weekday,effective_from) VALUES ({q(CO)},{q(S_HC)},{q(U('dept:'+d))},{wd},'2026-11-01');")
for wd in range(1, 7):
    w(f"INSERT INTO shift_assignment(company_id,shift_id,department_id,weekday,effective_from) VALUES ({q(CO)},{q(S_LT)},{q(U('dept:Lễ tân – Bảo vệ'))},{wd},'2026-11-01');")
w(f"INSERT INTO holiday(company_id,date,name) VALUES ({q(CO)},'2027-01-01','Tết Dương lịch');")

w("COMMIT;")
print("\n".join(out))
