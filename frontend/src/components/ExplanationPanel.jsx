/**
 * ExplanationPanel Component
 * 
 * Purpose: Generate and display concept explanations
 * 
 * Features:
 * - Tone selector (simple, exam, detailed, intuitive)
 * - Generate button
 * - Display explanation text
 * - Loading and error states
 */

import React, { useState } from 'react';
import { generateExplanation } from '../services/api';

const TONES = [
  { value: 'simple', label: '😊 Simple', description: 'Easy to understand, minimal jargon' },
  { value: 'exam', label: '📝 Exam-Oriented', description: 'Formal and structured' },
  { value: 'detailed', label: '🔬 Detailed', description: 'Comprehensive and technical' },
  { value: 'intuitive', label: '💡 Intuitive', description: 'Analogies and examples' },
];

const ExplanationPanel = ({ documentId, selectedConcept }) => {
  const [selectedTone, setSelectedTone] = useState('simple');
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle explanation generation
  const handleGenerate = async () => {
    if (!selectedConcept) {
      setError('Please select a concept first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await generateExplanation(
        documentId,
        selectedConcept.id,
        selectedTone
      );
      
      setExplanation(response);
    } catch (err) {
      console.error('Error generating explanation:', err);
      setError('Failed to generate explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3 className="card-header">💬 Explanation</h3>

      {/* Tone Selector */}
      <div className="form-group">
        <label className="form-label">Select Tone</label>
        <select
          className="form-select"
          value={selectedTone}
          onChange={(e) => setSelectedTone(e.target.value)}
          disabled={loading || !selectedConcept}
        >
          {TONES.map(tone => (
            <option key={tone.value} value={tone.value}>
              {tone.label} - {tone.description}
            </option>
          ))}
        </select>
      </div>

      {/* Generate Button */}
      <button
        className="btn btn-primary"
        onClick={handleGenerate}
        disabled={loading || !selectedConcept}
        style={{ width: '100%', marginBottom: '20px' }}
      >
        {loading ? '⏳ Generating...' : '🚀 Generate Explanation'}
      </button>

      {/* Selected Concept Info */}
      {selectedConcept && !explanation && !loading && (
        <div style={{ 
          background: 'var(--bg-color)', 
          padding: '15px', 
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Ready to explain:
          </p>
          <p style={{ fontWeight: '600', fontSize: '1.05rem' }}>
            {selectedConcept.name}
          </p>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
            {selectedConcept.definition}
          </p>
        </div>
      )}

      {/* No Concept Selected */}
      {!selectedConcept && !loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px', 
          color: 'var(--text-secondary)',
          background: 'var(--bg-color)',
          borderRadius: '6px'
        }}>
          <p>👆 Select a concept from the hierarchy above</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div>
          <div className="spinner"></div>
          <p className="loading-text">Generating explanation...</p>
        </div>
      )}

      {/* Explanation Display */}
      {explanation && !loading && (
        <div>
          {/* Metadata */}
          <div style={{ 
            marginBottom: '15px', 
            padding: '12px',
            background: 'var(--bg-color)',
            borderRadius: '6px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontWeight: '600' }}>{explanation.concept_id}</span>
              <span style={{ margin: '0 10px', color: 'var(--text-secondary)' }}>•</span>
              <span className="badge badge-completed">
                {TONES.find(t => t.value === explanation.tone)?.label}
              </span>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setExplanation(null)}
              style={{ padding: '6px 12px', fontSize: '0.85rem' }}
            >
              ✕ Clear
            </button>
          </div>

          {/* Explanation Content */}
          <div className="explanation-content">
            {explanation.explanation}
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplanationPanel;
