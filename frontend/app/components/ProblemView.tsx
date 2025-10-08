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

const mapStringToCategory = (str: string): Category | undefined => {
  switch (str) {
    case 'Algebra': return Category.Algebra
    case 'Combinatorics': return Category.Combinatorics
    case 'Probability': return Category.Probability
    case 'Geometry': return Category.Geometry
    case 'Number Theory': return Category.NumberTheory
    case 'Analysis': return Category.Analysis
    default: return Category.Other
  }
}

export default function ProblemView({ source }: ProblemViewProps) {
  const [problems, setProblems] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [error, setError] = useState<string | null>(null)

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
        onCategoryChange={setSelectedCategory}
        totalProblems={problems.length}
      />

      <div className="problems-grid">
        {filteredProblems.map((problem) => (
          <ProblemCard 
            key={`${source}-${problem.id}`}
            problem={problem}
            source={source}
          />
        ))}
        
        {filteredProblems.length === 0 && !loading && (
          <div className="no-problems">
            <p>No problems found for the selected category.</p>
          </div>
        )}
      </div>

      {problems.length > 0 && (
        <div className="problem-stats">
          <p>Showing {filteredProblems.length} of {problems.length} problems</p>
        </div>
      )}
    </>
  )
}
