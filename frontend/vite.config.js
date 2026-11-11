// import vue from '@vitejs/plugin-vue'
// import { defineConfig } from 'vite'

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [vue()],
// })


import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],

    server: {
        host: '127.0.0.1',
        port: 5173,

        // 将 API 请求转发到 Django
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8008',
                changeOrigin: true
            }
        }
    }
})