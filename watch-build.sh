#!/usr/bin/env bash
set -e

# JLO Production Build Watcher
# Watches frontend files and rebuilds on changes

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}👀 Watching frontend files for changes...${NC}"
echo -e "${YELLOW}Will rebuild production bundle on file changes${NC}"
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

# Check if fswatch is available
if ! command -v fswatch &> /dev/null; then
    echo -e "${YELLOW}⚠ fswatch not found. Installing via homebrew...${NC}"
    brew install fswatch
fi

# Initial build
echo -e "${BLUE}🔨 Initial build...${NC}"
cd "$PROJECT_ROOT/frontend"
npm run build

# Watch for changes
fswatch -o \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='.git' \
    src/ | while read change; do
    echo ""
    echo -e "${BLUE}🔨 Files changed, rebuilding...${NC}"
    npm run build
    echo -e "${GREEN}✓ Build complete at $(date +%H:%M:%S)${NC}"
done
