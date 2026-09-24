import { fileURLToPath, URL } from "node:url";
import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget =
    process.env.VITE_BACKEND_PROXY_TARGET || env.VITE_BACKEND_PROXY_TARGET || "http://localhost:8099";
  const wsTarget = backendTarget.replace(/^http/, "ws");
  const isGitHubPages = process.env.GITHUB_PAGES === "true";

  return {
    base: isGitHubPages ? "/aily/app/" : "/",
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    build: isGitHubPages
      ? {
          outDir: fileURLToPath(new URL("../docs/app", import.meta.url)),
          emptyOutDir: true,
        }
      : undefined,
    server: {
      host: "127.0.0.1",
      port: 5199,
      proxy: {
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
        "/ws": {
          target: wsTarget,
          ws: true,
          changeOrigin: true,
        },
      },
    },
  };
});
