-- KIỂM THỬ RÀNG BUỘC CSDL — chạy SAU schema.sql + seed.sql trên DB thử (không phải DB thật).
--   psql -v ON_ERROR_STOP=1 -d <db_thu> -f test_constraints.sql
-- Mỗi ca: "PHẢI LỖI" = ràng buộc phải chặn; "PHẢI ĐƯỢC" = thao tác hợp lệ phải chạy. Kết thúc bằng ROLLBACK.
BEGIN;
CREATE TEMP TABLE kq(ca text, mong_doi text, ket_qua text);

CREATE OR REPLACE FUNCTION pg_temp.thu(ca text, sql text, phai_loi boolean) RETURNS void AS $$
BEGIN
  BEGIN
    EXECUTE sql;
    INSERT INTO kq VALUES (ca, CASE WHEN phai_loi THEN 'PHẢI LỖI' ELSE 'PHẢI ĐƯỢC' END,
                           CASE WHEN phai_loi THEN 'SAI (không bị chặn)' ELSE 'ĐẠT' END);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO kq VALUES (ca, CASE WHEN phai_loi THEN 'PHẢI LỖI' ELSE 'PHẢI ĐƯỢC' END,
                           CASE WHEN phai_loi THEN 'ĐẠT' ELSE 'SAI: ' || SQLERRM END);
  END;
END $$ LANGUAGE plpgsql;

-- dữ liệu phụ cho test
INSERT INTO device(id, company_id, gate_id, name)
SELECT '11111111-1111-1111-1111-111111111111', c.id, g.id, 'Kiosk test' FROM company c, gate g WHERE g.name = 'Cửa chính';
CREATE TEMP VIEW v AS SELECT
  (SELECT id FROM company) co,
  (SELECT id FROM gate WHERE name='Cửa chính') g,
  '11111111-1111-1111-1111-111111111111'::uuid dv,
  (SELECT id FROM recognition_model WHERE code='V1_S3') m,
  (SELECT id FROM employee WHERE code='NV006') e6,
  (SELECT id FROM user_account WHERE email='nv006@demo.local') u6,
  (SELECT id FROM user_account WHERE email='nv005@demo.local') u5,
  (SELECT id FROM user_account WHERE email='nv020@demo.local') u20,
  (SELECT id FROM department WHERE name='Kỹ thuật') dkt,
  (SELECT id FROM shift WHERE name='Hành chính') shc;

-- ---------- recognition_event ----------
SELECT pg_temp.thu('E1 MATCH hợp lệ', format($q$INSERT INTO recognition_event(id,company_id,gate_id,device_id,occurred_at,result,employee_id,model_id,top1_score,threshold_used,threshold_level,n_frames,door_action)
  VALUES ('22222222-2222-2222-2222-222222222222',%L,%L,%L,now(),'MATCH',%L,%L,0.61,0.4233,'DEFAULT_VAL',3,'OPEN')$q$, co,g,dv,e6,m), false) FROM v;
SELECT pg_temp.thu('E2 MATCH có ảnh crop', format($q$INSERT INTO recognition_event(company_id,gate_id,device_id,occurred_at,result,employee_id,model_id,top1_score,threshold_used,n_frames,door_action,snapshot_path)
  VALUES (%L,%L,%L,now(),'MATCH',%L,%L,0.61,0.4233,3,'OPEN','x.jpg')$q$, co,g,dv,e6,m), true) FROM v;
SELECT pg_temp.thu('E3 MATCH không mở cửa', format($q$INSERT INTO recognition_event(company_id,gate_id,device_id,occurred_at,result,employee_id,model_id,top1_score,threshold_used,n_frames,door_action)
  VALUES (%L,%L,%L,now(),'MATCH',%L,%L,0.61,0.4233,3,'NONE')$q$, co,g,dv,e6,m), true) FROM v;
SELECT pg_temp.thu('E4 UNKNOWN gắn nhân viên', format($q$INSERT INTO recognition_event(company_id,gate_id,device_id,occurred_at,result,employee_id,model_id,n_frames)
  VALUES (%L,%L,%L,now(),'UNKNOWN',%L,%L,5)$q$, co,g,dv,e6,m), true) FROM v;
