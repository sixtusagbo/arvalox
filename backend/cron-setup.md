# Cron Job Setup for Subscription Management

To set up automated processing of subscription downgrades and usage resets, add these cron jobs:

## 1. Daily Downgrade Processing
Process scheduled downgrades every day at 2 AM:

```bash
# Add to crontab with: crontab -e
0 2 * * * cd /path/to/arvalox/backend && source .venv/bin/activate && python app/management/process_downgrades.py --type=downgrades >> /var/log/arvalox/downgrades.log 2>&1
```

## 2. Monthly Usage Reset (Optional)
Since usage reset is handled automatically on invoice creation, this is mainly for logging:

```bash
# Run on the 1st of each month at 3 AM
0 3 1 * * cd /path/to/arvalox/backend && source .venv/bin/activate && python app/management/process_downgrades.py --type=reset >> /var/log/arvalox/usage_reset.log 2>&1
```

## Manual Execution

You can also run these manually:

```bash
cd backend
source .venv/bin/activate

# Process downgrades
python app/management/process_downgrades.py --type=downgrades

# Reset usage counters
python app/management/process_downgrades.py --type=reset
```

## Log Directory Setup

Create log directory:
```bash
sudo mkdir -p /var/log/arvalox
sudo chown $(whoami):$(whoami) /var/log/arvalox
```