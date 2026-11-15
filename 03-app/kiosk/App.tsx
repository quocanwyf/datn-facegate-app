import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Alert, AppState, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { Inter_400Regular } from '@expo-google-fonts/inter/400Regular';
import { Inter_500Medium } from '@expo-google-fonts/inter/500Medium';
import { Inter_600SemiBold } from '@expo-google-fonts/inter/600SemiBold';
import { useKeepAwake } from 'expo-keep-awake';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { createKioskClient } from './src/api/client';
import type { components } from './src/api/schema';
import { ApiFailure, failureMessage, hubAddress, unwrap } from './src/api/rest';
import { clearDevice, loadDevice, saveDevice, type PairedDevice } from './src/storage/device';
import { KioskSocket, type Connection, type Transport } from './src/ws/KioskSocket';
import type { Config, Done, FrameState, HubMessage, Progress, Result } from './src/ws/protocol';
import { K01Pair } from './src/screens/k01-pair';
import { K02Scan } from './src/screens/k02-scan';
import { K04Result } from './src/screens/k04-result';
import { K05Pin } from './src/screens/k05-pin';
import { K06Pick } from './src/screens/k06-pick';
import { K07Consent } from './src/screens/k07-consent';
import { K09Sent } from './src/screens/k09-sent';
import { K11Offline } from './src/screens/k11-offline';
import { ErrorNotice, PillButton, styles } from './src/components/controls';
import { theme } from './src/theme';
type Scene = 'pair' | 'scan' | 'pin' | 'pick' | 'consent' | 'enroll' | 'result' | 'sent' | 'declined' | 'offline';
type Employee = components['schemas']['KioskEmployee'];
type Session = components['schemas']['EnrollSession'];
type Enroller = components['schemas']['Enroller'];

