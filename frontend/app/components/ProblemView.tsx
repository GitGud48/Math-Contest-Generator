'use client'

import { useState, useEffect } from 'react'
import path from 'path'
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
        
        const Database = (await import('better-sqlite3')).default
        const dbPath = path.join(process.cwd(), 'databases', `${source}.sqlite`)
        const db = new Database(dbPath, { readonly: true })
        
        let query = ''
        let rows: any[] = []
        
        // Simplified queries based on your actual database models
        if (source === 'imo') {
          query = `
            SELECT 
              p.id,
              p.statement,
              p.solution,
              p.subject_area as category,
              p.problem_number as problem_label,
              c.name as problem_competition
            FROM problems p
            LEFT JOIN contest_years cy ON p.contest_year_id = cy.id
            LEFT JOIN contests c ON cy.contest_id = c.id
            ORDER BY cy.year DESC, p.problem_number ASC
            LIMIT 50
          `
          rows = db.prepare(query).all()
        } else if (source === 'putnam') {
          query = `
            SELECT 
              p.id,
              p.statement,
              p.solution,
              p.label as problem_label,
              'Putnam' as problem_competition
            FROM problems p
            LEFT JOIN years y ON p.year_id = y.id
            ORDER BY y.year DESC, p.part ASC, p.number ASC
            LIMIT 50
          `
          rows = db.prepare(query).all()
        } else if (source === 'mit') {
          query = `
            SELECT 
              p.id,
              p.statement,
              p.solution,
              c.category,
              'MIT Integration Bee' as problem_competition
            FROM problems p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY c.category ASC, p.id ASC
            LIMIT 50
          `
          rows = db.prepare(query).all()
        }
        
        // Convert string categories to enum values
        const processedProblems = rows.map(row => ({
          ...row,
          category: row.category ? mapStringToCategory(row.category) : undefined
        }))
        
        db.close()
        setProblems(processedProblems)
      } catch (err) {
        console.error('Error loading problems:', err)
        setError(`Failed to load problems from ${source}.sqlite. Make sure the database exists.`)
        setProblems([])
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
