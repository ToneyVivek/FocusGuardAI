import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./manifest.js";

export default defineConfig({
  plugins: [
    react(),
    crx({ manifest }),
  ],
});