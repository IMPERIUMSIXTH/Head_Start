import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import './flip-card.css'
import { AuthProvider } from './context/AuthContext'
import Chatbot from './components/Chatbot'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HeadStart - AI Powered Learning',
  description: 'Personalized learning recommendations powered by AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {children}
          <Chatbot />
        </AuthProvider>
      </body>
    </html>
  )
}
