#!/bin/bash

# HenryBot AI Chat Setup Script
# This script sets up both backend and frontend for the chatbot

set -e  # Exit on error

echo "🚀 HenryBot AI Chat Setup"
echo "=========================="
echo ""

# Check if we're in the correct directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Backend Setup
echo "📦 Setting up Backend..."
echo ""

cd backend

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit backend/.env and add your OpenRouter API key${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

cd ..

# Frontend Setup
echo ""
echo "📦 Setting up Frontend..."
echo ""

cd frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

echo "✓ Node.js found: $(node --version)"

# Check for package manager
if command -v bun &> /dev/null; then
    PKG_MANAGER="bun"
    echo "✓ Using bun"
elif command -v yarn &> /dev/null; then
    PKG_MANAGER="yarn"
    echo "✓ Using yarn"
else
    PKG_MANAGER="npm"
    echo "✓ Using npm"
fi

# Install dependencies
echo "Installing frontend dependencies..."
$PKG_MANAGER install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd ..

# Final instructions
echo ""
echo "============================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Backend:"
echo "   cd backend"
echo "   nano .env  # Add your OpenRouter API key"
echo ""
echo "2. Start Backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "3. Start Frontend (in a new terminal):"
echo "   cd frontend"
echo "   $PKG_MANAGER run dev"
echo ""
echo "4. Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "📚 For more information, see CHATBOT_README.md"
echo ""