SELECT pg_temp.thu('E5 UNKNOWN hợp lệ (có crop)', format($q$INSERT INTO recognition_event(id,company_id,gate_id,device_id,occurred_at,result,model_id,top1_score,threshold_used,n_frames,snapshot_path)
  VALUES ('33333333-3333-3333-3333-333333333333',%L,%L,%L,now(),'UNKNOWN',%L,0.2,0.4233,5,'s/u.jpg')$q$, co,g,dv,m), false) FROM v;
SELECT pg_temp.thu('E6 MATCH thiếu mô hình', format($q$INSERT INTO recognition_event(company_id,gate_id,device_id,occurred_at,result,employee_id,top1_score,threshold_used,n_frames,door_action)
  VALUES (%L,%L,%L,now(),'MATCH',%L,0.61,0.4233,3,'OPEN')$q$, co,g,dv,e6), true) FROM v;
SELECT pg_temp.thu('E7 Chấm hộ thiếu lý do', format($q$INSERT INTO recognition_event(company_id,gate_id,occurred_at,result,employee_id,performed_by_user_id)
  VALUES (%L,%L,now(),'MANUAL_ATTENDANCE',%L,%L)$q$, co,g,e6,u20), true) FROM v;
SELECT pg_temp.thu('E8 Chấm hộ hợp lệ', format($q$INSERT INTO recognition_event(company_id,gate_id,occurred_at,result,employee_id,performed_by_user_id,reason)
  VALUES (%L,%L,now(),'MANUAL_ATTENDANCE',%L,%L,'NV không đăng ký khuôn mặt')$q$, co,g,e6,u20), false) FROM v;
SELECT pg_temp.thu('E9 Sửa điểm của event', $q$UPDATE recognition_event SET top1_score = 0.9 WHERE id='22222222-2222-2222-2222-222222222222'$q$, true);
SELECT pg_temp.thu('E10 Xoá event', $q$DELETE FROM recognition_event WHERE id='22222222-2222-2222-2222-222222222222'$q$, true);
SELECT pg_temp.thu('E11 Xoá ảnh crop (snapshot_path → NULL)', $q$UPDATE recognition_event SET snapshot_path = NULL WHERE id='33333333-3333-3333-3333-333333333333'$q$, false);
SELECT pg_temp.thu('E12 Đổi snapshot_path sang file khác', $q$UPDATE recognition_event SET snapshot_path = 'khac.jpg' WHERE id='22222222-2222-2222-2222-222222222222'$q$, true);

-- ---------- event_handling ----------
SELECT pg_temp.thu('H1 Xử lý cảnh báo trên event MATCH', format($q$INSERT INTO event_handling(event_id,status,handled_by_user_id) VALUES ('22222222-2222-2222-2222-222222222222','RESOLVED',%L)$q$, u20), true) FROM v;
SELECT pg_temp.thu('H2 IS_EMPLOYEE không gắn NV', format($q$INSERT INTO event_handling(event_id,status,handled_by_user_id) VALUES ('33333333-3333-3333-3333-333333333333','IS_EMPLOYEE',%L)$q$, u20), true) FROM v;
SELECT pg_temp.thu('H3 Xử lý cảnh báo UNKNOWN hợp lệ', format($q$INSERT INTO event_handling(event_id,status,handled_by_user_id) VALUES ('33333333-3333-3333-3333-333333333333','FALSE_ALARM',%L)$q$, u20), false) FROM v;

-- ---------- phân ca ----------
SELECT pg_temp.thu('S1 Chồng phân ca phòng ban cùng thứ', format($q$INSERT INTO shift_assignment(company_id,shift_id,department_id,weekday,effective_from) VALUES (%L,%L,%L,1,'2026-12-01')$q$, co,shc,dkt), true) FROM v;
SELECT pg_temp.thu('S2 Phân ca cá nhân (không chồng)', format($q$INSERT INTO shift_assignment(company_id,shift_id,employee_id,weekday,effective_from,effective_to) VALUES (%L,%L,%L,6,'2026-12-01','2026-12-31')$q$, co,shc,e6), false) FROM v;
SELECT pg_temp.thu('S3 Chồng phân ca cá nhân', format($q$INSERT INTO shift_assignment(company_id,shift_id,employee_id,weekday,effective_from) VALUES (%L,%L,%L,6,'2026-12-15')$q$, co,shc,e6), true) FROM v;
SELECT pg_temp.thu('S4 Phân ca vừa NV vừa phòng ban', format($q$INSERT INTO shift_assignment(company_id,shift_id,employee_id,department_id,weekday,effective_from) VALUES (%L,%L,%L,%L,7,'2026-12-01')$q$, co,shc,e6,dkt), true) FROM v;
SELECT pg_temp.thu('S5 Ca dài hơn 17 giờ', format($q$INSERT INTO shift(company_id,name,start_time,end_time) VALUES (%L,'Ca dài','05:00','23:00')$q$, co), true) FROM v;
SELECT pg_temp.thu('S6 Ca qua nửa đêm', format($q$INSERT INTO shift(company_id,name,start_time,end_time) VALUES (%L,'Ca đêm','22:00','06:00')$q$, co), true) FROM v;

