/**
 * Main Application Component
 * 
 * Sets up routing and global structure
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import UploadText from './pages/UploadText';
import DocumentView from './pages/DocumentView';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* Dashboard: List all documents */}
          <Route path="/" element={<Dashboard />} />
          
          {/* Upload: Create new document */}
          <Route path="/upload" element={<UploadText />} />
          
          {/* Document View: Main interaction page */}
          <Route path="/document/:documentId" element={<DocumentView />} />
          
          {/* 404 Fallback */}
          <Route path="*" element={
            <div style={{ textAlign: 'center', padding: '100px 20px' }}>
              <h1>404 - Page Not Found</h1>
              <p>The page you're looking for doesn't exist.</p>
              <button 
                className="btn btn-primary" 
                onClick={() => window.location.href = '/'}
                style={{ marginTop: '20px' }}
              >
                Go to Dashboard
              </button>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
