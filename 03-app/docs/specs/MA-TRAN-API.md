# Ma trận REST → tính năng

Đồng bộ OpenAPI v1.1.0 ngày 14/11/2026 theo Q-001–Q-013. Mỗi operation giữ feature phụ trách chính, thêm prefix `/api/v1` cho mọi path; quyền/response hiện tại từ hợp đồng nguồn.

| Method | Path | operationId | Feature chính | x-roles | Tham số | HTTP |
|---|---|---|---|---|---|---|
| POST | `/auth/login` | `postAuthLogin` | [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | public | — | 200, 400, 401, 429 |
| POST | `/auth/refresh` | `postAuthRefresh` | [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | public | — | 200, 401 |
| POST | `/auth/logout` | `postAuthLogout` | [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | any | — | 204, 401 |
| POST | `/auth/change-password` | `postAuthChangePassword` | [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | any | — | 204, 400, 401, 422 |
| GET | `/me` | `getMe` | [FG-AUTH-001](03.archived/FG-AUTH-001-xac-thuc-phien.md) | any | — | 200, 401 |
| GET | `/me/today` | `getMeToday` | [FG-ME-001](02.approved/FG-ME-001-cong-ca-ca-nhan.md) | EMPLOYEE | — | 200, 401, 403 |
| GET | `/me/attendance` | `getMeAttendance` | [FG-ME-001](02.approved/FG-ME-001-cong-ca-ca-nhan.md) | EMPLOYEE | month | 200, 401, 403 |
| GET | `/me/days/{date}` | `getMeDaysById` | [FG-ME-001](02.approved/FG-ME-001-cong-ca-ca-nhan.md) | EMPLOYEE | date | 200, 401, 403 |
| GET | `/me/requests` | `getMeRequests` | [FG-REQ-001](02.approved/FG-REQ-001-tao-huy-giai-trinh.md) | EMPLOYEE | status, page, size | 200, 401, 403 |
| POST | `/me/requests` | `postMeRequests` | [FG-REQ-001](02.approved/FG-REQ-001-tao-huy-giai-trinh.md) | EMPLOYEE | — | 201, 400, 401, 403, 409, 422 |
| POST | `/me/requests/{id}/cancel` | `postMeRequestsCancel` | [FG-REQ-001](02.approved/FG-REQ-001-tao-huy-giai-trinh.md) | EMPLOYEE | id | 200, 401, 403, 404, 422 |
| GET | `/me/face` | `getMeFace` | [FG-FACE-004](02.approved/FG-FACE-004-xoa-rut-dong-y.md) | EMPLOYEE | — | 200, 401, 403 |
| POST | `/me/face/revoke` | `postMeFaceRevoke` | [FG-FACE-004](02.approved/FG-FACE-004-xoa-rut-dong-y.md) | EMPLOYEE | — | 200, 401, 403, 503 |
| GET | `/dashboard/today` | `getDashboardToday` | [FG-DASH-001](02.approved/FG-DASH-001-tong-quan.md) | OWNER, HR | — | 200, 400, 401, 403 |
| GET | `/employees` | `getEmployees` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR, MANAGER, SECURITY (Q-014 tối thiểu ACTIVE/MANUAL) | q, department_id, status, attendance_method, face_profile_status, page, size | 200, 400, 401, 403 |
| POST | `/employees` | `postEmployees` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR | — | 201, 400, 401, 403, 409 |
| GET | `/employees/{id}` | `getEmployeesById` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR, MANAGER | id | 200, 401, 403, 404 |
| PATCH | `/employees/{id}` | `patchEmployeesById` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 409 |
| POST | `/employees/{id}/suspend` | `postEmployeesSuspend` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR | id | 200, 401, 403, 404, 422 |
| POST | `/employees/{id}/reactivate` | `postEmployeesReactivate` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR | id | 200, 401, 403, 404, 422 |
| POST | `/employees/{id}/terminate` | `postEmployeesTerminate` | [FG-EMP-001](02.approved/FG-EMP-001-nhan-vien.md) | OWNER, HR | id | 200, 401, 403, 404, 422, 503 |
| DELETE | `/employees/{id}/face` | `deleteEmployeesFace` | [FG-FACE-004](02.approved/FG-FACE-004-xoa-rut-dong-y.md) | OWNER, HR | id | 204, 401, 403, 404, 503 |
| GET | `/departments` | `getDepartments` | [FG-ORG-001](03.archived/FG-ORG-001-phong-ban.md) | OWNER, HR, MANAGER, SECURITY | — | 200, 400, 401, 403 |
| POST | `/departments` | `postDepartments` | [FG-ORG-001](03.archived/FG-ORG-001-phong-ban.md) | OWNER, HR | — | 201, 400, 401, 403, 409 |
| PATCH | `/departments/{id}` | `patchDepartmentsById` | [FG-ORG-001](03.archived/FG-ORG-001-phong-ban.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 409 |
| GET | `/users` | `getUsers` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | q, page, size | 200, 400, 401, 403 |
| POST | `/users` | `postUsers` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | — | 201, 400, 401, 403, 409 |
| PATCH | `/users/{id}` | `patchUsersById` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | id | 200, 400, 401, 403, 404 |
| PUT | `/users/{id}/roles` | `putUsersRoles` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 422 |
| PUT | `/users/{id}/kiosk-pin` | `putUsersKioskPin` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | id | 204, 400, 401, 403, 404, 422 |
| POST | `/users/{id}/reset-password` | `postUsersResetPassword` | [FG-AUTH-002](02.approved/FG-AUTH-002-tai-khoan-vai-tro-pin.md) | OWNER, HR | id | 200, 401, 403, 404 |
| GET | `/face-profiles` | `getFaceProfiles` | [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | OWNER, HR | status, employee_id, page, size | 200, 400, 401, 403 |
| GET | `/face-profiles/{id}` | `getFaceProfilesById` | [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | OWNER, HR | id | 200, 401, 403, 404 |
| POST | `/face-profiles/{id}/approve` | `postFaceProfilesApprove` | [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 422, 409, 503 |
| POST | `/face-profiles/{id}/reject` | `postFaceProfilesReject` | [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 422, 409, 503 |
| GET | `/face-samples/{id}/image` | `getFaceSamplesImage` | [FG-FACE-003](02.approved/FG-FACE-003-duyet-ho-so-gallery.md) | OWNER, HR | id | 200, 401, 403, 404 |
| GET | `/gates` | `getGates` | [FG-GATE-001](02.approved/FG-GATE-001-cua-chinh-sach.md) | OWNER, HR, SECURITY | — | 200, 400, 401, 403 |
| POST | `/gates` | `postGates` | [FG-GATE-001](02.approved/FG-GATE-001-cua-chinh-sach.md) | OWNER | — | 201, 400, 401, 403, 409 |
| PATCH | `/gates/{id}` | `patchGatesById` | [FG-GATE-001](02.approved/FG-GATE-001-cua-chinh-sach.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 409, 422 |
| PUT | `/gates/{id}/allowed-departments` | `putGatesAllowedDepartments` | [FG-GATE-001](02.approved/FG-GATE-001-cua-chinh-sach.md) | OWNER, HR | id | 200, 400, 401, 403, 404 |
| POST | `/gates/{id}/manual-open` | `postGatesManualOpen` | [FG-ACCESS-002](02.approved/FG-ACCESS-002-mo-cua-thu-cong.md) | OWNER, SECURITY | id | 201, 400, 401, 403, 404 |
| GET | `/devices` | `getDevices` | [FG-DEV-001](02.approved/FG-DEV-001-thiet-bi-ghep-thu-hoi.md) | OWNER | gate_id | 200, 400, 401, 403 |
| POST | `/devices` | `postDevices` | [FG-DEV-001](02.approved/FG-DEV-001-thiet-bi-ghep-thu-hoi.md) | OWNER | — | 201, 400, 401, 403, 404 |
| POST | `/devices/{id}/revoke` | `postDevicesRevoke` | [FG-DEV-001](02.approved/FG-DEV-001-thiet-bi-ghep-thu-hoi.md) | OWNER | id | 200, 401, 403, 404 |
| POST | `/kiosk/pair` | `postKioskPair` | [FG-DEV-001](02.approved/FG-DEV-001-thiet-bi-ghep-thu-hoi.md) | public | — | 200, 400, 404, 422, 429 |
| GET | `/kiosk/enrollers` | `getKioskEnrollers` | [FG-KIOSK-002](02.approved/FG-KIOSK-002-phien-dang-ky-pin.md) | device | — | 200, 401 |
| POST | `/kiosk/enroll/sessions` | `postKioskEnrollSessions` | [FG-KIOSK-002](02.approved/FG-KIOSK-002-phien-dang-ky-pin.md) | device | — | 201, 400, 401, 403, 429 |
| GET | `/kiosk/enroll/sessions/{id}/employees` | `getKioskEnrollSessionsEmployees` | [FG-KIOSK-002](02.approved/FG-KIOSK-002-phien-dang-ky-pin.md) | device | id, q | 200, 401, 404, 422 |
| POST | `/kiosk/enroll/sessions/{id}/consent` | `postKioskEnrollSessionsConsent` | [FG-FACE-001](02.approved/FG-FACE-001-dong-y-sinh-trac.md) | device | id | 200, 400, 401, 404, 422, 503 |
| GET | `/shifts` | `getShifts` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR, MANAGER | — | 200, 400, 401, 403 |
| POST | `/shifts` | `postShifts` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | — | 201, 400, 401, 403, 409, 422 |
| PATCH | `/shifts/{id}` | `patchShiftsById` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 422 |
| GET | `/shift-assignments` | `getShiftAssignments` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR, MANAGER | employee_id, department_id | 200, 400, 401, 403 |
| POST | `/shift-assignments` | `postShiftAssignments` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | — | 201, 400, 401, 403, 409 |
| DELETE | `/shift-assignments/{id}` | `deleteShiftAssignmentsById` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | id | 204, 401, 403, 404 |
| GET | `/holidays` | `getHolidays` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | any | year | 200, 400, 401, 403 |
| POST | `/holidays` | `postHolidays` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | — | 201, 400, 401, 403, 409 |
| DELETE | `/holidays/{date}` | `deleteHolidaysById` | [FG-ATT-001](03.archived/FG-ATT-001-ca-phan-ca-ngay-le.md) | OWNER, HR | date | 204, 401, 403, 404 |
| GET | `/attendance/days` | `getAttendanceDays` | [FG-ATT-003](02.approved/FG-ATT-003-bang-cong-sua-nghi.md) | OWNER, HR, MANAGER | from, to, department_id, employee_id, status, page, size | 200, 400, 401, 403 |
| PATCH | `/attendance/days/{id}` | `patchAttendanceDaysById` | [FG-ATT-003](02.approved/FG-ATT-003-bang-cong-sua-nghi.md) | OWNER, HR | id | 200, 400, 401, 403, 404, 422 |
| POST | `/attendance/leave` | `postAttendanceLeave` | [FG-ATT-003](02.approved/FG-ATT-003-bang-cong-sua-nghi.md) | OWNER, HR | — | 200, 400, 401, 403, 404 |
| GET | `/attendance/export` | `getAttendanceExport` | [FG-ATT-005](03.archived/FG-ATT-005-excel-thang.md) | OWNER, HR, MANAGER | month, department_id | 200, 400, 401, 403 |
| POST | `/attendance/manual` | `postAttendanceManual` | [FG-ATT-004](02.approved/FG-ATT-004-cham-cong-ho.md) | OWNER, HR, SECURITY | — | 201, 400, 401, 403, 404, 422 |
| GET | `/attendance/requests` | `getAttendanceRequests` | [FG-REQ-002](02.approved/FG-REQ-002-duyet-giai-trinh.md) | OWNER, HR, MANAGER | status, scope, page, size | 200, 400, 401, 403 |
| POST | `/attendance/requests/{id}/approve` | `postAttendanceRequestsApprove` | [FG-REQ-002](02.approved/FG-REQ-002-duyet-giai-trinh.md) | OWNER, HR, MANAGER | id | 200, 400, 401, 403, 404, 422 |
| POST | `/attendance/requests/{id}/reject` | `postAttendanceRequestsReject` | [FG-REQ-002](02.approved/FG-REQ-002-duyet-giai-trinh.md) | OWNER, HR, MANAGER | id | 200, 400, 401, 403, 404, 422 |
| GET | `/events` | `getEvents` | [FG-EVENT-001](02.approved/FG-EVENT-001-su-kien-csv-bao-cao.md) | OWNER, HR, SECURITY, MANAGER | from_ts, to_ts, gate_id, result, employee_id, performed_by, handled, limit, page, size | 200, 400, 401, 403 |
| GET | `/events/{id}/snapshot` | `getEventsSnapshot` | [FG-EVENT-001](02.approved/FG-EVENT-001-su-kien-csv-bao-cao.md) | OWNER, HR, SECURITY | id | 200, 401, 403, 404 |
| POST | `/events/{id}/handle` | `postEventsHandle` | [FG-MON-001](02.approved/FG-MON-001-giam-sat-canh-bao.md) | OWNER, SECURITY | id | 200, 400, 401, 403, 404, 422 |
| GET | `/events/manual-report` | `getEventsManualReport` | [FG-EVENT-001](02.approved/FG-EVENT-001-su-kien-csv-bao-cao.md) | OWNER, HR, SECURITY | from, to | 200, 400, 401, 403 |
| GET | `/events/export` | `getEventsExport` | [FG-EVENT-001](02.approved/FG-EVENT-001-su-kien-csv-bao-cao.md) | OWNER, HR, SECURITY | from_ts, to_ts, gate_id, result | 200, 400, 401, 403 |
| GET | `/settings/recognition` | `getSettingsRecognition` | [FG-AI-004](03.archived/FG-AI-004-settings-nguong.md) | OWNER, HR | — | 200, 400, 401, 403 |
| PUT | `/settings/recognition` | `putSettingsRecognition` | [FG-AI-004](03.archived/FG-AI-004-settings-nguong.md) | OWNER | — | 200, 400, 401, 403, 422 |
| GET | `/models/active` | `getModelsActive` | [FG-AI-004](03.archived/FG-AI-004-settings-nguong.md) | OWNER, HR | — | 200, 400, 401, 403 |
| GET | `/audit-logs` | `getAuditLogs` | [FG-AUDIT-001](02.approved/FG-AUDIT-001-nhat-ky.md) | OWNER | from_ts, to_ts, actor_user_id, action, page, size | 200, 400, 401, 403 |
| GET | `/health` | `getHealth` | [FG-SYS-001](02.approved/FG-SYS-001-suc-khoe-van-hanh.md) | public | — | 200 |
| GET | `/version` | `getVersion` | [FG-SYS-001](02.approved/FG-SYS-001-suc-khoe-van-hanh.md) | public | — | 200 |

Required/kiểu/bounds/schema tại [OpenAPI](../../openapi/openapi.yaml). WS ở [ws-protocol](../../openapi/ws-protocol.md): NO_GALLERY và lỗi frame có seq; xử lý nội bộ không có endpoint riêng.
