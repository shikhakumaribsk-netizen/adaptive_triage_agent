/** @type {import('tailwindcss').Config} */
export default {
  // Scan all source files for class names
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],

  // Dark mode via class (we always apply dark manually on <html>)
  darkMode: 'class',

  theme: {
    extend: {

      // ── Colours ──────────────────────────────────────────
      colors: {
        // Triage tier colours — used in JS and CSS
        tier: {
          selfcare:  '#16a34a',
          standard:  '#22c55e',
          urgent:    '#eab308',
          emergency: '#f97316',
          critical:  '#ef4444',
          resus:     '#a855f7',
        },
        // Dark surface palette
        surface: {
          950: '#030712',
          900: '#111827',
          800: '#1f2937',
          700: '#374151',
        },
      },

      // ── Typography ────────────────────────────────────────
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],   // 10px
        '3xs': ['0.5rem',   { lineHeight: '0.75rem' }],    // 8px
      },

      // ── Border radius ─────────────────────────────────────
      borderRadius: {
        '3xl': '1.5rem',
        '4xl': '2rem',
      },

      // ── Animations ────────────────────────────────────────
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%':   { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        dotBounce: {
          '0%, 80%, 100%': { transform: 'translateY(0)',    opacity: '0.4' },
          '40%':           { transform: 'translateY(-6px)', opacity: '1' },
        },
        bandPulse: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.6' },
        },
        scanLine: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      animation: {
        'fade-in':       'fadeIn 0.35s ease both',
        'slide-in':      'slideInRight 0.3s ease both',
        'dot-bounce':    'dotBounce 1.2s infinite',
        'pulse-slow':    'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'band-pulse':    'bandPulse 2s ease-in-out infinite',
        'scan-line':     'scanLine 2s linear infinite',
      },

      // ── Box shadow ────────────────────────────────────────
      boxShadow: {
        'glow-red':    '0 0 20px rgba(220,38,38,0.3)',
        'glow-purple': '0 0 20px rgba(168,85,247,0.3)',
        'glow-green':  '0 0 20px rgba(34,197,94,0.3)',
        'inner-dark':  'inset 0 2px 8px rgba(0,0,0,0.4)',
      },

      // ── Spacing ───────────────────────────────────────────
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },

      // ── Max width ─────────────────────────────────────────
      maxWidth: {
        '8xl':  '88rem',
        '9xl':  '96rem',
        '10xl': '120rem',
      },

      // ── Z-index ───────────────────────────────────────────
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },

      // ── Backdrop blur ─────────────────────────────────────
      backdropBlur: {
        xs: '2px',
      },
    },
  },

  plugins: [
    // No extra plugins needed — keeping zero runtime deps
  ],
};