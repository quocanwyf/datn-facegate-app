/** "Fresh Bloom" UI kit — Tailwind theme extension. Requires tokens.css loaded globally. */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,html}'],
  theme: {
    extend: {
      colors: {
        bg: v('bg'),
        surface: { DEFAULT: v('surface'), raised: v('surface-raised') },
        border: v('border'),
        fg: { DEFAULT: v('text-primary'), muted: v('text-secondary'), disabled: v('text-disabled') },
        primary: { DEFAULT: v('primary'), strong: v('primary-strong'), fg: v('on-primary') },
        accent: { DEFAULT: v('accent'), 2: v('accent-2') },
        inverse: { DEFAULT: v('inverse'), fg: v('on-inverse') },
        success: { DEFAULT: v('success'), surface: v('success-surface') },
        warning: { DEFAULT: v('warning'), surface: v('warning-surface') },
        error: { DEFAULT: v('error'), surface: v('error-surface') },
        info: { DEFAULT: v('info'), surface: v('info-surface') },
        leaf:   { 50:'#F5FBEA',100:'#E8F6D0',200:'#D2EDA4',300:'#B9E276',400:'#A3D853',500:'#8AC43A',600:'#6BA22A',700:'#4F7C20',800:'#3B5D1C',900:'#2C4517' },
        forest: { 50:'#EEF4E8',100:'#D7E6C8',200:'#B3CF95',300:'#8DB563',400:'#6A9A3C',500:'#4F8126',600:'#3E6A1A',700:'#2E5E14',800:'#234A10',900:'#17330A' },
        amber:  { 50:'#FFF8E6',100:'#FFEDBF',200:'#FFDD8A',300:'#FFCB4F',400:'#FDB827',500:'#F5A00A',600:'#D6820A',700:'#A9610C',800:'#7F4A10',900:'#5C3610' },
        berry:  { 50:'#FDECEC',100:'#FAD0D0',200:'#F4A3A4',300:'#EC6F71',400:'#E5484B',500:'#D92D2F',600:'#B5241F',700:'#8F1D1A',800:'#6B1715',900:'#4A1110' },
        stone:  { 0:'#FFFFFF',25:'#F7F6F4',50:'#F1F0ED',100:'#EAE8E4',200:'#DDDAD5',300:'#C7C4BE',400:'#A3A09A',500:'#85827C',600:'#66635E',700:'#4A4844',800:'#2E2D2A',900:'#1A1A18',950:'#0F0F0E' },
      },
      fontFamily: {
        display: ['"Inter Display"', 'Inter', 'Manrope', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'Manrope', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        display: ['56px', { lineHeight: '1.05', letterSpacing: '-0.03em', fontWeight: '600' }],
        h1: ['40px', { lineHeight: '1.1', letterSpacing: '-0.025em', fontWeight: '600' }],
        h2: ['32px', { lineHeight: '1.15', letterSpacing: '-0.02em', fontWeight: '600' }],
        h3: ['24px', { lineHeight: '1.25', letterSpacing: '-0.015em', fontWeight: '600' }],
        h4: ['20px', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        h5: ['18px', { lineHeight: '1.35', letterSpacing: '-0.005em', fontWeight: '500' }],
        h6: ['16px', { lineHeight: '1.4', fontWeight: '600' }],
        'body-lg': ['18px', { lineHeight: '1.55' }],
        'body-md': ['16px', { lineHeight: '1.5' }],
        'body-sm': ['14px', { lineHeight: '1.45' }],
        caption: ['12px', { lineHeight: '1.35', letterSpacing: '0.01em' }],
        label: ['13px', { lineHeight: '1.2', letterSpacing: '0.005em', fontWeight: '500' }],
        button: ['15px', { lineHeight: '1', letterSpacing: '-0.005em', fontWeight: '600' }],
        metric: ['22px', { lineHeight: '1.1', letterSpacing: '-0.01em', fontWeight: '600' }],
      },
      borderRadius: {
        xs: 'var(--radius-xs)', sm: 'var(--radius-sm)', md: 'var(--radius-md)',
        lg: 'var(--radius-lg)', xl: 'var(--radius-xl)', '2xl': 'var(--radius-2xl)', full: 'var(--radius-full)',
      },
      boxShadow: { 1: 'var(--shadow-1)', 2: 'var(--shadow-2)', 3: 'var(--shadow-3)', ring: 'var(--ring)' },
      backgroundImage: {
        backdrop: 'var(--gradient-backdrop)', bloom: 'var(--gradient-bloom)',
        scan: 'var(--gradient-scan)', 'media-fade': 'var(--gradient-media-fade)',
      },
      transitionDuration: { fast: '120ms', base: '200ms', slow: '320ms' },
      transitionTimingFunction: {
        standard: 'cubic-bezier(0.2,0,0,1)', emphasized: 'cubic-bezier(0.3,0,0,1.2)', exit: 'cubic-bezier(0.4,0,1,1)',
      },
      maxWidth: { content: '1280px', prose: '720px' },
      screens: { sm: '640px', md: '768px', lg: '1024px', xl: '1280px', '2xl': '1440px' },
      keyframes: {
        scan: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        'pop-in': { '0%': { opacity: 0, transform: 'scale(.96)' }, '100%': { opacity: 1, transform: 'scale(1)' } },
      },
      animation: { scan: 'scan 1.6s cubic-bezier(0.2,0,0,1) infinite alternate', 'pop-in': 'pop-in 200ms cubic-bezier(0.3,0,0,1.2)' },
    },
  },
};
