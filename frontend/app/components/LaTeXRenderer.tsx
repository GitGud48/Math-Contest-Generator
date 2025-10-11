'use client'

import { MathJax } from 'better-react-mathjax'
import { useState, useEffect } from 'react'

interface LaTeXRendererProps {
  content: string
  inline?: boolean
  className?: string
}

function stripUnsupportedLatex(content: string): string {
  // Remove enumerate/itemize environments and their content markers
  let cleaned = content
    .replace(/\\begin\{enumerate\}/g, '')
    .replace(/\\end\{enumerate\}/g, '')
    .replace(/\\begin\{itemize\}/g, '')
    .replace(/\\end\{itemize\}/g, '')
    .replace(/\\item/g, '')
    .replace(/\\textbf\{([^}]+)\}/g, '$1')  // Remove bold but keep content
    .replace(/\\textit\{([^}]+)\}/g, '$1')  // Remove italic but keep content
    .replace(/\\section\{[^}]+\}/g, '')
    .replace(/\\subsection\{[^}]+\}/g, '')
    .replace(/\\noindent/g, '')
    .replace(/\\vspace\{[^}]+\}/g, '')
    .replace(/\\hspace\{[^}]+\}/g, '')
    .replace(/\\emph\{([^}]+)\}/g, '$1')  // Remove emphasis but keep content
    .replace(/\\begin\{align\*\}/g, '\\begin{align}')  // Convert align* to align
    .replace(/\\end\{align\*\}/g, '\\end{align}')
    .replace(/\\begin\{cases}/g, '\\begin{align}')  // Convert cases to align
    .replace(/\\end\{cases}/g, '\\end{align}')
  
  return cleaned
}

export default function LaTeXRenderer({ 
  content, 
  inline = false, 
  className = '' 
}: LaTeXRendererProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  content = stripUnsupportedLatex(content)

  if (!isClient) {
    return inline ? (
      <span className={`latex-inline ${className}`}>{content}</span>
    ) : (
      <div className={`latex-content ${className}`}>{content}</div>
    )
  }

  return (
    <MathJax 
      inline={inline}
      className={inline ? `latex-inline ${className}` : `latex-content ${className}`}
      hideUntilTypeset='first'
      dynamic={false}
    >
      {content}
    </MathJax>
  )
}

