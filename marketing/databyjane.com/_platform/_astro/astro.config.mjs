import { defineConfig } from 'astro/config';

// Port 4323: niftyedtools.com uses 4321 and veratree.os uses 4322.
export default defineConfig({
  server: {
    host: true,
    port: 4323
  },
  devToolbar: {
    enabled: false
  },
  vite: {
    server: {
      allowedHosts: ['databyjane.com', 'www.databyjane.com']
    },
    preview: {
      allowedHosts: 'all'
    }
  }
});
