/**
 * API Service Layer
 * 
 * This module handles all HTTP communication with the FastAPI backend.
 * It provides a clean interface for all API operations.
 * 
 * Base URL: http://localhost:8000 (backend server)
 * All requests use the hardcoded user_id: "user_1" (authentication is out of scope)
 */

import axios from 'axios';

// Base API configuration
const API_BASE_URL = 'http://localhost:8000';
const HARDCODED_USER_ID = 'demo_user';  // Authentication is out of scope

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ====================================================
// DOCUMENT OPERATIONS
// ====================================================

/**
 * Create a new document from educational text
 * @param {string} text - The educational text content
 * @returns {Promise<{document_id: string, status: string}>}
 */
export const createDocument = async (text) => {
  const response = await api.post('/api/document/create', {
    user_id: HARDCODED_USER_ID,
    text: text,
  });
  return response.data;
};

/**
 * Get document details including concepts
 * @param {string} documentId - The document ID
 * @returns {Promise<{document_id: string, status: string, concepts: Array}>}
 */
export const getDocument = async (documentId) => {
  const response = await api.get(`/api/document/${documentId}`, {
    params: { user_id: HARDCODED_USER_ID },
  });
  return response.data;
};

/**
 * Get all documents for the current user
 * @returns {Promise<Array>}
 */
export const getUserDocuments = async () => {
  const response = await api.get(`/api/document/user/${HARDCODED_USER_ID}/list`);
  return response.data.documents;
};

/**
 * Delete a document
 * @param {string} documentId - The document ID to delete
 * @returns {Promise<{success: boolean}>}
 */
export const deleteDocument = async (documentId) => {
  const response = await api.delete(`/api/document/${documentId}`, {
    params: { user_id: HARDCODED_USER_ID },
  });
  return response.data;
};

// ====================================================
// EXPLANATION OPERATIONS (Agent 2, Mode A)
// ====================================================

/**
 * Generate an explanation for a concept
 * @param {string} documentId - The document ID
 * @param {string} conceptId - The concept ID (e.g., "C1")
 * @param {string} tone - Explanation tone: "simple" | "exam" | "detailed" | "intuitive"
 * @returns {Promise<{explanation: string}>}
 */
export const generateExplanation = async (documentId, conceptId, tone) => {
  const response = await api.post(
    '/api/explain',
    {
      document_id: documentId,
      concept_id: conceptId,
      tone: tone,
    },
    {
      params: { user_id: HARDCODED_USER_ID },
    }
  );
  return response.data;
};

// ====================================================
// QUIZ OPERATIONS (Agent 2, Mode B)
// ====================================================

/**
 * Generate a quiz for a concept
 * @param {string} documentId - The document ID
 * @param {string} conceptId - The concept ID (e.g., "C1")
 * @param {string} difficulty - Difficulty level: "easy" | "medium" | "hard"
 * @returns {Promise<{questions: Array}>}
 */
export const generateQuiz = async (documentId, conceptId, difficulty) => {
  const response = await api.post(
    '/api/quiz',
    {
      document_id: documentId,
      concept_id: conceptId,
      difficulty: difficulty,
    },
    {
      params: { user_id: HARDCODED_USER_ID },
    }
  );
  return response.data;
};

// ====================================================
// HEALTH CHECK
// ====================================================

/**
 * Check if the backend is operational
 * @returns {Promise<{status: string}>}
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
