/**
 * Dashboard Page
 * 
 * Purpose: Show all documents uploaded by the user
 * 
 * Features:
 * - List all documents with status badges
 * - "Upload New Text" button
 * - "Open Document" button (only for completed documents)
 * - Auto-refresh to check for processing completion
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserDocuments } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user's documents
  const fetchDocuments = async () => {
    try {
      setError(null);
      const data = await getUserDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Auto-refresh every 5 seconds if there are processing documents
  useEffect(() => {
    const hasProcessing = documents.some(doc => doc.status === 'processing');
    
    if (hasProcessing) {
      const interval = setInterval(() => {
        fetchDocuments();
      }, 5000);  // Poll every 5 seconds
      
      return () => clearInterval(interval);
    }
  }, [documents]);

  // Navigate to upload page
  const handleUploadNew = () => {
    navigate('/upload');
  };

  // Navigate to document view
  const handleOpenDocument = (documentId) => {
    navigate(`/document/${documentId}`);
  };

  // Get status badge class
  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'completed':
        return 'badge badge-completed';
      case 'processing':
        return 'badge badge-processing';
      case 'failed':
        return 'badge badge-failed';
      default:
        return 'badge';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="header">
        <div className="container">
          <h1>🎓 Autonomous Knowledge Extractor</h1>
          <p>Transform educational texts into interactive learning experiences</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container">
        {/* Action Bar */}
        <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>My Documents</h2>
          <button className="btn btn-primary" onClick={handleUploadNew}>
            ➕ Upload New Text
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div>
            <div className="spinner"></div>
            <p className="loading-text">Loading your documents...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && documents.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
            <h3 style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
              No documents yet
            </h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
              Upload your first educational text to get started
            </p>
            <button className="btn btn-primary" onClick={handleUploadNew}>
              Upload Educational Text
            </button>
          </div>
        )}

        {/* Document List */}
        {!loading && !error && documents.length > 0 && (
          <div className="grid grid-2">
            {documents.map((doc) => (
              <div key={doc.document_id} className="card">
                {/* Document Header */}
                <div style={{ marginBottom: '15px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>
                        Document {doc.document_id.substring(0, 8)}...
                      </h3>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        Created: {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={getStatusBadgeClass(doc.status)}>
                      {doc.status}
                    </span>
                  </div>
                </div>

                {/* Document Stats */}
                {doc.status === 'completed' && doc.concepts && (
                  <div style={{ 
                    background: 'var(--bg-color)', 
                    padding: '12px', 
                    borderRadius: '6px',
                    marginBottom: '15px'
                  }}>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                      📚 {doc.concepts.length} concepts extracted
                    </p>
                  </div>
                )}

                {/* Processing Message */}
                {doc.status === 'processing' && (
                  <div style={{ 
                    background: '#fff8e1', 
                    padding: '12px', 
                    borderRadius: '6px',
                    marginBottom: '15px'
                  }}>
                    <p style={{ fontSize: '0.9rem', color: '#f57c00' }}>
                      ⏳ Processing... This may take a minute
                    </p>
                  </div>
                )}

                {/* Failed Message */}
                {doc.status === 'failed' && (
                  <div style={{ 
                    background: '#fdecea', 
                    padding: '12px', 
                    borderRadius: '6px',
                    marginBottom: '15px'
                  }}>
                    <p style={{ fontSize: '0.9rem', color: 'var(--danger-color)' }}>
                      ❌ Processing failed
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleOpenDocument(doc.document_id)}
                    disabled={doc.status !== 'completed'}
                    style={{ flex: 1 }}
                  >
                    {doc.status === 'completed' ? '📖 Open Document' : '⏳ Processing...'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
