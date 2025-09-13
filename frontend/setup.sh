#!/bin/bash

# Frontend Setup Script for Receipt Search Application

echo "🚀 Setting up Receipt Search Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ $NODE_VERSION -lt 18 ]; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please upgrade to Node.js 18+."
    exit 1
fi

echo "✅ Node.js version $(node -v) found"

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
if command -v yarn &> /dev/null; then
    echo "Using Yarn..."
    yarn install
else
    echo "Using npm..."
    npm install
fi

# Copy environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env.local
    echo "✅ Created .env.local - please update with your backend API URL"
else
    echo "✅ Environment file already exists"
fi

# Create directories that might be needed
mkdir -p public/images
mkdir -p src/assets

echo ""
echo "🎉 Frontend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env.local with your backend API URL"
echo "2. Start development server: npm run dev"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Available commands:"
echo "  npm run dev      - Start development server"
echo "  npm run build    - Build for production"
echo "  npm run preview  - Preview production build"
echo "  npm run type-check - Check TypeScript types"
echo ""