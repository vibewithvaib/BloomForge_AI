/**
 * QuizPanel Component
 * 
 * Purpose: Generate and display quizzes
 * 
 * Features:
 * - Difficulty selector (easy, medium, hard)
 * - Generate button
 * - Display exactly 10 questions
 * - Show Bloom's level and difficulty score for each question
 * - Questions ranked by difficulty
 */

import React, { useState } from 'react';
import { generateQuiz } from '../services/api';

const DIFFICULTIES = [
  { value: 'easy', label: '🟢 Easy', description: 'Remember & Understand' },
  { value: 'medium', label: '🟡 Medium', description: 'Apply & Analyze' },
  { value: 'hard', label: '🔴 Hard', description: 'Evaluate & Create' },
];

const BLOOMS_COLORS = {
  'Remember': '#3498db',
  'Understand': '#2ecc71',
  'Apply': '#f39c12',
  'Analyze': '#e67e22',
  'Evaluate': '#e74c3c',
  'Create': '#9b59b6',
};

const QuizPanel = ({ documentId, selectedConcept }) => {
  const [selectedDifficulty, setSelectedDifficulty] = useState('medium');
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle quiz generation
  const handleGenerate = async () => {
    if (!selectedConcept) {
      setError('Please select a concept first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await generateQuiz(
        documentId,
        selectedConcept.id,
        selectedDifficulty
      );
      
      setQuiz(response);
    } catch (err) {
      console.error('Error generating quiz:', err);
      setError('Failed to generate quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Render a single question
  const renderQuestion = (question, index) => {
    return (
      <div key={question.id} className="question-card">
        {/* Question Number */}
        <div className="question-number">
          Question {index + 1} of 10
        </div>

        {/* Question Text */}
        <div className="question-text">
          {question.question}
        </div>

        {/* Metadata */}
        <div className="question-meta">
          {/* Bloom's Level Badge */}
          <span 
            className="badge"
            style={{ 
              backgroundColor: BLOOMS_COLORS[question.blooms_level] || '#95a5a6',
              color: 'white'
            }}
          >
            {question.blooms_level}
          </span>

          {/* Difficulty Score */}
          <span className="badge" style={{ backgroundColor: '#ecf0f1', color: '#2c3e50' }}>
            Difficulty: {question.difficulty_score}/10
          </span>

          {/* Concepts Tested */}
          {question.concepts && question.concepts.length > 0 && (
            <span className="badge" style={{ backgroundColor: '#ecf0f1', color: '#2c3e50' }}>
              Concepts: {question.concepts.join(', ')}
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="card">
      <h3 className="card-header">📝 Quiz Generator</h3>

      {/* Difficulty Selector */}
      <div className="form-group">
        <label className="form-label">Select Difficulty</label>
        <select
          className="form-select"
          value={selectedDifficulty}
          onChange={(e) => setSelectedDifficulty(e.target.value)}
          disabled={loading || !selectedConcept}
        >
          {DIFFICULTIES.map(diff => (
            <option key={diff.value} value={diff.value}>
              {diff.label} - {diff.description}
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
        {loading ? '⏳ Generating...' : '🎯 Generate Quiz (10 Questions)'}
      </button>

      {/* Selected Concept Info */}
      {selectedConcept && !quiz && !loading && (
        <div style={{ 
          background: 'var(--bg-color)', 
          padding: '15px', 
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Ready to quiz on:
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
          <p className="loading-text">
            Generating quiz questions...
            <br />
            <span style={{ fontSize: '0.9rem' }}>
              This includes AI generation and validation
            </span>
          </p>
        </div>
      )}

      {/* Quiz Display */}
      {quiz && !loading && (
        <div>
          {/* Quiz Header */}
          <div style={{ 
            marginBottom: '20px', 
            padding: '15px',
            background: 'var(--bg-color)',
            borderRadius: '6px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div>
                <span style={{ fontWeight: '600' }}>{quiz.concept_id}</span>
                <span style={{ margin: '0 10px', color: 'var(--text-secondary)' }}>•</span>
                <span className="badge badge-completed">
                  {DIFFICULTIES.find(d => d.value === quiz.difficulty)?.label}
                </span>
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => setQuiz(null)}
                style={{ padding: '6px 12px', fontSize: '0.85rem' }}
              >
                ✕ Clear
              </button>
            </div>
            
            {/* Validation Status */}
            {quiz.validation_passed ? (
              <div style={{ color: 'var(--secondary-color)', fontSize: '0.9rem' }}>
                ✅ Validated • {quiz.questions.length} questions
              </div>
            ) : (
              <div style={{ color: 'var(--warning-color)', fontSize: '0.9rem' }}>
                ⚠️ Validation warnings
              </div>
            )}

            {/* Validation Feedback */}
            {quiz.validation_feedback && (
              <div style={{ 
                marginTop: '10px', 
                padding: '10px',
                background: '#fff8e1',
                borderRadius: '4px',
                fontSize: '0.85rem',
                color: '#f57c00'
              }}>
                {quiz.validation_feedback}
              </div>
            )}
          </div>

          {/* Questions */}
          <div>
            {quiz.questions && quiz.questions.map((question, index) => 
              renderQuestion(question, index)
            )}
          </div>

          {/* Bloom's Level Legend */}
          <div style={{ 
            marginTop: '20px', 
            padding: '15px',
            background: 'var(--bg-color)',
            borderRadius: '6px'
          }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '10px' }}>
              📊 Bloom's Taxonomy Levels
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {Object.entries(BLOOMS_COLORS).map(([level, color]) => (
                <span 
                  key={level}
                  className="badge"
                  style={{ backgroundColor: color, color: 'white' }}
                >
                  {level}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizPanel;
