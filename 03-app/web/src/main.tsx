import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';
import { BrowserRouter } from 'react-router-dom';
import { antdTheme } from './theme/antdTheme';
import './theme/fonts';
import './theme/web-css-vars.css';
import './styles.css';
import { App } from './App';
import dayjs from 'dayjs';
import 'dayjs/locale/vi';
dayjs.locale('vi');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><ConfigProvider theme={antdTheme} locale={viVN}><BrowserRouter><App /></BrowserRouter></ConfigProvider></React.StrictMode>,
);
