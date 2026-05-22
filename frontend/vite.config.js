import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // All /api/* routes go to Flask backend
      '/api': 'http://127.0.0.1:5000',
      // Legacy backend routes (NOT frontend SPA routes)
      // These are actual backend endpoints, not React Router paths
      '/process': 'http://127.0.0.1:5000',
      '/analyze_one': 'http://127.0.0.1:5000',
      '/generate_email': 'http://127.0.0.1:5000',
      '/batch_outreach': 'http://127.0.0.1:5000',
      '/calculate_roi': 'http://127.0.0.1:5000',
      '/get_initial_data': 'http://127.0.0.1:5000',
      '/get_history_leads': 'http://127.0.0.1:5000',
      '/delete_lead': 'http://127.0.0.1:5000',
      '/delete_history': 'http://127.0.0.1:5000',
      '/save_settings': 'http://127.0.0.1:5000',
      '/get_settings': 'http://127.0.0.1:5000',
      '/auto_send': 'http://127.0.0.1:5000',
      '/check_session': 'http://127.0.0.1:5000',
      '/export_excel': 'http://127.0.0.1:5000',
      '/auth/google': 'http://127.0.0.1:5000'
    }
  }
})
