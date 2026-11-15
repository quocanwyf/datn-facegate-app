import * as SecureStore from 'expo-secure-store';
import type { components } from '../api/schema';
import { hubAddress } from '../api/rest';
export type PairedDevice = { hub: string; token: string; gate: components['schemas']['KioskGate'] };
const key = 'facegate.device.v1';
export async function loadDevice(): Promise<PairedDevice | undefined> {
  const saved = await SecureStore.getItemAsync(key); if (!saved) return;
  try {
    const value: PairedDevice = JSON.parse(saved);
    if (typeof value.token !== 'string' || !value.token || !value.gate?.id || !value.gate.name) throw new Error();
    return { ...value, hub: hubAddress(value.hub) };
  } catch { await SecureStore.deleteItemAsync(key); return; }
}
export async function saveDevice(value: PairedDevice) { await SecureStore.setItemAsync(key, JSON.stringify(value)); }
export async function clearDevice() { await SecureStore.deleteItemAsync(key); }
