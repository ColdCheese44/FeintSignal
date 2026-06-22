import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// FeintSignal frontend dev/build config. The backend runs on :8765 by default.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
