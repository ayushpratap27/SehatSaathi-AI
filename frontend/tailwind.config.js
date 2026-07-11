/** @type {import('tailwindcss').Config} */
// DESIGN.md reference: MongoDB design system
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // ── MongoDB Colors (from DESIGN.md) ─────────────────────────── //
      colors: {
        // Brand green
        'mdb-green':        '#00ed64',
        'mdb-green-dark':   '#00684a',
        'mdb-green-mid':    '#00a35c',
        'mdb-green-soft':   '#c3f0d2',
        'mdb-green-deep':   '#00b545',
        'mdb-green-press':  '#008c34',
        // Brand teal (dark canvas)
        'mdb-teal-deep':    '#001e2b',
        'mdb-teal':         '#003d4f',
        'mdb-teal-mid':     '#00684a',
        // Surface
        'mdb-canvas':       '#ffffff',
        'mdb-surface':      '#f9fbfa',
        'mdb-surface-soft': '#f4f7f6',
        'mdb-surface-feat': '#e3fcef',
        // Ink / type
        'mdb-ink':          '#001e2b',
        'mdb-charcoal':     '#1c2d38',
        'mdb-slate':        '#3d4f5b',
        'mdb-steel':        '#5c6c7a',
        'mdb-stone':        '#7c8c9a',
        'mdb-muted':        '#a8b3bc',
        // Hairlines
        'mdb-line':         '#e1e5e8',
        'mdb-line-soft':    '#eceff1',
        'mdb-line-strong':  '#c1ccd6',
        'mdb-line-dark':    '#1c2d38',
        // On-dark
        'mdb-on-dark':      '#ffffff',
        'mdb-on-primary':   '#001e2b',
        // Accent
        'mdb-purple':       '#7b3ff2',
        'mdb-orange':       '#fa6e39',
        'mdb-pink':         '#f06bb8',
        'mdb-blue':         '#3d4f9f',
      },

      // ── MongoDB Typography ────────────────────────────────────────── //
      fontFamily: {
        sans: ['"Euclid Circular A"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"Source Code Pro"', 'monospace'],
      },
      fontSize: {
        'mdb-hero':   ['72px', { lineHeight: '1.10', letterSpacing: '-1.5px' }],
        'mdb-xl':     ['56px', { lineHeight: '1.15', letterSpacing: '-1px'   }],
        'mdb-h1':     ['48px', { lineHeight: '1.20', letterSpacing: '-0.5px' }],
        'mdb-h2':     ['36px', { lineHeight: '1.25', letterSpacing: '-0.5px' }],
        'mdb-h3':     ['28px', { lineHeight: '1.30'  }],
        'mdb-h4':     ['22px', { lineHeight: '1.35'  }],
        'mdb-h5':     ['18px', { lineHeight: '1.40'  }],
        'mdb-body':   ['16px', { lineHeight: '1.55'  }],
        'mdb-sm':     ['14px', { lineHeight: '1.50'  }],
        'mdb-caption':['13px', { lineHeight: '1.40'  }],
        'mdb-micro':  ['12px', { lineHeight: '1.40'  }],
        'mdb-label':  ['11px', { lineHeight: '1.40', letterSpacing: '1px'   }],
      },

      // ── MongoDB Spacing ───────────────────────────────────────────── //
      spacing: {
        'mdb-xxs':  '4px',
        'mdb-xs':   '8px',
        'mdb-sm':   '12px',
        'mdb-md':   '16px',
        'mdb-lg':   '20px',
        'mdb-xl':   '24px',
        'mdb-xxl':  '32px',
        'mdb-xxxl': '40px',
        'mdb-sec-sm': '48px',
        'mdb-sec':    '64px',
        'mdb-sec-lg': '96px',
        'mdb-hero':   '120px',
      },

      // ── MongoDB Border Radius ─────────────────────────────────────── //
      borderRadius: {
        'mdb-xs':   '4px',
        'mdb-sm':   '6px',
        'mdb-md':   '8px',
        'mdb-lg':   '12px',
        'mdb-xl':   '16px',
        'mdb-xxl':  '24px',
        'mdb-full': '9999px',
      },

      // ── Shadows ───────────────────────────────────────────────────── //
      boxShadow: {
        'mdb-card': '0 1px 3px 0 rgba(0,30,43,0.08), 0 1px 2px -1px rgba(0,30,43,0.06)',
        'mdb-card-hover': '0 4px 12px 0 rgba(0,30,43,0.12), 0 2px 4px -1px rgba(0,30,43,0.08)',
        'mdb-btn': '0 1px 2px 0 rgba(0,30,43,0.10)',
      },

      // ── Animations ────────────────────────────────────────────────── //
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'typing': 'typing 1.4s infinite',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        typing:  { '0%, 80%, 100%': { transform: 'scale(0)' }, '40%': { transform: 'scale(1)' } },
      },

      // ── Breakpoints (mobile-first) ────────────────────────────────── //
      screens: {
        'xs':  '375px',   // small phones
        'sm':  '640px',   // large phones
        'md':  '768px',   // tablets
        'lg':  '1024px',  // laptops
        'xl':  '1280px',  // desktops
        '2xl': '1536px',  // large screens
      },
    },
  },
  plugins: [],
}