-- ---------- giải trình ----------
SELECT pg_temp.thu('R1 Người duyệt = người gửi', format($q$INSERT INTO attendance_request(company_id,employee_id,requested_by_user_id,work_date,type,requested_out,reason,status,reviewer_user_id,reviewed_at)
  VALUES (%L,%L,%L,'2026-11-16','FORGOT_OUT','2026-11-16 10:30+00','quên quét','APPROVED',%L,now())$q$, co,e6,u6,u6), true) FROM v;
SELECT pg_temp.thu('R2 Giải trình hợp lệ (PENDING)', format($q$INSERT INTO attendance_request(company_id,employee_id,requested_by_user_id,work_date,type,requested_out,reason)
  VALUES (%L,%L,%L,'2026-11-16','FORGOT_OUT','2026-11-16 10:30+00','quên quét')$q$, co,e6,u6), false) FROM v;
SELECT pg_temp.thu('R3 Hai giải trình chờ cùng ngày', format($q$INSERT INTO attendance_request(company_id,employee_id,requested_by_user_id,work_date,type,reason)
  VALUES (%L,%L,%L,'2026-11-16','OTHER','lý do khác')$q$, co,e6,u6), true) FROM v;
SELECT pg_temp.thu('R4 FORGOT_IN thiếu giờ vào', format($q$INSERT INTO attendance_request(company_id,employee_id,requested_by_user_id,work_date,type,reason)
  VALUES (%L,%L,%L,'2026-11-17','FORGOT_IN','quên')$q$, co,e6,u6), true) FROM v;
SELECT pg_temp.thu('R5 APPROVED thiếu người duyệt', format($q$INSERT INTO attendance_request(company_id,employee_id,requested_by_user_id,work_date,type,reason,status)
  VALUES (%L,%L,%L,'2026-11-18','OTHER','x','APPROVED')$q$, co,e6,u6), true) FROM v;

-- ---------- ngày công ----------
SELECT pg_temp.thu('A1 NORMAL thiếu giờ ra', format($q$INSERT INTO attendance_day(company_id,employee_id,work_date,check_in_at,status) VALUES (%L,%L,'2026-11-16','2026-11-16 01:25+00','NORMAL')$q$, co,e6), true) FROM v;
SELECT pg_temp.thu('A2 Giờ ra trước giờ vào', format($q$INSERT INTO attendance_day(company_id,employee_id,work_date,check_in_at,check_out_at,status) VALUES (%L,%L,'2026-11-16','2026-11-16 10:00+00','2026-11-16 01:00+00','NORMAL')$q$, co,e6), true) FROM v;
SELECT pg_temp.thu('A3 Sửa tay thiếu lý do', format($q$INSERT INTO attendance_day(company_id,employee_id,work_date,status,source) VALUES (%L,%L,'2026-11-17','LEAVE','MANUAL')$q$, co,e6), true) FROM v;
SELECT pg_temp.thu('A4 Ngày công hợp lệ', format($q$INSERT INTO attendance_day(company_id,employee_id,work_date,check_in_at,check_out_at,status,late_min) VALUES (%L,%L,'2026-11-16','2026-11-16 01:45+00','2026-11-16 10:35+00','LATE',5)$q$, co,e6), false) FROM v;
SELECT pg_temp.thu('A5 Trùng ngày công cùng NV', format($q$INSERT INTO attendance_day(company_id,employee_id,work_date,status) VALUES (%L,%L,'2026-11-16','ABSENT')$q$, co,e6), true) FROM v;

