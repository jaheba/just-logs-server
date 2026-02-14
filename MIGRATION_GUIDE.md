# Migration Guide: Environment Variable Security Updates

**Date:** February 14, 2026  
**Version:** 1.0 → 1.1 (Security Hardening)

---

## Overview

This guide helps you migrate from the previous version to the new security-hardened version that requires environment variables for sensitive configuration.

### What Changed?

**Critical Security Fixes:**
1. ✅ **JWT Secret Key** now requires `JLO_SECRET_KEY` environment variable
2. ✅ **Admin Password** now requires `JLO_ADMIN_PASSWORD` environment variable (first-time setup only)
3. ✅ **Secure Cookies** automatically enabled in production
4. ✅ **Rate Limiting** added to prevent brute force attacks
5. ✅ **SQL Injection Protection** added to tag filtering

**Why?**
- Hardcoded credentials in code are a **critical security vulnerability**
- `.secret_key` files in Docker images expose JWT signing keys
- Environment variables allow secure secret management

---

## Quick Start (New Deployments)

### 1. Generate Secrets

```bash
# Generate JWT secret key
export JLO_SECRET_KEY=$(openssl rand -hex 32)

# Set admin password
export JLO_ADMIN_PASSWORD="YourSecurePasswordHere123!"

# Save to .env file for persistence
echo "JLO_SECRET_KEY=$JLO_SECRET_KEY" > .env
echo "JLO_ADMIN_PASSWORD=$JLO_ADMIN_PASSWORD" >> .env
echo "JLO_ENV=production" >> .env
```

### 2. Start the Application

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or manually
export $(cat .env | xargs)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. First Login

1. Navigate to `https://yourdomain.com` (or `http://localhost:8000` in dev)
2. Login with username: `admin` and the password you set
3. **Change your password immediately** via Settings → Change Password

---

## Migration for Existing Deployments

### Before You Start

⚠️ **IMPORTANT:** Back up your database before migrating!

```bash
# Backup database
cp backend/jlo.db backend/jlo.db.backup

# Or if using Docker volume
docker run --rm -v jlo-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/jlo-data-backup.tar.gz /data
```

### Step 1: Extract Existing Secret Key

If you have an existing `.secret_key` file, extract it:

```bash
cd backend

# Extract existing secret key
if [ -f .secret_key ]; then
  export JLO_SECRET_KEY=$(cat .secret_key)
  echo "Extracted JLO_SECRET_KEY: $JLO_SECRET_KEY"
else
  echo "No .secret_key found. Generating new one..."
  export JLO_SECRET_KEY=$(openssl rand -hex 32)
fi

# Save to .env file
cd ..
echo "JLO_SECRET_KEY=$JLO_SECRET_KEY" > .env
```

⚠️ **WARNING:** If you generate a new secret key, **all existing user sessions will be invalidated** and users will need to log in again.

### Step 2: Set Admin Password

**Option A: Keep existing admin password**

If you know the current admin password:
```bash
echo "JLO_ADMIN_PASSWORD=your_current_password" >> .env
```

**Option B: Reset admin password**

If you forgot the admin password or want to change it:

```bash
# Set new admin password in .env
echo "JLO_ADMIN_PASSWORD=NewSecurePassword123!" >> .env

# Delete the existing admin user from database
sqlite3 backend/jlo.db "DELETE FROM web_users WHERE username='admin';"

# On next startup, a new admin user will be created with the new password
```

### Step 3: Update Docker Configuration (if using Docker)

```bash
# Pull latest image or rebuild
docker-compose pull  # If using pre-built images
# OR
docker-compose build  # If building locally

# Restart with new configuration
docker-compose down
docker-compose up -d
```

### Step 4: Verify Migration

```bash
# Check logs for successful startup
docker-compose logs -f

# You should see:
# ✅ Created admin user (username: admin)

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Should return: {"message":"Login successful", ...}
```

### Step 5: Clean Up (Optional but Recommended)

After verifying everything works:

