'use client'

import 'katex/dist/katex.min.css'
import { useEffect, useRef, useState } from 'react'
import renderMathInElement from 'katex/dist/contrib/auto-render'

interface LaTeXRendererProps {
  content: string
  inline?: boolean
  className?: string
}

export default function LaTeXRenderer({ 
  content, 
  inline = false, 
  className = '' 
}: LaTeXRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isClient, setIsClient] = useState(false)

  // Handle client-side mounting
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Render math whenever content changes
  useEffect(() => {
    if (!isClient || !containerRef.current) return

    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      if (containerRef.current) {
        renderMathInElement(containerRef.current, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '\\[', right: '\\]', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false }
          ],
          throwOnError: false,
          strict: false
        })
      }
    }, 10)

    return () => clearTimeout(timer)
  }, [content, isClient])

  // Prevent hydration mismatch
  if (!isClient) {
    return <div className={`latex-content ${className}`}>{content}</div>
  }

  if (inline) {
    return (
      <span 
        ref={containerRef as any}
        className={`latex-inline ${className}`}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    )
  }

  return (
    <div 
      ref={containerRef}
      className={`latex-content ${className}`}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  )
}
