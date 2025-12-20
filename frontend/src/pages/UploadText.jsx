/**
 * Upload Text Page
 * 
 * Purpose: Allow user to upload new educational content
 * 
 * Features:
 * - Large textarea for educational text input
 * - Validation (minimum 100 characters)
 * - Loading state during submission
 * - Redirect to Dashboard after successful upload
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createDocument } from '../services/api';

const UploadText = () => {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const MIN_TEXT_LENGTH = 100;

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate
    if (text.trim().length < MIN_TEXT_LENGTH) {
      setError(`Educational text must be at least ${MIN_TEXT_LENGTH} characters long.`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create document
      const response = await createDocument(text);
      
      console.log('Document created:', response);
      
      // Redirect to dashboard
      navigate('/', { 
        state: { 
          message: `Document ${response.document_id.substring(0, 8)}... is being processed!` 
        } 
      });
      
    } catch (err) {
      console.error('Error creating document:', err);
      setError('Failed to upload document. Please try again.');
      setLoading(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate('/');
  };

  return (
    <div>
      {/* Header */}
      <div className="header">
        <div className="container">
          <h1>📝 Upload Educational Text</h1>
          <p>Paste your educational content to extract concepts and create quizzes</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container">
        <div className="card" style={{ maxWidth: '900px', margin: '0 auto' }}>
          
          {/* Instructions */}
          <div style={{ 
            background: 'var(--bg-color)', 
            padding: '15px', 
            borderRadius: '6px',
            marginBottom: '20px'
          }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '10px' }}>
              📚 Instructions
            </h3>
            <ul style={{ marginLeft: '20px', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
              <li>Paste educational content (textbook chapters, articles, lecture notes, etc.)</li>
              <li>Minimum {MIN_TEXT_LENGTH} characters required</li>
              <li>The AI will extract key concepts and build a learning hierarchy</li>
              <li>Processing usually takes 30-60 seconds</li>
            </ul>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">
                Educational Text *
              </label>
              <textarea
                className="form-textarea"
                placeholder="Paste your educational content here...&#10;&#10;Example:&#10;Process scheduling is a fundamental concept in operating systems. It determines which process runs at any given time. The CPU scheduler selects from among the processes in memory that are ready to execute, and allocates the CPU to one of them..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={loading}
                style={{ minHeight: '400px' }}
              />
              <div style={{ 
                fontSize: '0.85rem', 
                color: 'var(--text-secondary)', 
                marginTop: '8px' 
              }}>
                {text.length} / {MIN_TEXT_LENGTH} characters minimum
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleCancel}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || text.trim().length < MIN_TEXT_LENGTH}
              >
                {loading ? '⏳ Processing...' : '🚀 Process Text'}
              </button>
            </div>
          </form>

          {/* Loading State */}
          {loading && (
            <div style={{ marginTop: '30px' }}>
              <div className="spinner"></div>
              <p className="loading-text">
                Uploading and analyzing your educational text...
                <br />
                <span style={{ fontSize: '0.9rem' }}>This may take up to a minute</span>
              </p>
            </div>
          )}
        </div>

        {/* Example Section */}
        {!loading && (
          <div className="card" style={{ maxWidth: '900px', margin: '30px auto 0', background: 'var(--bg-color)' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '15px' }}>
              💡 Example Topics
            </h3>
            <div style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
              <p style={{ marginBottom: '10px' }}>You can upload content about:</p>
              <ul style={{ marginLeft: '20px' }}>
                <li>Computer Science (algorithms, data structures, operating systems)</li>
                <li>Mathematics (calculus, linear algebra, statistics)</li>
                <li>Physics (mechanics, thermodynamics, quantum physics)</li>
                <li>Biology (cell biology, genetics, ecology)</li>
                <li>Any other educational subject!</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadText;
