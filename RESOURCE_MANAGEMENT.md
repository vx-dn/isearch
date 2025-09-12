# ⚡ Cloud Resource Management Guide

## 🎯 Best Practices for Different Scenarios

### **Development/Testing Environment**
✅ **STOP/START Pattern** (Recommended for you)
- Stop services during nights, weekends, holidays
- Save 60-80% on costs while preserving all data
- Quick restart when needed (2-3 minutes)

### **Production Environment**  
✅ **Always-on with Auto-scaling**
- Keep services running 24/7
- Use auto-scaling for load variations
- Focus on optimization, not stopping

### **Demo/Learning Environment**
✅ **Scheduled Stop/Start**
- Automate daily stop/start cycles
- Use AWS Lambda or EventBridge for scheduling
- Maximum cost savings with minimal management

---

## 🛠️ Your Options

### Option 1: Stop Services (Recommended for Development)
```bash
./stop_services.sh
```
**What it does:**
- 🛑 Stops EC2 instance (Meilisearch)
- 🔒 Sets Lambda concurrency limits
- ✅ Preserves ALL data and configuration
- 💰 Saves ~$15-20/month (30-40% reduction)
- ⏱️ Restart in 2-3 minutes when needed

### Option 2: Start Services
```bash
./start_services.sh
```
**What it does:**
- 🚀 Starts EC2 instance
- 🔓 Removes Lambda limits
- 🧪 Health checks all services
- ⚡ Full functionality restored

### Option 3: Complete Cleanup (Permanent deletion)
```bash
./cleanup.sh
```
**What it does:**
- 🗑️ Deletes ALL resources permanently
- 💰 Saves ~$50-65/month (100% reduction)
- ⚠️ ALL DATA LOST - Cannot be recovered

---

## 📊 Cost Comparison

| Scenario | Monthly Cost | Data Preserved | Restart Time |
|----------|-------------|----------------|--------------|
| **Running** | ~$50-65 | ✅ Yes | Immediate |
| **Stopped** | ~$35-45 | ✅ Yes | 2-3 minutes |
| **Deleted** | $0 | ❌ No | 30-60 minutes to redeploy |

---

## 🔄 Common Workflows

### Daily Development Cycle
```bash
# Morning: Start work
./start_services.sh

# Evening: Stop work  
./stop_services.sh
```

### Weekend Break
```bash
# Friday evening
./stop_services.sh

# Monday morning
./start_services.sh
```

### End of Project
```bash
# Backup any important data first
# Then permanently clean up
./cleanup.sh
```

---

## 🎯 Recommended Approach for Your Situation

Since you're learning/developing, I recommend the **Stop/Start pattern**:

1. **Stop services when not using** (evenings, weekends)
   ```bash
   ./stop_services.sh
   ```

2. **Start services when developing**
   ```bash
   ./start_services.sh
   ```

3. **Only delete permanently when completely done**
   ```bash
   ./cleanup.sh
   ```

### Benefits:
- ✅ Save 30-40% on costs
- ✅ Keep all your data and configuration
- ✅ Quick restart (2-3 minutes)
- ✅ No need to redeploy or reconfigure
- ✅ Perfect for learning and development

---

## 🚀 Quick Start

**Stop services now to save costs:**
```bash
cd /home/dev/psearch/receipt-search-app/backend/deploy
./stop_services.sh
```

**Start services when you need them:**
```bash
./start_services.sh
```

---

## 💡 Pro Tips

1. **Automate with cron** (optional):
   ```bash
   # Stop at 6 PM weekdays
   0 18 * * 1-5 /path/to/stop_services.sh
   
   # Start at 9 AM weekdays  
   0 9 * * 1-5 /path/to/start_services.sh
   ```

2. **Monitor costs** in AWS Billing Dashboard

3. **Set billing alerts** for unexpected charges

4. **Use CloudWatch** to monitor when services are actually being used

The **stop/start approach** is definitely the industry best practice for development environments! 🎯