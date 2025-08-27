import { useState, useEffect } from 'react';
import useSWR from 'swr';
import ProblemCard from '../components/ProblemCard';
import DatabaseSelector from '../components/DatabaseSelector';
import CategoryFilter from '../components/CategoryFilter';

const fetcher = (url) => fetch(url).then((res) => res.json());

export default function Home() {
  const [selectedDatabase, setSelectedDatabase] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [filteredProblems, setFilteredProblems] = useState([]);

  // Fetch databases
  const { data: databasesData } = useSWR('/api/databases', fetcher);

  // Fetch problems when database changes
  const { data: problemsData, error, isLoading } = useSWR(
    selectedDatabase ? `/api/problems?database=${selectedDatabase}&limit=50` : null,
    fetcher
  );

  // Filter problems by category
  useEffect(() => {
    if (problemsData?.problems) {
      if (selectedCategory === 'all') {
        setFilteredProblems(problemsData.problems);
      } else {
        setFilteredProblems(
          problemsData.problems.filter(
            (problem) => problem.subject === selectedCategory
          )
        );
      }
    }
  }, [problemsData, selectedCategory]);

  const getRandomProblem = () => {
    if (filteredProblems.length > 0) {
      const randomIndex = Math.floor(Math.random() * filteredProblems.length);
      const randomProblem = filteredProblems[randomIndex];
      setFilteredProblems([randomProblem]);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8 text-blue-600">
        🧮 Math Contest Problems
      </h1>

      {/* Controls */}
      <div className="flex flex-wrap justify-center items-center gap-4 mb-8 p-6 bg-gray-50 rounded-lg">
        <DatabaseSelector
          databases={databasesData?.databases || []}
          selectedDatabase={selectedDatabase}
          onDatabaseChange={setSelectedDatabase}
        />
        
        <CategoryFilter
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
        />
        
        <button
          onClick={getRandomProblem}
          disabled={filteredProblems.length === 0}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          🎲 Random Problem
        </button>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="text-lg text-gray-600">📚 Loading problems...</div>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <div className="text-red-600 bg-red-50 p-4 rounded-lg">
            ❌ Error loading problems: {error.message}
          </div>
        </div>
      )}

      {filteredProblems.length > 0 && (
        <>
          <div className="text-center mb-6 text-gray-600">
            Showing {filteredProblems.length} problems
            {selectedCategory !== 'all' && ` in ${selectedCategory}`}
          </div>
          
          <div className="space-y-6">
            {filteredProblems.map((problem, index) => (
              <ProblemCard key={`${problem.source}-${problem.label}-${index}`} problem={problem} />
            ))}
          </div>
        </>
      )}

      {selectedDatabase && !isLoading && filteredProblems.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-600">
            No problems found for the selected filters.
          </div>
        </div>
      )}
    </div>
  );
}
