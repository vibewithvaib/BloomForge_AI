/**
 * ConceptTree Component
 * 
 * Purpose: Display hierarchical concept selector
 * 
 * Features:
 * - Hierarchical display based on concept levels
 * - Visual indentation for nested concepts
 * - Click to select a concept
 * - Highlight selected concept
 * - Show prerequisites relationship
 */

import React from 'react';

const ConceptTree = ({ concepts, selectedConceptId, onSelectConcept }) => {
  // Group concepts by level for hierarchical display
  const conceptsByLevel = concepts.reduce((acc, concept) => {
    if (!acc[concept.level]) {
      acc[concept.level] = [];
    }
    acc[concept.level].push(concept);
    return acc;
  }, {});

  // Get max level
  const maxLevel = Math.max(...concepts.map(c => c.level));

  // Render a concept item
  const renderConcept = (concept) => {
    const isSelected = concept.id === selectedConceptId;
    const levelClass = `concept-item level-${Math.min(concept.level, 2)} ${isSelected ? 'selected' : ''}`;

    return (
      <div
        key={concept.id}
        className={levelClass}
        onClick={() => onSelectConcept(concept)}
        style={{
          marginLeft: `${concept.level * 20}px`,
          position: 'relative'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: concept.level === 0 ? '600' : '500', marginBottom: '4px' }}>
              {concept.level === 0 && '📌 '}
              {concept.level === 1 && '└─ '}
              {concept.level >= 2 && '└── '}
              {concept.name}
            </div>
            <div style={{ 
              fontSize: '0.85rem', 
              opacity: isSelected ? 0.9 : 0.7,
              marginTop: '4px'
            }}>
              {concept.definition.substring(0, 80)}
              {concept.definition.length > 80 ? '...' : ''}
            </div>
          </div>
          
          {/* Importance indicator */}
          <div style={{ 
            fontSize: '0.75rem', 
            opacity: 0.7,
            marginLeft: '10px',
            whiteSpace: 'nowrap'
          }}>
            Level {concept.level}
          </div>
        </div>

        {/* Prerequisites indicator */}
        {concept.prerequisites && concept.prerequisites.length > 0 && (
          <div style={{ 
            fontSize: '0.75rem', 
            opacity: 0.6,
            marginTop: '6px',
            fontStyle: 'italic'
          }}>
            Requires: {concept.prerequisites.join(', ')}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="concept-tree">
      {/* Header */}
      <div style={{ 
        marginBottom: '15px', 
        paddingBottom: '15px', 
        borderBottom: '2px solid var(--border-color)' 
      }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>
          📚 Concept Hierarchy
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          {concepts.length} concepts extracted • Select one to explore
        </p>
      </div>

      {/* Empty state */}
      {concepts.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
          <p>No concepts found</p>
        </div>
      )}

      {/* Render concepts by level */}
      {Array.from({ length: maxLevel + 1 }, (_, level) => (
        <div key={level}>
          {conceptsByLevel[level]?.map(concept => renderConcept(concept))}
        </div>
      ))}

      {/* Help text */}
      {selectedConceptId && (
        <div style={{ 
          marginTop: '20px', 
          padding: '12px', 
          background: 'var(--bg-color)',
          borderRadius: '6px',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)'
        }}>
          💡 Concept selected. Use the panels below to generate explanations or quizzes.
        </div>
      )}
    </div>
  );
};

export default ConceptTree;
