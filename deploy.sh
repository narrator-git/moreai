#!/bin/bash

# MoreAI Docker Deployment Script
set -e

echo "🚀 MoreAI Docker Deployment Script"
echo "=================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f env.docker.example ]; then
        cp env.docker.example .env
        echo "✅ .env file created from env.docker.example"
        echo "⚠️  Please edit .env file with your actual values before continuing"
        echo "   Required: OPENAI_API_KEY"
        echo "   Recommended: SECRET_KEY"
        exit 0
    else
        echo "❌ env.docker.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env; then
    echo "✅ .env file appears to be configured"
else
    echo "⚠️  Please configure your OPENAI_API_KEY in .env file"
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the application
echo "🚀 Starting MoreAI application..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ MoreAI is running successfully!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Web Interface: http://localhost:8000"
    echo "   Health Check:  http://localhost:8000/health"
    echo ""
    echo "🔐 Default admin login:"
    echo "   Username: admin"
    echo "   Password: Admin123!"
    echo ""
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop application: docker-compose down"
else
    echo "❌ Application failed to start. Check logs:"
    docker-compose logs
    exit 1
fi 