import type { ManifestV3Export } from "@crxjs/vite-plugin";

const manifest: ManifestV3Export = {
  manifest_version: 3,
  name: "FocusGuard",
  version: "1.0.0",
  description: "FocusGuard Browser Extension",

  action: {
    default_popup: "index.html",
  },

  background: {
    service_worker: "src/background/background.ts",
    type: "module",
  },

  options_page: "options.html",

  permissions: ["storage", "tabs","idle"],

  host_permissions: ["http://localhost:8000/*"],
};

export default manifest;