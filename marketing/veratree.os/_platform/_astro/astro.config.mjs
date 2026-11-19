import { defineConfig } from 'astro/config';

export default defineConfig({
  base: '/veratreeos',
  server: {
    host: true,
    port: 4322
  },
  devToolbar: {
    enabled: false
  },
  vite: {
    server: {
      allowedHosts: ['niftyedtools.com', 'www.niftyedtools.com', 'veratree.os', 'www.veratree.os']
    }
  }
});
