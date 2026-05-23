#!/usr/bin/env bash
# setup.sh — One-time setup for the IT Brief pipeline
# Run: bash setup.sh

set -e

echo ""
echo "================================================="
echo " India IT Brief Pipeline — Setup"
echo "================================================="
echo ""

# ── Check Python ───────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required. Install it first."
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYTHON_VERSION found"

# ── Install dependencies ───────────────────────────────────
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages --quiet
echo "✓ Dependencies installed"

# ── Create .env if not exists ──────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "✓ Created .env from template"
    echo "  → Edit .env and add your GEMINI_API_KEY before running"
else
    echo "✓ .env already exists"
fi

# ── Create data directory ──────────────────────────────────
mkdir -p data output/daily output/site
echo "✓ Directories created"

# ── Initialise context store if not exists ─────────────────
if [ ! -f data/context.json ]; then
    echo ""
    echo "Initialising context store..."
    cd pipeline && python3 -c "from store import load_store; load_store('../data/context.json')" && cd ..
    echo "✓ data/context.json initialised"
else
    echo "✓ data/context.json already exists"
fi

# ── Cron setup instructions ────────────────────────────────
echo ""
echo "================================================="
echo " Setup complete."
echo "================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your GEMINI_API_KEY"
echo ""
echo "2. Test a manual run:"
echo "    python3 run.py"
echo ""
echo "3. Add to cron for daily runs at 12:01 AM IST:"
echo "   crontab -e"
echo ""
echo "   Add this line (adjust path):"
echo "   1 0 * * * TZ=Asia/Kolkata cd $(pwd) && source .env && python3 run.py >> logs/pipeline.log 2>&1"
echo ""
echo "4. Set WEBSITE_REPO_PATH in .env to auto-publish"
echo ""
