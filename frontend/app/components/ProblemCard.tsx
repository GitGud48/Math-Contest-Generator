'use client'

import { useState } from 'react'
import LaTeXRenderer from './LaTeXRenderer'

type DatabaseSource = 'imo' | 'putnam' | 'mit'

enum Category {
  Algebra = 'Algebra',
  Combinatorics = 'Combinatorics',
  Probability = 'Probability',
  Geometry = 'Geometry',
  NumberTheory = 'Number Theory',
  Analysis = 'Analysis',
  Other = 'Other'
}

interface Problem {
  id: number
  statement: string
  solution?: string
  category?: Category
  problem_label?: number
  problem_competition?: string
}

interface ProblemCardProps {
  problem: Problem
  source: DatabaseSource
}

export default function ProblemCard({ problem, source }: ProblemCardProps) {
  const [showSolution, setShowSolution] = useState(false)

  const getProblemTitle = () => {
    if (problem.problem_label) {
      return `Problem ${problem.problem_label} ${problem.problem_competition ? `(${problem.problem_competition})` : ''}`
    }
    return `Problem #${problem.id}`
  }

  const getProblemMeta = (): string[] => {  // Add explicit return type
    const meta: string[] = []  // Add explicit type annotation
    if (problem.category) meta.push(problem.category)
    if (problem.problem_competition) meta.push(problem.problem_competition)
    return meta
  }

  return (
    <div className="problem-card">
      <div className="problem-header">
        <h3 className="problem-title">{getProblemTitle()}</h3>
        
        <div className="problem-meta">
          {getProblemMeta().map((item, index) => (
            <span key={index} className="meta-tag">
              {item}
            </span>
          ))}
        </div>
      </div>

      <div className="problem-content">
        <div className="problem-statement">
          <h4>Problem Statement</h4>
          <LaTeXRenderer content={problem.statement} />
        </div>

        {problem.solution && (
          <div className="problem-solution">
            <div className="solution-header">
              <h4>Solution</h4>
              <button 
                className={`toggle-solution ${showSolution ? 'active' : ''}`}
                onClick={() => setShowSolution(!showSolution)}
              >
                {showSolution ? 'Hide Solution' : 'Show Solution'}
              </button>
            </div>
            
            {showSolution && (
              <div className="solution-content">
                <LaTeXRenderer content={problem.solution} />
              </div>
            )}
          </div>
        )}
      </div>

      <div className="problem-footer">
        <div className="problem-actions">
          <button className="action-btn bookmark">
            ⭐ Bookmark
          </button>
          <button className="action-btn share">
            🔗 Share
          </button>
        </div>
      </div>
    </div>
  )
}