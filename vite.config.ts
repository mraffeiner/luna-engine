import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit(), tailwindcss()],
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:5000',
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, ''),
				configure: (proxy) => {
					proxy.on('error', (err, req, res) => {
						console.error('Proxy error:', err);
						if (res.writeHead && !res.headersSent) {
							res.writeHead(500, { 'Content-Type': 'application/json' });
						}
						res.end(JSON.stringify({ error: 'Proxy unavailable, please try again later.' }));
					});
				}
			}
		}
	}
});
