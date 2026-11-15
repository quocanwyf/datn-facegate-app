import type { ThemeConfig } from 'antd';
import tokens from './tokens.json';
export const antdTheme: ThemeConfig = { token: tokens.token, components: tokens.components };
