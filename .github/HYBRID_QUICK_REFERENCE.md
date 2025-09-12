# 🔧 Hybrid Flexible CI/CD - Quick Reference

## 🚀 Workflow Triggers

### Automatic Triggers
- **Push to `develop`** → Deploy to development environment
- **Push to `main`** → Deploy to staging environment  
- **Pull Request to `main`** → Run validation and tests only

### Manual Triggers (GitHub Actions → Run workflow)
- **Environment**: Choose dev/staging/prod
- **Run Tests**: Toggle full test suite on/off
- **Deploy Infrastructure**: Toggle Terraform deployment on/off

## 🎛️ Manual Deployment Examples

### Development Deployment
```bash
# Via GitHub UI: Actions → Hybrid Flexible CI/CD → Run workflow
Environment: dev
Run tests: ✅ true
Deploy infrastructure: ❌ false
```

### Production Deployment (requires main branch)
```bash
# Via GitHub UI: Actions → Hybrid Flexible CI/CD → Run workflow  
Environment: prod
Run tests: ✅ true
Deploy infrastructure: ❌ false (unless infrastructure changes)
```

### Infrastructure Update
```bash
# Via GitHub UI: Actions → Hybrid Flexible CI/CD → Run workflow
Environment: dev
Run tests: ❌ false (skip for faster deployment)
Deploy infrastructure: ✅ true
```

## 🔍 Smart Features

### Change Detection
- **Backend changes** → Run Python tests and linting
- **Infrastructure changes** → Validate Terraform
- **No changes** → Skip unnecessary jobs

### Conditional Execution
- **Unit tests**: Always run when backend changes
- **Integration tests**: Only on main branch
- **Security scans**: Only when backend changes
- **Infrastructure validation**: Only when Terraform changes

## 📊 Cost Optimization

### GitHub Actions Usage
- **Development push**: ~8-12 minutes (unit tests + deploy)
- **Main branch push**: ~15-20 minutes (full tests + deploy)
- **Manual deployment**: ~5-10 minutes (skip tests)

### AWS Cost Management
- Integrates with your existing `stop_services.sh` and `start_services.sh`
- Use manual triggers to control deployment timing
- Deploy only when needed vs automatic on every push

## 🔒 Required GitHub Secrets

### Minimum Setup (Development Only)
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key  
MEILISEARCH_MASTER_KEY=your_meilisearch_key
```

### Multi-Environment Setup
```
# Development
AWS_ACCESS_KEY_ID=dev_aws_access_key
AWS_SECRET_ACCESS_KEY=dev_aws_secret_key
MEILISEARCH_MASTER_KEY=dev_meilisearch_key

# Staging  
AWS_ACCESS_KEY_ID_STAGING=staging_aws_access_key
AWS_SECRET_ACCESS_KEY_STAGING=staging_aws_secret_key
MEILISEARCH_MASTER_KEY_STAGING=staging_meilisearch_key

# Production
AWS_ACCESS_KEY_ID_PROD=prod_aws_access_key
AWS_SECRET_ACCESS_KEY_PROD=prod_aws_secret_key
MEILISEARCH_MASTER_KEY_PROD=prod_meilisearch_key
```

## 🌊 Recommended Workflow

### Daily Development
1. Work on `develop` branch
2. Push changes → Auto-deploy to dev
3. Test your changes
4. Create PR to `main` → Auto-run tests

### Release to Staging
1. Merge PR to `main` → Auto-deploy to staging
2. Test staging environment
3. Manual production deployment when ready

### Cost-Conscious Development
1. Use manual triggers to control deployment timing
2. Skip tests when doing quick fixes
3. Use `./stop_services.sh` after testing
4. Use `./start_services.sh` when resuming work

## 🔄 Branch Strategy

```
main (production-ready)
├── staging deployments (automatic)
├── production deployments (manual approval)
└── develop (active development)
    ├── feature/branch-1
    ├── feature/branch-2
    └── dev deployments (automatic)
```

## 🆘 Troubleshooting

### Workflow Not Triggering
- Check branch names match (`main`, `develop`)
- Verify file is in `.github/workflows/`
- Check GitHub Actions tab for errors

### Deployment Failures
- Check AWS credentials in GitHub secrets
- Verify Meilisearch key is correct
- Check AWS resource limits/quotas

### Test Failures
- Run tests locally: `cd backend && pytest tests/unit/`
- Check dependency installation issues
- Verify test data and mocks

## 📞 Quick Commands

```bash
# Local testing
cd backend && pytest tests/unit/
cd backend/deploy && ./test_deployment.sh

# Cost management
./backend/deploy/stop_services.sh    # Save 30-40% costs
./backend/deploy/start_services.sh   # Resume services

# Git workflow
git checkout develop                 # Switch to dev branch
git checkout main                    # Switch to main branch
git push origin develop              # Deploy to dev
git push origin main                 # Deploy to staging
```