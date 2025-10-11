'use client'

import { useState, useEffect } from 'react'
import ProblemCard from './ProblemCard'
import CategoryFilter from './CategoryFilter'

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

interface ProblemViewProps {
  source: DatabaseSource
}

const shuffleArray = <T,>(array: T[]): T[] => {
  return [...array].sort(() => Math.random() - 0.5)
}

export default function ProblemView({ source }: ProblemViewProps) {
  const [problems, setProblems] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [error, setError] = useState<string | null>(null)
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const [isShuffled, setIsShuffled] = useState(false)

  useEffect(() => {
  console.log('Problems loaded:', problems.length)
  console.log('Current index:', currentProblemIndex)
}, [problems, currentProblemIndex])


  useEffect(() => {
  async function loadProblems() {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`/api/problems?contest=${source}`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to load problems')
      }
      
      setProblems(data.problems)
    } catch (err: any) {
      console.error('Error loading problems:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  loadProblems()
}, [source])

  const getCategories = (): string[] => {
    const categories = new Set<string>()
    problems.forEach(problem => {
      if (problem.category) {
        categories.add(problem.category)
      }
    })
    return Array.from(categories).sort()
  }

  const filteredProblems = problems.filter(problem => {
    if (selectedCategory === 'all') return true
    return problem.category === selectedCategory
  })

  const handleShuffle = () => {
    setProblems(shuffleArray(problems))
    setCurrentProblemIndex(0)
    setIsShuffled(true)
  }

  const handleNextProblem = () => {
    if (currentProblemIndex < filteredProblems.length - 1) {
      setCurrentProblemIndex(currentProblemIndex + 1)
    } else {
      setCurrentProblemIndex(0) // Loop back to first problem
    }
  }

  const handlePreviousProblem = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(currentProblemIndex - 1)
    } else {
      setCurrentProblemIndex(filteredProblems.length - 1) // Loop to last problem
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading {source.toUpperCase()} problems...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-message">
        <h3>Error Loading Problems</h3>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <>
      <CategoryFilter 
        source={source}
        categories={getCategories()}
        selectedCategory={selectedCategory}
        onCategoryChange={(cat) => {
          setSelectedCategory(cat)
          setCurrentProblemIndex(0) // Reset to first problem when category changes
        }}
        totalProblems={problems.length}
      />

      <div className="problem-controls">
        <button className="control-btn shuffle" onClick={handleShuffle}>
          🔀 Shuffle Problems
        </button>
        <div className="navigation-controls">
          <button 
            className="control-btn" 
            onClick={handlePreviousProblem}
            disabled={filteredProblems.length === 0}
          >
            ← Previous
          </button>
          <span className="problem-counter">
            {filteredProblems.length > 0 ? currentProblemIndex + 1 : 0} / {filteredProblems.length}
          </span>
          <button 
            className="control-btn" 
            onClick={handleNextProblem}
            disabled={filteredProblems.length === 0}
          >
            Next →
          </button>
        </div>
      </div>

      {filteredProblems.length > 0 && (
        <div className="problem-display">
          <ProblemCard 
            key={`${source}-${filteredProblems[currentProblemIndex].id}`}
            problem={filteredProblems[currentProblemIndex]}
            source={source}
          />
        </div>
      )}
      
      {filteredProblems.length === 0 && !loading && (
        <div className="no-problems">
          <p>No problems found for the selected category.</p>
        </div>
      )}

      {problems.length > 0 && (
        <div className="problem-stats">
          <p>Showing problem {currentProblemIndex + 1} of {filteredProblems.length}</p>
        </div>
      )}
    </>
  )
}