```bash
# Remove .secret_key file (no longer needed)
rm backend/.secret_key

# Secure .env file permissions
chmod 600 .env

# Add .env to .gitignore (if not already there)
echo ".env" >> .gitignore
```

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example | Required? |
|----------|-------------|---------|-----------|
| `JLO_SECRET_KEY` | JWT signing key | Generated with `openssl rand -hex 32` | ✅ Yes (fails to start without it) |
| `JLO_ADMIN_PASSWORD` | Admin user password | `SecurePassword123!` | ⚠️  Only for first-time setup |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `JLO_ENV` | Environment mode | `production` | `development` or `production` |
| `JLO_HOST` | Bind address | `0.0.0.0` | `127.0.0.1` |
| `JLO_PORT` | Server port | `8000` | `3000` |
| `JLO_WORKERS` | Uvicorn workers | `4` | `2` |
| `JLO_DB_PATH` | Database file path | `jlo.db` | `/data/jlo.db` |

---

## Deployment Scenarios

### Scenario 1: Local Development

```bash
# .env file
JLO_SECRET_KEY=dev-secret-key-not-for-production
JLO_ADMIN_PASSWORD=admin123
JLO_ENV=development  # Allows HTTP cookies

# Start server
cd backend
uvicorn main:app --reload
```

### Scenario 2: Docker Compose Production

```yaml
# docker-compose.yml
services:
  jlo:
    image: jlo:latest
    environment:
      - JLO_SECRET_KEY=${JLO_SECRET_KEY}
      - JLO_ADMIN_PASSWORD=${JLO_ADMIN_PASSWORD}
      - JLO_ENV=production
```

```bash
# .env file (not committed to git)
JLO_SECRET_KEY=<generated-with-openssl>
JLO_ADMIN_PASSWORD=<strong-password>
JLO_ENV=production
```

### Scenario 3: Kubernetes / Cloud

```yaml
# Create secret
apiVersion: v1
kind: Secret
metadata:
  name: jlo-secrets
type: Opaque
stringData:
  jlo-secret-key: "<generated-with-openssl>"
  jlo-admin-password: "<strong-password>"

---
# Use in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jlo
spec:
  template:
    spec:
      containers:
      - name: jlo
        image: jlo:latest
        env:
        - name: JLO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jlo-secrets
              key: jlo-secret-key
        - name: JLO_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: jlo-secrets
              key: jlo-admin-password
        - name: JLO_ENV
          value: "production"
```

### Scenario 4: AWS ECS / Fargate

```json
{
  "containerDefinitions": [{
    "name": "jlo",
    "image": "jlo:latest",
    "secrets": [
      {
        "name": "JLO_SECRET_KEY",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:jlo/secret-key"
      },
      {
        "name": "JLO_ADMIN_PASSWORD",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:jlo/admin-password"
      }
    ],
    "environment": [
      {
        "name": "JLO_ENV",
        "value": "production"
      }
    ]
  }]
}
```

---

## Troubleshooting

### Problem: "JLO_SECRET_KEY environment variable not set!"

**Solution:**
```bash
# Generate and set secret key
export JLO_SECRET_KEY=$(openssl rand -hex 32)
echo "JLO_SECRET_KEY=$JLO_SECRET_KEY" >> .env

# Restart application
docker-compose restart
```

### Problem: "WARNING: No admin user exists and JLO_ADMIN_PASSWORD not set!"

**Solution:**
```bash
# Set admin password
export JLO_ADMIN_PASSWORD="YourSecurePassword123!"
echo "JLO_ADMIN_PASSWORD=$JLO_ADMIN_PASSWORD" >> .env

# Restart application
docker-compose restart
```

### Problem: All users logged out after migration

**Cause:** JWT secret key changed, invalidating all existing sessions.

**Solution:** Users need to log in again. This is expected and secure behavior.

### Problem: "Using legacy .secret_key file" warning

**Solution:**
```bash
# Extract secret to environment variable
export JLO_SECRET_KEY=$(cat backend/.secret_key)
echo "JLO_SECRET_KEY=$JLO_SECRET_KEY" >> .env

# Remove legacy file
rm backend/.secret_key

# Restart application
docker-compose restart
```

