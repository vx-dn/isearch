#!/bin/bash

# Receipt Search Application Startup Script

set -e

echo "🚀 Starting Receipt Search Application Setup..."

# Change to backend directory
cd /home/dev/psearch/receipt-search-app/backend

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Using .env.example as template."
    echo "Please copy .env.example to .env and configure your environment variables."
    cp .env.example .env
fi

# Activate Python virtual environment
echo "🐍 Activating Python virtual environment..."
source /home/dev/psearch/.venv/bin/activate

# Verify Python environment
echo "✅ Python version: $(/home/dev/psearch/.venv/bin/python --version)"
echo "✅ Virtual environment: $VIRTUAL_ENV"

# Install/update dependencies
echo "📦 Installing Python dependencies..."
/home/dev/psearch/.venv/bin/pip install -r requirements.txt

# Run health checks
echo "🏥 Running basic health checks..."

# Check if we can import our modules
echo "🔍 Checking module imports..."
/home/dev/psearch/.venv/bin/python -c "
import sys
sys.path.append('/home/dev/psearch/receipt-search-app/backend/src')

try:
    from domain.config import DOMAIN_CONFIG
    print('✅ Domain configuration loaded')
    
    from infrastructure.config import infrastructure_config
    print('✅ Infrastructure configuration loaded')
    
    from main import app
    print('✅ FastAPI application loaded')
    
    print('🎉 All core modules imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Module import check passed"
else
    echo "❌ Module import check failed"
    exit 1
fi

# Start the application
echo "🌟 Starting Receipt Search API..."
echo "📍 API will be available at: http://localhost:${PORT:-8000}"
echo "📚 API documentation at: http://localhost:${PORT:-8000}/docs"
echo "🔄 Redoc documentation at: http://localhost:${PORT:-8000}/redoc"

# Start FastAPI with uvicorn
cd src
/home/dev/psearch/.venv/bin/python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --reload \
    --log-level info
