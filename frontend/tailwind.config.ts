import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/hooks/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // ── Lumina Finance color tokens (from DESIGN.md) ──────────────────
      colors: {
        background:                 "#0b1326",
        surface:                    "#0b1326",
        "surface-dim":              "#0b1326",
        "surface-bright":           "#31394d",
        "surface-container-lowest": "#060e20",
        "surface-container-low":    "#131b2e",
        "surface-container":        "#171f33",
        "surface-container-high":   "#222a3d",
        "surface-container-highest":"#2d3449",
        "surface-variant":          "#2d3449",
        "on-surface":               "#dae2fd",
        "on-surface-variant":       "#bec8d2",
        "inverse-surface":          "#dae2fd",
        "inverse-on-surface":       "#283044",
        "surface-tint":             "#89ceff",
        outline:                    "#88929b",
        "outline-variant":          "#3e4850",
        primary:                    "#89ceff",
        "primary-container":        "#0ea5e9",
        "on-primary":               "#00344d",
        "on-primary-container":     "#003751",
        "inverse-primary":          "#006591",
        "primary-fixed":            "#c9e6ff",
        "primary-fixed-dim":        "#89ceff",
        secondary:                  "#ffb95f",
        "secondary-container":      "#ee9800",
        "on-secondary":             "#472a00",
        "on-secondary-container":   "#5b3800",
        "secondary-fixed":          "#ffddb8",
        "secondary-fixed-dim":      "#ffb95f",
        tertiary:                   "#ffb86e",
        "tertiary-container":       "#de8712",
        "on-tertiary":              "#492900",
        "on-tertiary-container":    "#4d2b00",
        "tertiary-fixed":           "#ffdcbd",
        "tertiary-fixed-dim":       "#ffb86e",
        error:                      "#ffb4ab",
        "error-container":          "#93000a",
        "on-error":                 "#690005",
        "on-error-container":       "#ffdad6",
      },

      // ── Typography ────────────────────────────────────────────────────
      fontFamily: {
        sans: ["var(--font-plus-jakarta)", "Plus Jakarta Sans", "sans-serif"],
      },
      fontSize: {
        "display-lg":       ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg":      ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-lg-mobile":["24px", { lineHeight: "32px", fontWeight: "600" }],
        "headline-md":      ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "body-lg":          ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "body-md":          ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-md":         ["14px", { lineHeight: "20px", letterSpacing: "0.05em", fontWeight: "600" }],
        caption:            ["12px", { lineHeight: "16px", fontWeight: "500" }],
      },

      // ── Spacing (4px rhythm) ──────────────────────────────────────────
      spacing: {
        "stack-gap-sm":       "8px",
        "stack-gap-md":       "16px",
        "stack-gap-lg":       "32px",
        "container-padding":  "24px",
        gutter:               "16px",
        unit:                 "4px",
      },

      // ── Border radius ─────────────────────────────────────────────────
      borderRadius: {
        DEFAULT: "0.25rem",
        lg:      "0.5rem",
        xl:      "0.75rem",
        "2xl":   "1.25rem",
        "3xl":   "1.5rem",
        full:    "9999px",
      },

      // ── Keyframe animations (matching Stitch code.html) ───────────────
      keyframes: {
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(30px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-left": {
          "0%":   { opacity: "0", transform: "translateX(-30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "fade-in-right": {
          "0%":   { opacity: "0", transform: "translateX(30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "bounce-dot": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-6px)" },
        },
      },
      animation: {
        "fade-in-up":    "fade-in-up 0.8s ease-out forwards",
        "fade-in-left":  "fade-in-left 0.4s ease-out forwards",
        "fade-in-right": "fade-in-right 0.4s ease-out forwards",
        "bounce-dot-1":  "bounce-dot 1s ease-in-out infinite 0ms",
        "bounce-dot-2":  "bounce-dot 1s ease-in-out infinite 200ms",
        "bounce-dot-3":  "bounce-dot 1s ease-in-out infinite 400ms",
      },
    },
  },
  plugins: [],
};

export default config;