### Problem: Rate limiting blocking legitimate users

**Symptoms:** HTTP 429 errors, "Rate limit exceeded"

**Solution:**
```bash
# Check rate limits in backend/main.py:
# - Login: 5 attempts/minute
# - Password change: 10/minute
# - Log ingestion: 1000/minute

# For higher limits in trusted networks, modify backend/main.py:
# @limiter.limit("10/minute")  # Increase from 5 to 10
```

---

## Security Checklist

After migration, verify:

- [ ] ✅ `JLO_SECRET_KEY` is set via environment variable
- [ ] ✅ `JLO_ADMIN_PASSWORD` is set and secure (12+ chars, mixed case, numbers, symbols)
- [ ] ✅ `.env` file has restrictive permissions (`chmod 600 .env`)
- [ ] ✅ `.env` is in `.gitignore` (not committed to version control)
- [ ] ✅ `.secret_key` file removed from backend directory
- [ ] ✅ `.dockerignore` excludes `.secret_key` and `*.db` files
- [ ] ✅ Admin password changed after first login
- [ ] ✅ All users can log in successfully
- [ ] ✅ Rate limiting is working (test with 6+ rapid login attempts)
- [ ] ✅ HTTPS is enabled in production (`JLO_ENV=production`)

---

## Rollback Plan

If you need to rollback to the previous version:

### Step 1: Restore Database Backup
```bash
# Stop application
docker-compose down

# Restore database
cp backend/jlo.db.backup backend/jlo.db

# Or restore from volume backup
tar xzf jlo-data-backup.tar.gz -C /
```

### Step 2: Restore .secret_key File
```bash
# If you kept the original secret key
echo "$JLO_SECRET_KEY" > backend/.secret_key
```

### Step 3: Checkout Previous Version
```bash
git checkout <previous-commit-hash>
docker-compose build
docker-compose up -d
```

---

## FAQ

### Q: Do I need to set JLO_ADMIN_PASSWORD after the initial setup?

**A:** No. `JLO_ADMIN_PASSWORD` is **only used when creating the initial admin user**. If the admin user already exists, this variable is ignored. You can safely leave it unset after first startup or use it to recreate the admin user if needed.

### Q: What happens if I change JLO_SECRET_KEY after deployment?

**A:** All existing JWT tokens (user sessions) will become invalid, and all users will need to log in again. Only change this if you suspect the key has been compromised.

### Q: Can I use the same secrets across multiple environments?

**A:** **NO!** Each environment (dev, staging, production) should have its own unique `JLO_SECRET_KEY` and `JLO_ADMIN_PASSWORD`. Never share secrets between environments.

### Q: How do I rotate the JWT secret key?

**A:**
```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update .env file
sed -i "s/JLO_SECRET_KEY=.*/JLO_SECRET_KEY=$NEW_SECRET/" .env

# 3. Restart application (all users will be logged out)
docker-compose restart

# 4. Notify users to log in again
```

### Q: Is it safe to store secrets in .env files?

**A:** For small deployments, yes, if you:
- Set proper file permissions (`chmod 600 .env`)
- Never commit to version control (`.gitignore`)
- Restrict server access

For production, consider using dedicated secrets management:
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets
- Azure Key Vault
- Google Cloud Secret Manager

---

## Support

If you encounter issues during migration:

1. Check application logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test with curl commands (examples in Step 4 above)
4. Open an issue on GitHub with logs and configuration (redact secrets!)

---

## Version Compatibility

| Version | .secret_key File | Environment Variables | Notes |
|---------|------------------|----------------------|-------|
| ≤ 1.0 | ✅ Required | ❌ Not supported | Insecure |
| 1.1+ | ⚠️  Fallback only | ✅ Required | Secure (this version) |

**Recommendation:** Migrate to environment variables immediately for security.

---

**Status:** ✅ Migration guide complete  
**Next:** Follow steps above to secure your deployment
