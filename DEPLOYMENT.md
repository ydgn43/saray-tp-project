# Production Deployment Guide

This guide walks you through deploying the Smart Restroom Management System to a production server.

## Prerequisites

- Ubuntu/Debian server (or similar Linux distribution)
- Root or sudo access
- Python 3.8 or higher
- Domain name (optional but recommended)

## Step-by-Step Deployment

### 1. Prepare Your Server

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx git
```

### 2. Transfer Project Files

**Option A: Using Git (Recommended)**
```bash
cd /home/yourusername
git clone https://github.com/yourusername/test_esp32.git
cd test_esp32
```

**Option B: Using SCP from Windows**
```powershell
# From your local machine (PowerShell)
scp -r C:\Users\ydgn4\Desktop\test_esp32 user@your-server-ip:/home/user/
```

### 3. Set Up Python Environment

```bash
cd /home/yourusername/test_esp32

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn
```

### 4. Configure Firebase (If Using)

```bash
# Upload your Firebase credentials securely
# From Windows:
scp firebase-credentials.json user@your-server-ip:/home/user/test_esp32/

# Set proper permissions
chmod 600 firebase-credentials.json
```

Edit `server.py` and update the Firebase database URL:
```python
'databaseURL': 'https://your-project-id.firebaseio.com/'
```

### 5. Test the Application

```bash
# Test with development server
python server.py

# Test with Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 wsgi:app
```

Visit `http://your-server-ip:5000` to verify it works.

### 6. Set Up System Service

```bash
# Edit the service file with correct paths
nano restroom-system.service

# Update these values:
# - User=YOUR_USERNAME (e.g., User=ubuntu)
# - WorkingDirectory=/path/to/test_esp32 (e.g., /home/ubuntu/test_esp32)
# - Environment="PATH=/path/to/.venv/bin" (e.g., /home/ubuntu/test_esp32/.venv/bin)
# - ExecStart=/path/to/.venv/bin/gunicorn... (update full path)

# Copy to systemd
sudo cp restroom-system.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable restroom-system

# Start the service
sudo systemctl start restroom-system

# Check status
sudo systemctl status restroom-system
```

### 7. Configure Nginx

```bash
# Edit nginx configuration with your domain
nano nginx.conf

# Update:
# - server_name your-domain.com (or use server IP)
# - Static files path if needed

# Copy to Nginx sites
sudo cp nginx.conf /etc/nginx/sites-available/restroom-system

# Create symbolic link
sudo ln -s /etc/nginx/sites-available/restroom-system /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 8. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 9. Set Up SSL (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Certificate will auto-renew
# Test renewal
sudo certbot renew --dry-run
```

### 10. Update ESP32 Code

Update the server URL in your ESP32 code:
```cpp
const char* SERVER_URL = "https://your-domain.com/report";
// or
const char* SERVER_URL = "http://your-server-ip/report";
```

## Maintenance Commands

### View Logs
```bash
# Application logs
sudo journalctl -u restroom-system -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart application
sudo systemctl restart restroom-system

# Restart Nginx
sudo systemctl restart nginx
```

### Update Application
```bash
cd /home/yourusername/test_esp32

# Pull latest changes (if using git)
git pull

# Activate virtual environment
source .venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart restroom-system
```

### Check Status
```bash
# Application status
sudo systemctl status restroom-system

# Nginx status
sudo systemctl status nginx

# Check if port is listening
sudo netstat -tlnp | grep 5000
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u restroom-system -n 50

# Check file permissions
ls -la /home/yourusername/test_esp32

# Verify Python path
which python3
/home/yourusername/test_esp32/.venv/bin/python --version
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### WebSocket Connection Issues
- Ensure Nginx properly forwards WebSocket connections
- Check firewall allows connections
- Verify `proxy_http_version 1.1` in Nginx config

### ESP32 Can't Connect
- Verify server URL is correct
- Check firewall allows connections on port 80/443
- Ensure room_id exists in database
- Check application logs for errors

## Security Best Practices

1. **Keep system updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Set up SSH key authentication** (disable password login)

3. **Configure fail2ban**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

4. **Regular backups**
   - Firebase automatically backs up data
   - Backup `rooms_data.json` if using local storage

5. **Monitor resources**
   ```bash
   htop
   df -h
   ```

## Performance Optimization

1. **Use Nginx for static files** (already configured in nginx.conf)

2. **Enable Gzip compression** in Nginx:
   ```nginx
   gzip on;
   gzip_types text/css application/javascript;
   ```

3. **Monitor with systemd**:
   The service will automatically restart if it crashes

4. **Database indexing** (Firebase automatically optimizes)

## Environment Variables (Optional)

For better security, use environment variables:

```bash
# Create .env file
nano .env
```

Add:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=https://your-firebase-url.firebaseio.com/
```

Update `server.py` to read from environment:
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
```

Install python-dotenv:
```bash
pip install python-dotenv
```

## Support

If you encounter issues:
1. Check logs first
2. Verify all paths in configuration files
3. Ensure all services are running
4. Test with development server first

## Quick Reference

**Start Service:**
```bash
sudo systemctl start restroom-system
```

**Stop Service:**
```bash
sudo systemctl stop restroom-system
```

**View Logs:**
```bash
sudo journalctl -u restroom-system -f
```

**Restart After Changes:**
```bash
sudo systemctl restart restroom-system
```

Your system is now production-ready! 🚀
