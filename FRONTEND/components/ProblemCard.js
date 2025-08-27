import { useState } from 'react';
import LaTeXRenderer from './LaTeXRenderer';

const categoryColors = {
  'Geometry': 'bg-blue-100 text-blue-800',
  'Algebra': 'bg-red-100 text-red-800',
  'Number Theory': 'bg-purple-100 text-purple-800',
  'Combinatorics': 'bg-yellow-100 text-yellow-800',
  'Mixed': 'bg-gray-100 text-gray-800',
};

export default function ProblemCard({ problem }) {
  const [showSolution, setShowSolution] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="bg-gray-800 text-white p-4 rounded-t-lg">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold">
            {problem.contest} {problem.year} - {problem.label}
          </h3>
          {problem.subject && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              categoryColors[problem.subject] || 'bg-gray-100 text-gray-800'
            }`}>
              {problem.subject}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Problem Statement */}
        <div className="mb-4">
          <h4 className="font-medium text-gray-800 mb-2">Problem Statement:</h4>
          <div className="prose max-w-none">
            <LaTeXRenderer 
              latex={problem.statement} 
              className="problem-statement"
            />
          </div>
        </div>

        {/* Solution Toggle */}
        {problem.solution && (
          <div>
            <button
              onClick={() => setShowSolution(!showSolution)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors mb-4"
            >
              💡 {showSolution ? 'Hide Solution' : 'View Solution'}
            </button>

            {showSolution && (
              <div className="bg-green-50 border-l-4 border-green-400 p-4 rounded">
                <h4 className="font-medium text-gray-800 mb-2">Solution:</h4>
                <div className="prose max-w-none">
                  <LaTeXRenderer 
                    latex={problem.solution} 
                    className="problem-solution"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
