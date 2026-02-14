#!/bin/bash

# jlo - Just Logs startup script

set -e

echo "Starting jlo - Just Logs..."
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found. Please run this script from the project root."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync backend dependencies
echo "Syncing backend dependencies with uv..."
cd backend
uv sync
cd ..

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    echo ""
    echo "Frontend is not built yet."
    echo "You have two options:"
    echo "  1. Build the frontend for production (recommended)"
    echo "  2. Run backend only (you'll need to start frontend separately)"
    echo ""
    read -p "Build frontend now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! command -v npm &> /dev/null; then
            echo "Error: npm is not installed. Please install Node.js and npm."
            exit 1
        fi
        
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        echo "Building frontend..."
        npm run build
        cd ..
    fi
fi

echo ""
echo "Starting jlo server with uv..."
echo "Access the application at: http://localhost:8000"
echo "Default credentials: admin / admin"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
