/**
 * Document View Page (MAIN INTERACTION PAGE)
 * 
 * Purpose: Core interaction screen for a completed document
 * 
 * Structure:
 * - Section A: Concept Hierarchy (left/top)
 * - Section B: Explanation Panel (right/bottom)
 * - Section C: Quiz Panel (right/bottom)
 * 
 * Features:
 * - Display concept hierarchy
 * - Select concepts
 * - Generate explanations
 * - Generate quizzes
 * - Loading and error states
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDocument } from '../services/api';
import ConceptTree from '../components/ConceptTree';
import ExplanationPanel from '../components/ExplanationPanel';
import QuizPanel from '../components/QuizPanel';

const DocumentView = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch document data
  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await getDocument(documentId);
        
        // Check if document is still processing
        if (data.status === 'processing') {
          // Poll every 3 seconds
          setTimeout(() => {
            fetchDocument();
          }, 3000);
          return;
        }
        
        if (data.status === 'failed') {
          setError('Document processing failed. Please try uploading again.');
          setLoading(false);
          return;
        }
        
        setDocument(data);
        setConcepts(data.concepts || []);
        
        // Auto-select first concept if available
        if (data.concepts && data.concepts.length > 0) {
          setSelectedConcept(data.concepts[0]);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching document:', err);
        setError('Failed to load document. Please try again.');
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  // Handle concept selection
  const handleSelectConcept = (concept) => {
    setSelectedConcept(concept);
  };

  // Handle back to dashboard
  const handleBackToDashboard = () => {
    navigate('/');
  };

  return (
    <div>
      {/* Header */}
      <div className="header">
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>📖 Document Viewer</h1>
              <p>
                Document ID: {documentId.substring(0, 16)}...
              </p>
            </div>
            <button className="btn btn-secondary" onClick={handleBackToDashboard}>
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container">
        {/* Loading State */}
        {loading && (
          <div className="card">
            <div className="spinner"></div>
            <p className="loading-text">
              {document?.status === 'processing' 
                ? 'Document is still processing... Please wait.'
                : 'Loading document...'}
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Document View */}
        {!loading && !error && document && (
          <div>
            {/* Document Info */}
            <div className="card" style={{ marginBottom: '30px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <h2 style={{ marginBottom: '10px' }}>
                    {concepts.length} Concepts Extracted
                  </h2>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    Created: {new Date(document.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="badge badge-completed">
                  {document.status}
                </span>
              </div>
            </div>

            {/* Main Layout: 2 columns on desktop, stacked on mobile */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
              gap: '20px',
              alignItems: 'start'
            }}>
              {/* LEFT COLUMN: Concept Hierarchy */}
              <div>
                <ConceptTree
                  concepts={concepts}
                  selectedConceptId={selectedConcept?.id}
                  onSelectConcept={handleSelectConcept}
                />

                {/* Selected Concept Details */}
                {selectedConcept && (
                  <div className="card" style={{ marginTop: '20px' }}>
                    <h3 className="card-header">🎯 Selected Concept</h3>
                    <div style={{ 
                      background: 'var(--bg-color)', 
                      padding: '15px', 
                      borderRadius: '6px' 
                    }}>
                      <h4 style={{ marginBottom: '10px', fontSize: '1.1rem' }}>
                        {selectedConcept.name}
                      </h4>
                      <p style={{ marginBottom: '12px', fontSize: '0.95rem' }}>
                        {selectedConcept.definition}
                      </p>
                      
                      <div style={{ 
                        display: 'flex', 
                        gap: '10px', 
                        flexWrap: 'wrap',
                        marginTop: '12px'
                      }}>
                        <span className="badge" style={{ background: '#3498db', color: 'white' }}>
                          ID: {selectedConcept.id}
                        </span>
                        <span className="badge" style={{ background: '#2ecc71', color: 'white' }}>
                          Level {selectedConcept.level}
                        </span>
                        <span className="badge" style={{ background: '#f39c12', color: 'white' }}>
                          Importance: {(selectedConcept.importance * 100).toFixed(0)}%
                        </span>
                      </div>

                      {selectedConcept.prerequisites && selectedConcept.prerequisites.length > 0 && (
                        <div style={{ marginTop: '12px' }}>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            <strong>Prerequisites:</strong> {selectedConcept.prerequisites.join(', ')}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* RIGHT COLUMN: Explanation & Quiz Panels */}
              <div>
                {/* Explanation Panel */}
                <ExplanationPanel
                  documentId={documentId}
                  selectedConcept={selectedConcept}
                />

                {/* Quiz Panel */}
                <div style={{ marginTop: '20px' }}>
                  <QuizPanel
                    documentId={documentId}
                    selectedConcept={selectedConcept}
                  />
                </div>
              </div>
            </div>

            {/* Empty State - No Concepts */}
            {concepts.length === 0 && (
              <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
                <h3 style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                  No concepts found in this document
                </h3>
                <button className="btn btn-primary" onClick={handleBackToDashboard}>
                  Back to Dashboard
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentView;
