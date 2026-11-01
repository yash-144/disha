import React from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App'
import { AppProvider } from './context/AppContext'
import { queryClient } from './lib/api/queryClient'
import { LanguageProvider } from './i18n'
import { SessionProvider } from './lib/auth/SessionProvider'

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <SessionProvider>
          <AppProvider>
            <App />
          </AppProvider>
        </SessionProvider>
      </LanguageProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
