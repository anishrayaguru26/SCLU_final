# SCLU Deployment Guide

## Production Deployment Checklist

### Prerequisites
- [ ] Python 3.8+ installed
- [ ] Active Zerodha trading account
- [ ] Kite Connect API subscription
- [ ] Sufficient capital for trading
- [ ] Risk management plan approved

### Environment Setup

#### 1. System Requirements
```bash
# Minimum System Requirements
- CPU: 2+ cores
- RAM: 4GB (8GB recommended)
- Storage: 10GB free space
- Network: Stable internet connection (low latency preferred)
- OS: Linux/macOS/Windows
```

#### 2. Python Environment
```bash
# Create virtual environment
python -m venv sclu_env
source sclu_env/bin/activate  # On Windows: sclu_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

#### 3. Configuration Setup
```bash
# Copy configuration templates
cp config/production.yaml config/production-live.yaml
cp config/env.example .env

# Edit configuration files
nano .env  # Add your API credentials
nano config/production-live.yaml  # Adjust trading parameters
```

### API Configuration

#### 1. Zerodha Kite Connect Setup
1. Log in to [Kite Connect Developer Console](https://developers.kite.trade/)
2. Create a new app or use existing app
3. Note down your API Key and API Secret
4. Generate access token (manual process for now)

#### 2. Environment Variables
```bash
# Required credentials
SCLU_API_KEY=your_kite_api_key_here
SCLU_ACCESS_TOKEN=your_access_token_here

# Optional settings
SCLU_ENVIRONMENT=production
SCLU_LOG_LEVEL=INFO
SCLU_DRY_RUN_MODE=false  # Set to true for paper trading
```

### Security Considerations

#### 1. Credential Management
- Store API credentials in environment variables, not files
- Use secure key management systems in production
- Rotate access tokens regularly
- Monitor API usage for unusual activity

#### 2. System Security
```bash
# Set proper file permissions
chmod 600 .env
chmod 600 config/production-live.yaml

# Create non-root user for trading
sudo useradd -m sclu_trader
sudo usermod -aG sclu_trader sclu_trader
```

### Pre-Deployment Testing

#### 1. Backtesting Validation
```bash
# Run comprehensive backtests
python scripts/run_backtest.py data/historical/sample_data.csv \
    --config config/production-live.yaml \
    --cash 100000 \
    --plot

# Validate different market conditions
python scripts/run_backtest.py data/historical/trending_market.csv
python scripts/run_backtest.py data/historical/sideways_market.csv
python scripts/run_backtest.py data/historical/volatile_market.csv
```

#### 2. Paper Trading Phase
```bash
# Run in dry-run mode for at least 1 week
python scripts/live_trading.py \
    --dry-run \
    --config config/production-live.yaml

# Monitor logs and performance
tail -f logs/sclu_production.log
```

#### 3. API Connectivity Testing
```bash
# Test API connection
python -c "
from src.sclu.api import KiteClient
from src.sclu.utils import Config

config = Config('config/production-live.yaml')
client = KiteClient(
    config.get('api', 'api_key'),
    config.get('api', 'access_token')
)

# Test basic connectivity
instruments = client.get_instruments()
print(f'Successfully connected. Loaded {len(instruments)} instruments.')

# Test data fetching
data = client.fetch_historical_data(10716162, 5)
print(f'Historical data test: {len(data)} records fetched.')
"
```

### Production Deployment

#### 1. Infrastructure Setup

##### Cloud Deployment (Recommended)
```bash
# AWS EC2 / Google Cloud / DigitalOcean
# Minimum t3.small or equivalent instance
# Ubuntu 20.04 LTS recommended

# Install dependencies
sudo apt update
sudo apt install -y python3.8 python3-pip python3-venv git
git clone https://github.com/yourusername/SCLU.git
cd SCLU
```

##### Local Deployment
```bash
# Ensure stable power and internet
# Use UPS for power backup
# Configure automatic restarts

# Create systemd service (Linux)
sudo cp deployment/sclu-trading.service /etc/systemd/system/
sudo systemctl enable sclu-trading
sudo systemctl start sclu-trading
```

#### 2. Process Management

##### Using systemd (Linux)
```bash
# /etc/systemd/system/sclu-trading.service
[Unit]
Description=SCLU Trading System
After=network.target

[Service]
Type=simple
User=sclu_trader
WorkingDirectory=/home/sclu_trader/SCLU
Environment=PATH=/home/sclu_trader/SCLU/sclu_env/bin
ExecStart=/home/sclu_trader/SCLU/sclu_env/bin/python scripts/live_trading.py --config config/production-live.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

