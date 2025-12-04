#!/bin/bash

# Passport Photo AI - Quick Setup Script
# This script creates the complete project structure

echo "🚀 Setting up Passport Photo AI project..."

# Create main directory
mkdir -p passport-photo-ai
cd passport-photo-ai

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p backend frontend/src frontend/public demo docs/screenshots docker

# Create backend files
echo "📄 Creating backend files..."

# backend/requirements.txt
cat > backend/requirements.txt << 'EOF'
flask==3.0.0
flask-cors==4.0.0
pillow==10.1.0
opencv-python==4.8.1.78
numpy==1.26.2
anthropic==0.8.1
python-dotenv==1.0.0
gunicorn==21.2.0
EOF

# backend/.env.example
cat > backend/.env.example << 'EOF'
# Anthropic API Key (optional - for AI vision analysis)
ANTHROPIC_API_KEY=your_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Upload Configuration
MAX_CONTENT_LENGTH=16777216
EOF

# frontend/package.json
echo "📄 Creating frontend files..."
cat > frontend/package.json << 'EOF'
{
  "name": "passport-photo-frontend",
  "version": "1.0.0",
  "description": "AI Passport Photo Converter Frontend",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.31",
    "autoprefixer": "^10.4.16"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "proxy": "http://localhost:5000",
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
EOF

# frontend/tailwind.config.js
cat > frontend/tailwind.config.js << 'EOF'
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: []
}
EOF

# frontend/postcss.config.js
cat > frontend/postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
}
EOF

# frontend/src/index.css
cat > frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

# frontend/src/index.js
cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# frontend/public/index.html
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#000000" />
  <meta name="description" content="AI Passport Photo Converter" />
  <title>AI Passport Photo Converter</title>
</head>
<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root"></div>
</body>
</html>
EOF

# .gitignore
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
venv/
env/
__pycache__/
*.pyc

# Environment variables
.env
.env.local

# Build outputs
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
temp_*.jpg
temp_*.png
EOF

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:5000
EOF

# docker/Dockerfile.backend
cat > docker/Dockerfile.backend << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
EOF

# docker/Dockerfile.frontend
cat > docker/Dockerfile.frontend << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOF

# README.md
cat > README.md << 'EOF'
# 📸 AI Passport Photo Converter

Convert any photo into US passport-compliant photos using AI-powered face detection and image processing.

## Features

- 🎯 Intelligent Face Detection
- 📏 Smart Cropping (50-69% head height)
- 🎨 Background Removal
- 📐 Measurement Overlays
- 🤖 AI Vision Analysis (Optional)
- 🖼️ Perfect Specifications (600x600px, 300 DPI, 2x2 inches)

## Quick Start

### Option 1: Docker (Easiest)
```bash
docker-compose up
```
Open http://localhost:3000

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Requirements

- Python 3.8+
- Node.js 14+
- Docker (optional)

## License

MIT License - See LICENSE file
EOF

echo "✅ Project structure created!"
echo ""
echo "📝 Next steps:"
echo "1. Copy app.py to backend/app.py from the artifacts"
echo "2. Copy App.js to frontend/src/App.js from the artifacts"
echo "3. Initialize git: git init"
echo "4. Create GitHub repo and push"
echo ""
echo "🚀 To run locally:"
echo "   cd backend && pip install -r requirements.txt && python app.py"
echo "   cd frontend && npm install && npm start"
