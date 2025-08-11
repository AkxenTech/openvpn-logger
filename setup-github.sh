#!/bin/bash

# GitHub Repository Setup Script for OpenVPN Logger

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first:"
    echo "sudo apt update && sudo apt install git"
    exit 1
fi

# Check if we're in a git repository
if [ -d ".git" ]; then
    print_warning "Git repository already exists in this directory"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Initialize git repository
print_status "Initializing git repository..."
git init

# Add all files
print_status "Adding files to git..."
git add .

# Create initial commit
print_status "Creating initial commit..."
git commit -m "Initial commit: OpenVPN Logger project

- Real-time OpenVPN log monitoring
- MongoDB integration for data storage
- System statistics tracking
- Data analysis tools
- Systemd service integration"

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    print_status "GitHub CLI found. Using it to create repository..."
    
    # Check if user is authenticated
    if gh auth status &> /dev/null; then
        print_status "GitHub CLI authenticated. Creating repository..."
        
        # Get repository name from current directory
        REPO_NAME=$(basename "$PWD")
        
        # Ask user for repository visibility
        echo "Choose repository visibility:"
        echo "1) Public (recommended for open source)"
        echo "2) Private"
        read -p "Enter choice (1 or 2): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[1]$ ]]; then
            VISIBILITY="--public"
        else
            VISIBILITY="--private"
        fi
        
        # Create repository
        gh repo create "$REPO_NAME" $VISIBILITY --source=. --remote=origin --push
        
        print_status "Repository created and code pushed to GitHub!"
        print_status "Repository URL: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
        
    else
        print_warning "GitHub CLI not authenticated. Please run 'gh auth login' first."
        print_status "Continuing with manual setup..."
        manual_setup
    fi
else
    print_warning "GitHub CLI not found. Using manual setup..."
    manual_setup
fi

manual_setup() {
    print_status "Manual setup instructions:"
    echo ""
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: $(basename "$PWD")"
    echo "3. Choose visibility (public/private)"
    echo "4. DO NOT initialize with README, .gitignore, or license"
    echo "5. Click 'Create repository'"
    echo ""
    echo "After creating the repository, run these commands:"
    echo ""
    echo "git remote add origin https://github.com/YOUR_USERNAME/$(basename "$PWD").git"
    echo "git branch -M main"
    echo "git push -u origin main"
    echo ""
    print_status "Your local repository is ready with initial commit!"
}

print_status "Setup complete!"
