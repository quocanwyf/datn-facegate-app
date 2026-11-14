/** "Canopy" web UI kit — Tailwind theme extension. Load tokens.css globally. */
const v = (n) => `rgb(var(--${n}) / <alpha-value>)`;
const st = (n) => ({ bg: v(`st-${n}-bg`), fg: v(`st-${n}-fg`) });

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,html}'],
  theme: {
    extend: {
      colors: {
        canvas: v('canvas'),
        bg: v('bg'),
        surface: { DEFAULT: v('surface'), muted: v('surface-muted'), selected: v('surface-selected') },
        border: { DEFAULT: v('border'), strong: v('border-strong') },
        fg: { DEFAULT: v('text-primary'), muted: v('text-secondary'), placeholder: v('text-placeholder'), disabled: v('text-disabled') },
        primary: { DEFAULT: v('primary'), hover: v('primary-hover'), fg: v('on-primary'), soft: v('primary-soft'), 'soft-fg': v('on-primary-soft') },
        status: { new: st('new'), progress: st('progress'), success: st('success'), info: st('info'), error: st('error'), warning: st('warning'), dot: v('dot') },
        teal: { 50:'#EAF6F4',100:'#DDF1EE',200:'#B5E2DB',300:'#84CFC4',400:'#4FB8A9',500:'#12A08F',600:'#0E7C74',700:'#0A5F59',800:'#084A46',900:'#063735' },
        sky:  { 50:'#EEF7FD',100:'#D9EDFB',200:'#B6DCF7',300:'#8CC8F2',400:'#5FB0EA',500:'#3B96DC',600:'#2A7BC0',700:'#1F6299',800:'#184C77',900:'#133B5C' },
        gray: { 0:'#FFFFFF',25:'#FAFAFA',50:'#F4F5F4',100:'#EDEFEE',200:'#E3EBE9',300:'#D3D9D7',400:'#A9B0AD',500:'#828A87',600:'#5F6865',700:'#46504D',800:'#2C3836',900:'#1B2B2A',950:'#0E1A19' },
      },
      fontFamily: {
        heading: ['Poppins', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        display: ['48px', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '500' }],
        h1: ['36px', { lineHeight: '1.15', letterSpacing: '-0.015em', fontWeight: '500' }],
        h2: ['28px', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '500' }],
        h3: ['22px', { lineHeight: '1.3', letterSpacing: '-0.005em', fontWeight: '500' }],
        h4: ['18px', { lineHeight: '1.35', fontWeight: '500' }],
        h5: ['16px', { lineHeight: '1.4', fontWeight: '600' }],
        h6: ['14px', { lineHeight: '1.4', fontWeight: '600' }],
        'body-lg': ['16px', { lineHeight: '1.5' }],
        'body-md': ['14px', { lineHeight: '1.5' }],
        'body-sm': ['13px', { lineHeight: '1.45' }],
        caption: ['12px', { lineHeight: '1.35', letterSpacing: '0.01em' }],
        overline: ['11px', { lineHeight: '1.3', letterSpacing: '0.04em', fontWeight: '500' }],
        label: ['12px', { lineHeight: '1.3', letterSpacing: '0.005em' }],
        button: ['14px', { lineHeight: '1', fontWeight: '500' }],
        table: ['13px', { lineHeight: '1.4', fontWeight: '500' }],
        metric: ['28px', { lineHeight: '1.15', letterSpacing: '-0.01em', fontWeight: '500' }],
      },
      borderRadius: {
        xs: 'var(--radius-xs)', sm: 'var(--radius-sm)', md: 'var(--radius-md)', lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)', '2xl': 'var(--radius-2xl)', '3xl': 'var(--radius-3xl)', full: 'var(--radius-full)',
      },
      boxShadow: { 1: 'var(--shadow-1)', 2: 'var(--shadow-2)', 3: 'var(--shadow-3)', frame: 'var(--shadow-frame)', ring: 'var(--ring)' },
      backgroundImage: {
        sidebar: 'var(--gradient-sidebar)', 'glass-frame': 'var(--gradient-glass-frame)',
        header: 'var(--gradient-header)', 'hero-mist': 'var(--gradient-hero-mist)',
      },
      spacing: { header: 'var(--header-h)', rail: 'var(--rail-w)' },
      maxWidth: { content: '1440px', form: '480px', prose: '720px' },
      screens: { sm: '640px', md: '768px', lg: '1024px', xl: '1280px', '2xl': '1536px' },
      transitionDuration: { fast: '120ms', base: '180ms', slow: '280ms' },
      transitionTimingFunction: { standard: 'cubic-bezier(.2,0,0,1)', exit: 'cubic-bezier(.4,0,1,1)' },
      keyframes: {
        'fade-up': { '0%': { opacity: 0, transform: 'translateY(4px)' }, '100%': { opacity: 1, transform: 'none' } },
        'tab-ink': { '0%': { transform: 'scaleX(0)' }, '100%': { transform: 'scaleX(1)' } },
      },
      animation: { 'fade-up': 'fade-up 180ms cubic-bezier(.2,0,0,1)', 'tab-ink': 'tab-ink 180ms cubic-bezier(.2,0,0,1)' },
    },
  },
};