##### Using PM2 (Node.js)
```bash
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### 3. Monitoring Setup

##### Log Monitoring
```bash
# Centralized logging with rsyslog
echo "local0.*    /var/log/sclu.log" >> /etc/rsyslog.conf
sudo systemctl restart rsyslog

# Log rotation
sudo cp deployment/sclu-logrotate /etc/logrotate.d/sclu
```

##### Performance Monitoring
```bash
# System monitoring
pip install psutil
python scripts/monitor_system.py &

# Trading performance monitoring
python scripts/monitor_trading.py &
```

##### Alerting
```bash
# Email alerts for critical issues
pip install yagmail
python scripts/alert_manager.py &

# Slack/Discord webhooks for notifications
# Configure in .env file
```

### Risk Management in Production

#### 1. Position Limits
```yaml
# config/production-live.yaml
trading:
  max_daily_trades: 20          # Conservative limit
  max_portfolio_risk: 0.015     # 1.5% max portfolio risk
  position_size_pct: 0.05       # 5% position sizes
  emergency_stop_loss: 0.15     # 15% emergency stop
```

#### 2. Circuit Breakers
```yaml
live_trading:
  max_daily_loss: 5000.0        # Maximum daily loss
  max_consecutive_losses: 3     # Stop after 3 consecutive losses
  enable_alerts: true           # Enable all alerts
  heartbeat_interval: 300       # 5-minute heartbeat
```

#### 3. Manual Override
```bash
# Emergency stop script
python scripts/emergency_stop.py

# Position cleanup
python scripts/close_all_positions.py

# System status check
python scripts/health_check.py
```

### Monitoring and Maintenance

#### 1. Daily Checks
- [ ] System is running and responsive
- [ ] No error messages in logs
- [ ] API connectivity is stable
- [ ] Positions are within limits
- [ ] P&L tracking is accurate

#### 2. Weekly Reviews
- [ ] Performance analysis
- [ ] Parameter optimization review
- [ ] Risk metrics evaluation
- [ ] System resource usage
- [ ] Log file cleanup

#### 3. Monthly Maintenance
- [ ] Full system backup
- [ ] Security updates
- [ ] Performance benchmarking
- [ ] Strategy review and optimization
- [ ] Hardware health check

### Troubleshooting Guide

#### Common Issues

##### API Connection Problems
```bash
# Check network connectivity
ping api.kite.trade

# Verify credentials
python scripts/test_api_connection.py

# Check rate limits
grep "rate limit" logs/sclu_production.log
```

##### Strategy Not Trading
```bash
# Check market hours
python -c "from datetime import datetime; print(datetime.now().strftime('%H:%M'))"

# Verify data feed
python scripts/test_data_feed.py

# Check signal generation
python scripts/debug_signals.py
```

##### Performance Issues
```bash
# System resources
top -p $(pgrep -f live_trading.py)

# Memory usage
python scripts/memory_profiler.py

# Network latency
python scripts/latency_test.py
```

### Backup and Recovery

#### 1. Configuration Backup
```bash
# Automated daily backup
0 2 * * * /home/sclu_trader/scripts/backup_config.sh

# Configuration versioning
git add config/
git commit -m "Daily config backup"
git push origin backup-branch
```

#### 2. Data Backup
```bash
# Trade logs and performance data
rsync -av logs/ /backup/sclu/logs/
rsync -av data/ /backup/sclu/data/

# Database backup (if using)
pg_dump sclu_db > /backup/sclu/db_$(date +%Y%m%d).sql
```

#### 3. Disaster Recovery
```bash
# Quick restoration script
./scripts/restore_from_backup.sh /backup/sclu/latest/

# Emergency trading halt
./scripts/emergency_stop.sh

# System recovery checklist
./scripts/recovery_checklist.sh
```

### Performance Optimization

#### 1. System Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Network optimization
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf
```

#### 2. Application Optimization
```python
# Use connection pooling
# Optimize data structures
# Cache frequently accessed data
# Minimize disk I/O operations
```

### Compliance and Audit Trail

#### 1. Regulatory Compliance
- Maintain detailed trade logs
- Implement audit trails
- Ensure data retention policies
- Regular compliance reviews

#### 2. Audit Trail
```bash
# All trades logged with timestamps
# Decision rationale recorded
# System changes tracked
# Performance metrics stored
```

---

## Emergency Procedures

### Emergency Stop
```bash
# Immediate system halt
sudo systemctl stop sclu-trading

# Close all positions (if needed)
python scripts/emergency_close_positions.py

# Send alert notifications
python scripts/send_emergency_alert.py
```

### Contact Information
- **System Administrator**: [your-email@domain.com]
- **Risk Manager**: [risk@domain.com]
- **Emergency Contact**: [emergency@domain.com]

---

**Remember**: Always test thoroughly before deploying to production. Start with small position sizes and gradually increase as confidence builds.
