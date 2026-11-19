import { defineConfig } from 'astro/config';

export default defineConfig({
  server: {
    host: true,
    port: 4321
  },
  devToolbar: {
    enabled: false
  },
  vite: {
    server: {
      allowedHosts: ['niftyedtools.com', 'www.niftyedtools.com'],
      proxy: {
        '/api': {
          target: 'http://api:8000',
          rewrite: (path) => path.replace(/^\/api/, ''),
        }
      }
    },
    preview: {
      allowedHosts: 'all'
    }
  }
});
