import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Math Problem Generator',
  description: 'Generate and solve mathematical competition problems from IMO, Putnam, and MIT',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <div className={inter.className}>
        <main className="main">
          {children}
        </main>
      </div>
    </>
  )
}