// components/SimpleLatexRenderer.js
import 'katex/dist/katex.min.css';
import Latex from 'react-latex-next';

export default function LatexRenderer({ latex, className = '' }) {
  if (!latex) return null;
  
  try {
    return (
      <div className={`latex-content ${className}`}>
        <Latex>{latex}</Latex>
      </div>
    );
  } catch (error) {
    console.error('LaTeX rendering error:', error);
    return (
      <div className={`latex-error ${className}`} style={{ color: 'red' }}>
        Failed to render LaTeX content
      </div>
    );
  }
}
