
### Tech Stack
- **Framework**: React 18 with Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## User Flow

### 1. Dashboard (`/`)
- Shows all user's documents
- Each document displays:
  - Document ID (truncated)
  - Status badge (processing/completed/failed)
  - Creation date
  - Number of concepts (if completed)
- Auto-refreshes while documents are processing
- "Upload New Text" button → Navigate to upload page
- "Open Document" button → Navigate to document view (only for completed documents)

### 2. Upload Text (`/upload`)
- Large textarea for educational content
- Minimum 100 characters validation
- Real-time character counter
- Submit → Creates document and redirects to dashboard
- Shows loading state during processing

### 3. Document View (`/document/:id`)

#### Concept Hierarchy (Left/Top)
- Hierarchical tree of concepts
- Visual indentation by level (0, 1, 2+)
- Click to select concept
- Shows:
  - Concept name
  - Definition preview
  - Level indicator
  - Prerequisites

#### Explanation Panel (Right/Bottom)
- Tone selector dropdown:
  - Simple (ELI5 style)
  - Exam-Oriented (formal)
  - Detailed (comprehensive)
  - Intuitive (analogies)
- "Generate Explanation" button
- Displays explanation with metadata
- Loading states

#### Quiz Panel (Right/Bottom)
- Difficulty selector:
  - Easy (Remember & Understand)
  - Medium (Apply & Analyze)
  - Hard (Evaluate & Create)
- "Generate Quiz" button
- Displays exactly 10 questions with:
  - Question text
  - Bloom's taxonomy level (color-coded)
  - Difficulty score (1-10)
  - Concepts tested
- Shows validation status
- Bloom's level legend

