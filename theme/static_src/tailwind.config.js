/**
 * «Нескучные выходные» — Tailwind config
 *
 * Палитра построена вокруг бирюзы: она доминирует на сайте,
 * коралл отдан конверсии (кнопки, цены), солнечный жёлтый —
 * бейджам и акцентам на тёмном.
 *
 * Правила, которые нельзя нарушать (проверены по контрасту):
 *   • белый текст на turquoise — запрещён (2.25:1), для текста берём ink
 *   • кнопки с белым текстом — turquoise-700 (4.5:1) или coral (крупный жирный)
 *   • coral как текст на белом — только через coral-deep (4.6:1)
 *
 * Те же значения продублированы в theme/static/trips/admin.css — это два разных
 * бандла, оба собираются из этого файла.
 */
module.exports = {
  content: [
    "./src/styles.css",
    "../../trips/templates/**/*.html",
    "../../static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // ── основная бирюза ──────────────────────────────────
        turquoise: "#00C2B0",
        "turquoise-600": "#00A796",
        "turquoise-700": "#00857A",
        "turquoise-300": "#33D3C3",

        // ── мята ────────────────────────────────────────────
        "mint-300": "#6FE3D6",
        "mint-100": "#C6F4EC",
        "mint-wash": "#E9FBF8",
        "mint-line": "#B4EDE2",

        // ── чернила ─────────────────────────────────────────
        ink: "#063D3A",
        "ink-80": "#0B5A55",
        "ink-60": "#3E7C77",

        // ── акценты ─────────────────────────────────────────
        coral: "#FF6B4A",
        "coral-soft": "#FF8A5B",
        "coral-deep": "#C93C1B",
        sun: "#FFC145",
        "sun-deep": "#E09B00",

        white: "#FFFFFF",
      },

      fontFamily: {
        serif: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },

      letterSpacing: {
        wide: "0.08em",
        wider: "0.14em",
        widest: "0.22em",
        mega: "0.28em",
      },

      lineHeight: {
        relaxed: "1.65",
        airy: "1.8",
      },

      borderRadius: {
        card: "20px",
        soft: "16px",
        pill: "999px",
      },

      boxShadow: {
        zen: "0 10px 40px rgba(0,132,122,0.10)",
        "zen-lg": "0 20px 60px rgba(0,132,122,0.14)",
        lift: "0 14px 28px rgba(0,132,122,0.16)",
        glow: "0 0 0 4px rgba(0,194,176,0.25)",
        ink: "0 12px 40px rgba(6,61,58,0.28)",
      },

      maxWidth: {
        prose: "54ch",
      },

      keyframes: {
        kenburns: {
          from: { transform: "scale(1.03)" },
          to: { transform: "scale(1.17)" },
        },
        reveal: {
          from: { opacity: "0", transform: "translateY(34px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        arrowfloat: {
          "0%,100%": { transform: "translateY(0)", opacity: ".45" },
          "50%": { transform: "translateY(10px)", opacity: "1" },
        },
        marquee: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-50%)" },
        },
        ringpulse: {
          "0%": { boxShadow: "0 0 0 0 rgba(0,194,176,.45)" },
          "70%": { boxShadow: "0 0 0 12px rgba(0,194,176,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(0,194,176,0)" },
        },
      },

      animation: {
        kenburns: "kenburns 24s ease-in-out infinite alternate",
        reveal: "reveal 1.1s cubic-bezier(.2,.7,.2,1) both",
        arrow: "arrowfloat 2.6s ease-in-out infinite",
        marquee: "marquee 38s linear infinite",
        pulse: "ringpulse 2.4s ease-out infinite",
      },
    },
  },
  plugins: [],
};