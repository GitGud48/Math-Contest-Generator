import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { MathJaxContext } from 'better-react-mathjax'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Math Problem Generator',
  description: 'Generate and solve mathematical competition problems from IMO, Putnam, and MIT',
}

export default function RootLayout({ children }) {
  const config = {
    loader: { 
      load: [
      '[tex]/ams',        
      '[tex]/color',      
      '[tex]/html',       
      '[tex]/boldsymbol', 
      '[tex]/mathtools'   
      ] 
    },
    tex: {
      packages: { 
        '[+]': ['ams', 'color', 'html', 'boldsymbol', 'mathtools'] 
      },
      inlineMath: [
        ['$', '$'],
        ['\\(', '\\)']
      ],
      displayMath: [
        ['$$', '$$'],
        ['\\[', '\\]']
      ]
    }
  }

  return (
    <html>
      <body>
        <MathJaxContext config={config}>
          {children}
        </MathJaxContext>
      </body>
    </html>
  )
}
