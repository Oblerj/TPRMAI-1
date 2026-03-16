#!/bin/bash

# Development startup script for AI TPRM Machine
# Starts mock-OIDC and Next.js with correct configuration

set -e

echo "🚀 Starting AI TPRM Machine Development Environment"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop any existing services
echo -e "\n${BLUE}📦 Stopping existing services...${NC}"
pkill -f "next dev" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
sleep 2

# Clear Next.js cache
echo -e "${BLUE}🧹 Clearing Next.js cache...${NC}"
rm -rf .next

# Start mock-OIDC with correct configuration
echo -e "\n${BLUE}🔐 Starting mock-OIDC provider...${NC}"
cd mock-oidc
export MOCK_OIDC_INTERNAL_BASE_URL="http://localhost:10090"
export MOCK_OIDC_EXTERNAL_BASE_URL="http://localhost:10090"
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 10090 > /tmp/mock-oidc.log 2>&1 &
OIDC_PID=$!
cd ..

# Wait for mock-OIDC to be ready
echo -e "${BLUE}⏳ Waiting for mock-OIDC...${NC}"
for i in {1..10}; do
  if curl -s http://localhost:10090/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Mock-OIDC is ready${NC}"
    break
  fi
  if [ $i -eq 10 ]; then
    echo -e "${RED}✗ Mock-OIDC failed to start${NC}"
    exit 1
  fi
  sleep 1
done

# Seed mock-OIDC with test users
echo -e "${BLUE}🌱 Seeding test users...${NC}"
bash scripts/seed-mock-oidc.sh

# Start Next.js
echo -e "\n${BLUE}⚡ Starting Next.js development server...${NC}"
npm run dev > /tmp/nextjs.log 2>&1 &
NEXTJS_PID=$!

# Wait for Next.js to be ready
echo -e "${BLUE}⏳ Waiting for Next.js...${NC}"
for i in {1..20}; do
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Next.js is ready${NC}"
    break
  fi
  if [ $i -eq 20 ]; then
    echo -e "${RED}✗ Next.js failed to start${NC}"
    echo -e "${RED}Check /tmp/nextjs.log for errors${NC}"
    exit 1
  fi
  sleep 1
done

# Verify OIDC configuration
echo -e "\n${BLUE}🔍 Verifying OIDC configuration...${NC}"
ISSUER=$(curl -s http://localhost:10090/.well-known/openid-configuration | python3 -c "import sys, json; print(json.load(sys.stdin)['issuer'])" 2>/dev/null)
if [ "$ISSUER" = "http://localhost:10090" ]; then
  echo -e "${GREEN}✓ OIDC issuer correctly configured: $ISSUER${NC}"
else
  echo -e "${RED}✗ OIDC issuer misconfigured: $ISSUER${NC}"
  echo -e "${RED}  Expected: http://localhost:10090${NC}"
fi

# Success message
echo -e "\n${GREEN}=================================================="
echo -e "✅ Development environment is ready!"
echo -e "==================================================${NC}"
echo -e ""
echo -e "📱 Application: ${BLUE}http://localhost:3000${NC}"
echo -e "🔐 Mock OIDC:   ${BLUE}http://localhost:10090${NC}"
echo -e ""
echo -e "📋 Test Users:"
echo -e "   • Mock Admin    (ADMIN role)"
echo -e "   • Mock Analyst  (ANALYST role)"
echo -e "   • Mock Viewer   (VIEWER role)"
echo -e "   • Mock Vendor   (VENDOR role)"
echo -e ""
echo -e "📝 Logs:"
echo -e "   • Next.js:    tail -f /tmp/nextjs.log"
echo -e "   • Mock OIDC:  tail -f /tmp/mock-oidc.log"
echo -e ""
echo -e "🛑 To stop: pkill -f 'next dev'; pkill -f uvicorn"
echo -e ""
