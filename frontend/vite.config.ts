/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The API runs on Django; the proxy keeps the browser on one origin in development.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
