#!/bin/bash
# 🚀 Hybrid Flexible CI/CD Setup Script
# This script helps you set up the GitHub Actions workflow

set -e

echo "🚀 Setting up Hybrid Flexible CI/CD for Receipt Search App"
echo "============================================================"

# Check if we're in the right directory
if [ ! -f "DEPLOYMENT_SUMMARY.md" ]; then
    echo "❌ Error: Please run this script from the receipt-search-app root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not initialized. Run 'git init' first."
    exit 1
fi

echo "✅ Git repository detected"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "master")
echo "📍 Current branch: $CURRENT_BRANCH"

# Recommend branch setup
if [ "$CURRENT_BRANCH" = "master" ]; then
    echo "💡 Recommendation: Rename master to main for better GitHub integration"
    read -p "   Rename master branch to main? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -m master main
        echo "✅ Branch renamed to main"
        CURRENT_BRANCH="main"
    fi
fi

# Check if develop branch exists
if ! git show-ref --verify --quiet refs/heads/develop; then
    echo "💡 Creating develop branch for development workflow"
    git checkout -b develop
    git checkout $CURRENT_BRANCH
    echo "✅ Develop branch created"
fi

# Add all current files to git if not already tracked
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory is clean"
else
    echo "📦 Adding current project files to git..."
    git add .
    git commit -m "🎉 Initial commit: Receipt Search App with AWS serverless infrastructure

- Complete Python FastAPI backend with Lambda functions
- Terraform infrastructure as code
- Comprehensive test suite (unit/integration/e2e)
- Deployment automation scripts
- Resource management and cost optimization tools
- GitHub Actions Hybrid Flexible CI/CD workflow"
    echo "✅ Initial commit created"
fi

echo ""
echo "🔧 Hybrid Flexible CI/CD Workflow Features:"
echo "- 🎛️  Manual deployment control via workflow_dispatch"
echo "- 📊  Smart testing (only runs when code changes)"
echo "- 🌍  Multi-environment support (dev/staging/prod)"
echo "- ⚡  Fast feedback loops"
echo "- 💰  Cost-effective GitHub Actions usage"
echo "- 🔍  Change detection for targeted builds"
echo ""

echo "📋 Required GitHub Secrets Setup:"
echo "============================================"
echo "Go to GitHub → Your Repository → Settings → Secrets and variables → Actions"
echo ""
echo "🔑 Required secrets:"
echo "  AWS_ACCESS_KEY_ID              # Your AWS access key for development environment"
echo "  AWS_SECRET_ACCESS_KEY          # Your AWS secret key for development environment"
echo "  MEILISEARCH_MASTER_KEY         # Your Meilisearch master key"
echo ""
echo "🔑 Optional (for multi-environment):"
echo "  AWS_ACCESS_KEY_ID_STAGING      # Staging environment AWS access key"
echo "  AWS_SECRET_ACCESS_KEY_STAGING  # Staging environment AWS secret key"
echo "  AWS_ACCESS_KEY_ID_PROD         # Production environment AWS access key"
echo "  AWS_SECRET_ACCESS_KEY_PROD     # Production environment AWS secret key"
echo "  MEILISEARCH_MASTER_KEY_STAGING # Staging Meilisearch key"
echo "  MEILISEARCH_MASTER_KEY_PROD    # Production Meilisearch key"
echo ""

echo "🚀 Usage Examples:"
echo "=================="
echo "1. 📈 Automatic triggers:"
echo "   - Push to 'develop' → Deploy to dev environment"
echo "   - Push to 'main' → Deploy to staging environment"
echo "   - Pull request → Run validation and tests"
echo ""
echo "2. 🎛️  Manual triggers (via GitHub Actions tab):"
echo "   - Select environment: dev/staging/prod"
echo "   - Toggle full test suite: on/off"
echo "   - Deploy infrastructure changes: on/off"
echo ""

echo "💡 Next Steps:"
echo "=============="
echo "1. 🔐 Set up GitHub secrets (see above)"
echo "2. 🌐 Push to GitHub: git remote add origin <your-repo-url>"
echo "3. 📤 Push code: git push -u origin main"
echo "4. 🌿 Create develop branch: git push -u origin develop"
echo "5. 🔄 Test workflow: Make a change and push to develop"
echo ""

echo "🎯 Workflow file location: .github/workflows/hybrid-flexible.yml"
echo "📖 Full documentation: .github/WORKFLOW_COMPARISON.md"
echo ""

echo "✅ Hybrid Flexible CI/CD setup complete!"
echo "💰 This workflow will help you manage AWS costs while maintaining professional CI/CD practices."
echo ""

# Show current git status
echo "📊 Current Git Status:"
git status --short