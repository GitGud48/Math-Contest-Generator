'use client'

import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'
import { useEffect, useState } from 'react'

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
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Prevent hydration mismatch by only rendering on client
  if (!mounted) {
    return <div className={`latex-content ${className}`}>{content}</div>
  }

  if (!content) return null

  const processContent = (text: string) => {
    return text
      .replace(/\\\[(.+?)\\\]/g, '$$$$1$$')
      .replace(/\\\((.+?)\\\)/g, '$$$1$$')
      .replace(/\\text\{([^}]+)\}/g, '\\textrm{$1}')
      .replace(/\\mathrm\{([^}]+)\}/g, '\\textrm{$1}')
  }

  const processedContent = processContent(content)

  if (inline) {
    if (processedContent.includes('$') && !processedContent.includes('$$')) {
      const mathExpression = processedContent.replace(/\$(.+?)\$/g, '$1')
      return (
        <span className={`latex-inline ${className}`}>
          <InlineMath math={mathExpression} />
        </span>
      )
    }
    return <span className={`latex-inline ${className}`}>{processedContent}</span>
  }

  // Simple block rendering
  const displayMathMatch = processedContent.match(/\$\$(.+?)\$\$/)
  
  if (displayMathMatch) {
    return (
      <div className={`latex-content ${className}`}>
        <BlockMath math={displayMathMatch[1]} />
      </div>
    )
  }

  return <div className={`latex-content ${className}`}>{processedContent}</div>
}
