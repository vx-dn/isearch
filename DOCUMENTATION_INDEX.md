# 📚 Documentation Index

Quick navigation guide for Receipt Search App documentation.

## 🎯 Quick Links

### **For Deployment Status & Overview**
- **[`DEPLOYMENT_SUMMARY.md`](DEPLOYMENT_SUMMARY.md)** - Current status, infrastructure overview, quick operations

### **For Lambda Development**
- **[`backend/deploy/README.md`](backend/deploy/README.md)** - Complete Lambda deployment guide, troubleshooting

### **For Cost Management**
- **[`RESOURCE_MANAGEMENT.md`](RESOURCE_MANAGEMENT.md)** - Professional resource management best practices
- **[`backend/deploy/stop_services.sh`](backend/deploy/stop_services.sh)** - Stop services (save 30-40% costs)
- **[`backend/deploy/start_services.sh`](backend/deploy/start_services.sh)** - Restart services

### **For Clean Development**
- **[`CLEANUP_GUIDE.md`](CLEANUP_GUIDE.md)** - Development environment cleanup
- **[`backend/deploy/cleanup.sh`](backend/deploy/cleanup.sh)** - Automated cleanup script

## 🗂️ File Organization

```
receipt-search-app/
├── DEPLOYMENT_SUMMARY.md      # 📊 Main status & overview
├── RESOURCE_MANAGEMENT.md     # 💰 Cost optimization guide  
├── CLEANUP_GUIDE.md          # 🧹 Development cleanup
├── DEPLOYMENT_SUCCESS.md     # 🎉 Initial deployment log
├── backend/deploy/
│   ├── README.md             # 🚀 Lambda deployment guide
│   ├── stop_services.sh      # ⏹️  Stop services (save money)
│   ├── start_services.sh     # ▶️  Restart services
│   ├── test_deployment.sh    # 🧪 Test deployments
│   ├── test_pipeline.sh      # 🔄 End-to-end testing
│   └── ...other scripts      # ⚙️  Various deployment tools
└── infrastructure/           # 🏗️  Terraform infrastructure
```

## 🚀 Common Workflows

### **Daily Development**
1. Check status: `cat DEPLOYMENT_SUMMARY.md`
2. Work with Lambda: `backend/deploy/README.md`
3. Save costs: `./backend/deploy/stop_services.sh`

### **New Team Member Onboarding**
1. Read: `DEPLOYMENT_SUMMARY.md` (overview)
2. Deploy: `backend/deploy/README.md` (hands-on)
3. Manage: `RESOURCE_MANAGEMENT.md` (best practices)

### **End of Work Session**
1. Run: `./backend/deploy/stop_services.sh`
2. Saves: ~$15-20/month (30-40% cost reduction)
3. Restart: `./backend/deploy/start_services.sh` (when needed)

---
*Last Updated: 2025-09-12*