export default function App() { return <SafeAreaProvider><KioskApp /></SafeAreaProvider>; }
function KioskApp() {
  useKeepAwake(undefined, { suppressDeactivateWarnings: true });
  const [fontsLoaded, fontError] = useFonts({ Inter_400Regular, Inter_500Medium, Inter_600SemiBold });
  const [hydrated, setHydrated] = useState(false); const [device, setDevice] = useState<PairedDevice>();
  const [scene, setScene] = useState<Scene>('pair'); const sceneRef = useRef<Scene>('pair');
  const socketRef = useRef<KioskSocket | undefined>(undefined);
  const [connection, setConnection] = useState<Connection>({ connected: false, offline: false, attempt: 0 });
  const [config, setConfig] = useState<Config>(); const [frame, setFrame] = useState<FrameState>();
  const [result, setResult] = useState<Result>(); const [progress, setProgress] = useState<Progress>(); const [done, setDone] = useState<Done>();
  const [resultSeconds, setResultSeconds] = useState(3);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const mutation = useRef(false);
  const [people, setPeople] = useState<Enroller[]>([]); const [peopleLoading, setPeopleLoading] = useState(false);
  const peopleRequest = useRef(0);
  const [session, setSession] = useState<Session>(); const sessionRef = useRef<Session | undefined>(undefined);
  const [employee, setEmployee] = useState<Employee>(); const employeeRef = useRef<Employee | undefined>(undefined);
  const [query, setQuery] = useState(''); const [employees, setEmployees] = useState<Employee[]>([]); const [employeesLoading, setEmployeesLoading] = useState(false); const [listRetry, setListRetry] = useState(0);
  const [remaining, setRemaining] = useState('5:00'); const clockOffset = useRef(0);
  const firstFaceAt = useRef<number | undefined>(undefined); const lastFrameAt = useRef(0);
  const client = useMemo(() => device ? createKioskClient(device.hub, async () => device.token) : undefined, [device]);
  const go = useCallback((next: Scene) => { sceneRef.current = next; socketRef.current?.setCaptureEnabled(next === 'scan' || next === 'enroll'); setScene(next); }, []);
  useEffect(() => { if (__DEV__) console.info('FACEGATE_SCENE', scene); }, [scene]);
  const resetEnrollment = useCallback(() => { peopleRequest.current++; sessionRef.current = undefined; employeeRef.current = undefined; setSession(undefined); setEmployee(undefined); setProgress(undefined); setDone(undefined); setFrame(undefined); setError(''); setQuery(''); }, []);
  const cancel = useCallback(() => { resetEnrollment(); socketRef.current?.restart(); firstFaceAt.current = undefined; go('scan'); }, [go, resetEnrollment]);
  useEffect(() => { let live = true; void loadDevice().then(value => { if (live) { setDevice(value); go(value ? 'scan' : 'pair'); } }).catch(() => { if (live) setError('Không đọc được thông tin thiết bị đã lưu. Vui lòng ghép lại.'); }).finally(() => { if (live) setHydrated(true); }); return () => { live = false; }; }, [go]);
  useEffect(() => {
    if (!device || !hydrated || !fontsLoaded) return;
    function receive(message: HubMessage) {
      if (message.type === 'config') { setConfig(message); const difference = Date.parse(message.server_time) - Date.now(); if (Number.isFinite(difference)) clockOffset.current = difference; }
      else if (message.type === 'state' && ['scan', 'enroll'].includes(sceneRef.current)) {
        setFrame(message);
        if (['NO_FACE', 'TOO_FAR', 'LOOK_STRAIGHT', 'NO_GALLERY'].includes(message.state)) firstFaceAt.current = undefined;
        else if (message.frames_in_window === 1 || firstFaceAt.current === undefined) firstFaceAt.current = lastFrameAt.current;
      } else if (message.type === 'result' && sceneRef.current === 'scan') {
        if (firstFaceAt.current !== undefined) console.info('FACEGATE_TIMING', JSON.stringify({ elapsed_ms: Date.now() - firstFaceAt.current, result: message.result }));
        firstFaceAt.current = undefined; setResultSeconds(socketRef.current?.config?.result_display_sec ?? 3); setResult(message); go('result');
      } else if (message.type === 'enroll_progress' && sceneRef.current === 'enroll') { setProgress(message); if (__DEV__) console.info('FACEGATE_ENROLL_PROGRESS', JSON.stringify({ accepted: message.accepted, reason: message.reason })); }
      else if (message.type === 'enroll_done' && sceneRef.current === 'enroll') { setDone(message); go('sent'); }
      else if (message.type === 'error') {
        if (message.code === 'SESSION_EXPIRED') { resetEnrollment(); go('scan'); }
        else if (sceneRef.current === 'enroll' && !['MODEL_NOT_VERIFIED', 'RECOGNITION_UNAVAILABLE', 'FRAME_DECODE_FAILED'].includes(message.code)) { socketRef.current?.setCaptureEnabled(false); setError(message.message); }
      }
    }
    const socket = new KioskSocket(device.hub, device.token, {
      onMessage: receive,
      onConnection: value => {
        setConnection(value);
        if (value.offline || value.unavailable) { if (sceneRef.current !== 'offline') { resetEnrollment(); go('offline'); } }
        else if (value.connected && sceneRef.current === 'offline') go('scan');
      },
      onRevoked: () => { void clearDevice().catch(() => {}).finally(() => { setDevice(undefined); setConfig(undefined); resetEnrollment(); setError('Thiết bị đã bị thu hồi hoặc token hết hạn. Vui lòng ghép lại.'); go('pair'); }); },
    }, url => new WebSocket(url) as unknown as Transport);
    socketRef.current = socket; socket.setCaptureEnabled(sceneRef.current === 'scan'); socket.start();
    const subscription = AppState.addEventListener('change', state => { if (state !== 'active') { socket.setCaptureEnabled(false); socket.stop(); } else { resetEnrollment(); go('scan'); socket.start(); } });
    return () => { subscription.remove(); socket.stop(); if (socketRef.current === socket) socketRef.current = undefined; };
  }, [device, hydrated, fontsLoaded, go, resetEnrollment]);
  useEffect(() => {
    const seconds = scene === 'result' ? resultSeconds : scene === 'sent' ? 5 : scene === 'declined' ? 4 : undefined;
    if (seconds === undefined) return;
    const timer = setTimeout(() => { resetEnrollment(); go('scan'); }, seconds * 1000); return () => clearTimeout(timer);
  }, [scene, resultSeconds, go, resetEnrollment]);
  useEffect(() => {
    if (!session || !['pick', 'consent', 'enroll'].includes(scene)) return;
    const tick = () => { const seconds = Math.ceil((Date.parse(session.expires_at) - Date.now() - clockOffset.current) / 1000); if (seconds <= 0) cancel(); else setRemaining(`${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`); };
    tick(); const timer = setInterval(tick, 1000); return () => clearInterval(timer);
  }, [session, scene, cancel]);
  useEffect(() => {
    if (scene !== 'pick' || !session || !client) return;
    let live = true; const abort = new AbortController(); setEmployeesLoading(true); setError('');
    const timer = setTimeout(() => {
      void client.GET('/kiosk/enroll/sessions/{id}/employees', { params: { path: { id: session.enroll_session_id }, query: { q: query.trim() || undefined } }, signal: abort.signal }).then(unwrap).then(value => { if (live) setEmployees(value); }).catch(failure => { if (live) { if (failure instanceof ApiFailure && failure.code === 'SESSION_EXPIRED') cancel(); else setError(failureMessage(failure)); } }).finally(() => { if (live) setEmployeesLoading(false); });
    }, 250);
    const timeout = setTimeout(() => abort.abort(), 15000);
    return () => { live = false; clearTimeout(timer); clearTimeout(timeout); abort.abort(); };
  }, [scene, session, client, query, listRetry, cancel]);
  async function pair(hub: string, code: string) {
    if (mutation.current) return; mutation.current = true; setBusy(true); setError('');
    try {
      let address: string; try { address = hubAddress(hub); } catch { setError('Địa chỉ Hub phải có dạng http://địa-chỉ:8000, không kèm đường dẫn.'); return; }
      const response = unwrap(await createKioskClient(address, async () => null).POST('/kiosk/pair', { body: { code } }));
      const value: PairedDevice = { hub: address, token: response.device_token, gate: response.gate }; await saveDevice(value); setDevice(value); go('scan');
    } catch (failure) { setError(failureMessage(failure)); } finally { mutation.current = false; setBusy(false); }
  }
  async function loadPeople() {
    if (!client) return; setPeopleLoading(true); setError('');
    const request = ++peopleRequest.current;
    const current = () => peopleRequest.current === request && sceneRef.current === 'pin';
    try { const values = unwrap(await client.GET('/kiosk/enrollers')); if (current()) setPeople(values); }
    catch (failure) { if (current()) setError(failureMessage(failure)); } finally { if (current()) setPeopleLoading(false); }
  }
  async function enterEnrollment() { if (!connection.connected || connection.unavailable) return; resetEnrollment(); go('pin'); await loadPeople(); }
  async function submitPin(id: string, pin: string) {
    if (!client || mutation.current) return; mutation.current = true; setBusy(true); setError('');
    const request = peopleRequest.current;
    const current = () => sceneRef.current === 'pin' && peopleRequest.current === request;
    try { const created = unwrap(await client.POST('/kiosk/enroll/sessions', { body: { user_id: id, pin } })); if (current()) { sessionRef.current = created; setSession(created); go('pick'); } }
    catch (failure) { if (current()) setError(failureMessage(failure)); } finally { mutation.current = false; setBusy(false); }
  }
  function pick(value: Employee) {
    const sessionId = sessionRef.current?.enroll_session_id;
    if (!sessionId) return;
    const select = () => {
      if (sceneRef.current !== 'pick' || sessionRef.current?.enroll_session_id !== sessionId) return;
      if (Date.parse(sessionRef.current.expires_at) <= Date.now() + clockOffset.current) { cancel(); return; }
      employeeRef.current = value; setEmployee(value); setError(''); go('consent');
    };
    if (value.face_profile_status === 'PENDING_REVIEW') Alert.alert('Đăng ký lại?', 'Đã có bản chờ xác nhận. Chụp lại? Bản cũ chỉ được thay khi bộ mới lưu thành công.', [{ text: 'Huỷ', style: 'cancel' }, { text: 'Chụp lại', onPress: select }]);
    else select();
  }
  async function consent(agree: boolean) {
    if (!client || !sessionRef.current || !employeeRef.current || mutation.current) return;
    const sessionId = sessionRef.current.enroll_session_id; const employeeId = employeeRef.current.id;
    const current = () => sceneRef.current === 'consent' && sessionRef.current?.enroll_session_id === sessionId && employeeRef.current?.id === employeeId;
    mutation.current = true; setBusy(true); setError('');
    try {
      unwrap(await client.POST('/kiosk/enroll/sessions/{id}/consent', { params: { path: { id: sessionId } }, body: { employee_id: employeeId, agree } }));
      if (current()) { setProgress(undefined); setFrame(undefined); go(agree ? 'enroll' : 'declined'); }
    } catch (failure) { if (current()) { if (failure instanceof ApiFailure && failure.code === 'SESSION_EXPIRED') cancel(); else setError(failureMessage(failure)); } } finally { mutation.current = false; setBusy(false); }
  }
  const onSent = useCallback((at: number) => { lastFrameAt.current = at; }, []);
  function retryEnrollment() {
    if (!sessionRef.current || Date.parse(sessionRef.current.expires_at) <= Date.now() + clockOffset.current) { cancel(); return; }
    employeeRef.current = undefined; setEmployee(undefined); setProgress(undefined); setError(''); socketRef.current?.restart(); go('pick');
  }
  let content;
  if (!hydrated || !fontsLoaded) content = <View style={[styles.page, { justifyContent: 'center', alignItems: 'center' }]}><ActivityIndicator /><Text>{fontError ? 'Không tải được font. Vui lòng mở lại ứng dụng.' : 'Đang chuẩn bị Kiosk…'}</Text></View>;
  else if (scene === 'pair') content = <K01Pair busy={busy} error={error} onPair={(hub, code) => void pair(hub, code)} />;
  else if (scene === 'offline') content = <K11Offline connection={connection} />;
  else if (scene === 'result' && result) content = <K04Result result={result} seconds={resultSeconds} />;
  else if (scene === 'sent' || scene === 'declined') content = <K09Sent duplicate={done?.duplicate_warning} declined={scene === 'declined'} />;
  else if (scene === 'pin') content = <K05Pin people={people} loading={peopleLoading} error={error} busy={busy} onRetry={() => void loadPeople()} onCancel={cancel} onSubmit={submitPin} />;
  else if (scene === 'pick') content = <K06Pick employees={employees} loading={employeesLoading} error={error} query={query} remaining={remaining} onQuery={setQuery} onPick={pick} onCancel={cancel} onRetry={() => setListRetry(value => value + 1)} />;
  else if (scene === 'consent' && employee) content = <K07Consent employee={employee} error={error} busy={busy} onConsent={agree => void consent(agree)} onCancel={cancel} />;
  else if (config && socketRef.current) content = <K02Scan socket={socketRef.current} config={config} connected={connection.connected} state={frame} onEnroll={() => void enterEnrollment()} onSent={onSent} enroll={scene === 'enroll' && session && employee ? { mode: 'enroll', enroll_session_id: session.enroll_session_id, employee_id: employee.id } : undefined} progress={progress} error={scene === 'enroll' ? error : undefined} onCancel={cancel} onRetry={retryEnrollment} />;
  else content = <View style={[styles.page, { justifyContent: 'center', alignItems: 'center' }]}><ActivityIndicator /><Text style={styles.title}>Đang kết nối máy chủ…</Text><ErrorNotice message={error} />{!device ? <PillButton title="Ghép lại thiết bị" onPress={() => go('pair')} /> : null}</View>;
  return <SafeAreaView edges={scene === 'scan' || scene === 'enroll' ? [] : ['top', 'left', 'right', 'bottom']} style={{ flex: 1, backgroundColor: theme.color.bg }}><StatusBar hidden />{content}</SafeAreaView>;
}