-- ---------- vai trò, khuôn mặt, mô hình, cửa ----------
SELECT pg_temp.thu('U1 MANAGER không có phạm vi', format($q$INSERT INTO user_role(user_id,role) VALUES (%L,'MANAGER')$q$, u6), true) FROM v;
SELECT pg_temp.thu('U2 Vai trò trùng lặp', format($q$INSERT INTO user_role(user_id,role) VALUES (%L,'EMPLOYEE')$q$, u6), true) FROM v;
SELECT pg_temp.thu('U3 Email trùng (khác hoa thường)', format($q$INSERT INTO user_account(company_id,email,password_hash) VALUES (%L,'NV006@DEMO.LOCAL','x')$q$, co), true) FROM v;
SELECT pg_temp.thu('F1 Hồ sơ PENDING hợp lệ', format($q$INSERT INTO face_profile(id,company_id,employee_id,enrolled_by_user_id) VALUES ('44444444-4444-4444-4444-444444444444',%L,%L,%L)$q$, co,e6,u5), false) FROM v;
SELECT pg_temp.thu('F2 Hai hồ sơ PENDING cùng NV', format($q$INSERT INTO face_profile(company_id,employee_id,enrolled_by_user_id) VALUES (%L,%L,%L)$q$, co,e6,u5), true) FROM v;
SELECT pg_temp.thu('F3 ACTIVE mà chưa ai duyệt', $q$UPDATE face_profile SET status='ACTIVE' WHERE id='44444444-4444-4444-4444-444444444444'$q$, true);
SELECT pg_temp.thu('F4 Embedding 511 chiều', format($q$INSERT INTO face_sample(id,profile_id,image_path,det_score,yaw_ratio) VALUES ('55555555-5555-5555-5555-555555555555','44444444-4444-4444-4444-444444444444','f.png',0.9,0.05);
  INSERT INTO face_embedding(sample_id,model_id,vector) SELECT '55555555-5555-5555-5555-555555555555',%L,array_fill(0.01::real, ARRAY[511])$q$, m), true) FROM v;
SELECT pg_temp.thu('F5 Embedding 512 chiều hợp lệ', format($q$INSERT INTO face_sample(id,profile_id,image_path,det_score,yaw_ratio) VALUES ('66666666-6666-6666-6666-666666666666','44444444-4444-4444-4444-444444444444','f.png',0.9,0.05);
  INSERT INTO face_embedding(sample_id,model_id,vector) SELECT '66666666-6666-6666-6666-666666666666',%L,array_fill(0.01::real, ARRAY[512])$q$, m), false) FROM v;
SELECT pg_temp.thu('F6 Xoá hồ sơ → xoá dây chuyền mẫu + embedding', $q$DELETE FROM face_profile WHERE id='44444444-4444-4444-4444-444444444444';
  DO $d$ BEGIN IF EXISTS (SELECT 1 FROM face_embedding WHERE sample_id='66666666-6666-6666-6666-666666666666') THEN RAISE EXCEPTION 'còn embedding'; END IF; END $d$$q$, false);
SELECT pg_temp.thu('M1 Hai mô hình cùng đang chạy', $q$INSERT INTO recognition_model(code,name,backbone,manifest_id,source_path,source_sha256,stripped_sha256,epoch,t_bs,alignment_version)
  VALUES ('X','x','r18','x','x',repeat('0',64),repeat('0',64),1,0.1,'x')$q$, true);
SELECT pg_temp.thu('G1 Cửa CUSTOM không có ngưỡng', format($q$INSERT INTO gate(company_id,name,mode,default_policy,threshold_level) VALUES (%L,'Kho','ACCESS_ONLY','DEPARTMENTS_ONLY','CUSTOM')$q$, co), true) FROM v;
SELECT pg_temp.thu('G2 Thiết bị ACTIVE không có token', $q$UPDATE device SET status='ACTIVE' WHERE id='11111111-1111-1111-1111-111111111111'$q$, true);
SELECT pg_temp.thu('N1 TERMINATED không có ngày nghỉ', format($q$UPDATE employee SET status='TERMINATED' WHERE id=%L$q$, e6), true) FROM v;

SELECT ca, mong_doi, ket_qua FROM kq;
SELECT count(*) FILTER (WHERE ket_qua = 'ĐẠT') AS dat, count(*) AS tong FROM kq;
ROLLBACK;
