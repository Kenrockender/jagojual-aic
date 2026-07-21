import type { Config } from "tailwindcss";

/**
 * Palet & tipografi JagoJual.
 *
 * Menjauh dari default Tailwind (slate/indigo) secara sengaja: produk ini ruang
 * LATIHAN untuk pramuniaga & sales showroom, bukan dashboard SaaS. Nuansanya kertas
 * hangat + tinta, dengan satu aksen bata sebagai satu-satunya warna yang menuntut
 * perhatian — supaya yang menonjol adalah percakapan dan skor, bukan hiasan.
 *
 * Font memakai stack sistem (tanpa unduhan eksternal) supaya aplikasi tetap tampil
 * benar saat panitia menjalankannya lewat docker compose tanpa internet.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kertas: { DEFAULT: "#FBF9F6", tua: "#F3EEE7" },
        tinta: { DEFAULT: "#1B1917", lembut: "#57534E", samar: "#8C837A" },
        bata: { DEFAULT: "#B2442B", tua: "#8C3520", muda: "#F6E6E0" },
        garis: { DEFAULT: "#E6DED3", tua: "#D5C9B9" },
        kuat: "#15803D",
        sedang: "#B45309",
        lemah: "#B4402B",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto",
          "Helvetica Neue", "Arial", "sans-serif",
        ],
        display: ["ui-serif", "Georgia", "Cambria", "Times New Roman", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
