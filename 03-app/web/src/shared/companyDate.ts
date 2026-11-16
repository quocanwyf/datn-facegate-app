import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import { companyTimezone } from './format';
dayjs.extend(utc);
dayjs.extend(timezone);
export const companyDate = (value?: string) => value ? dayjs(value).tz(companyTimezone) : dayjs().tz(companyTimezone);
