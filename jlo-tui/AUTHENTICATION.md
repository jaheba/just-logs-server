# Authentication Guide

This guide explains the different ways to authenticate with just-logs server using jlo-tui.

## Overview

jlo-tui supports three authentication methods with different security levels and use cases.

## Method 1: Interactive Login (Most Secure)

**Best for**: Daily development work, manual testing

This is the default and most secure method. Simply run jlo-tui without any credentials:

```bash
jlo-tui
```

You'll see a login screen where you can enter:
- Username
- Password (masked with `*`)

**Pros**:
- ✅ No credentials in config files
- ✅ No credentials in shell history
- ✅ No credentials visible in process list
- ✅ Most secure option

**Cons**:
- ❌ Requires manual input each time
- ❌ Not suitable for automation

### Pre-filling Username

You can pre-fill the username in the config file or via CLI to save time:

**Config file** (`~/.config/jlo-tui/config.toml`):
```toml
server_url = "http://localhost:8000"
username = "admin"
```

**Or via CLI**:
```bash
jlo-tui --username admin
```

Only the password will be prompted.

---

## Method 2: Environment Variable (Recommended for Automation)

**Best for**: Scripts, CI/CD pipelines, automated tasks

Set the `JLO_PASSWORD` environment variable:

### One-time Use

```bash
JLO_PASSWORD="your-password" jlo-tui --username admin
```

The TUI will automatically login without prompting.

### Session-wide

```bash
export JLO_PASSWORD="your-password"
jlo-tui --username admin
```

The password remains available for the entire shell session.

### In Scripts

```bash
#!/bin/bash
# script.sh

export JLO_PASSWORD="your-password"

# Run TUI and it will auto-login
jlo-tui --username admin --server http://production:8000
```

### CI/CD Integration

**GitHub Actions**:
```yaml
- name: View logs
  env:
    JLO_PASSWORD: ${{ secrets.JLO_PASSWORD }}
  run: |
    jlo-tui --username admin --server https://logs.example.com
```

**GitLab CI**:
```yaml
view-logs:
  script:
    - export JLO_PASSWORD=$JLO_PASSWORD
    - jlo-tui --username admin --server https://logs.example.com
  variables:
    JLO_PASSWORD:
      vault: production/jlo/password
```

**Docker**:
```bash
docker run -e JLO_PASSWORD=secret myapp/jlo-tui --username admin
```

**Pros**:
- ✅ Not visible in process list
- ✅ Not stored in shell history
- ✅ Works great with secret managers
- ✅ Suitable for automation
- ✅ Can be scoped to session or process

**Cons**:
- ⚠️ Visible to other processes run by same user
- ⚠️ May be logged in system logs
- ⚠️ Requires proper secret management

---

## Method 3: Command-Line Argument (Not Recommended)

**Best for**: Quick testing only (never use in production!)

⚠️ **WARNING**: This method is **NOT SECURE** and should only be used for temporary testing.

```bash
jlo-tui --username admin --password your-password
```

**Why it's insecure**:
- ❌ **Visible in process list**: Anyone on the system can see it with `ps aux`
- ❌ **Stored in shell history**: The password remains in `~/.bash_history`
- ❌ **Visible in logs**: System logs may capture the full command
- ❌ **Screen sharing risk**: May be visible if sharing terminal

**Only use this for**:
- Testing with non-sensitive accounts
- Local development with dummy credentials
- Quick debugging (then delete from history immediately)

**Never use this for**:
- Production systems
- Shared servers
- Systems with multiple users
- Any system with real data

---

## Comparison Table

| Method | Security | Automation | Use Case |
|--------|----------|------------|----------|
| **Interactive** | ⭐⭐⭐⭐⭐ High | ❌ No | Daily development |
| **Environment Variable** | ⭐⭐⭐⭐ Good | ✅ Yes | Scripts, CI/CD |
| **CLI Argument** | ⭐ Very Low | ✅ Yes | Testing only |

---

## Best Practices

### For Development

1. **Use config file for username**:
   ```toml
   # ~/.config/jlo-tui/config.toml
   username = "admin"
   ```

2. **Let TUI prompt for password** (or use env var if you prefer)

3. **Never commit credentials** to git

### For Automation

1. **Use environment variables**:
   ```bash
   export JLO_PASSWORD="$(your-secret-manager get jlo-password)"
   jlo-tui --username admin
   ```

2. **Store secrets in proper secret managers**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - GitHub Secrets
   - Azure Key Vault
   - etc.

3. **Use least-privilege accounts** for automation

4. **Rotate credentials regularly**

### Security Checklist

- [ ] Never use CLI password argument in production
- [ ] Store passwords in secret managers, not plain text
- [ ] Use read-only accounts where possible
- [ ] Enable audit logging on the just-logs server
- [ ] Rotate credentials every 90 days
- [ ] Use different accounts for dev/staging/prod
- [ ] Clear shell history after testing with credentials
- [ ] Use HTTPS for server connections

---

## Examples

### Example 1: Development Workflow

```bash
# Config file: ~/.config/jlo-tui/config.toml
cat << EOF > ~/.config/jlo-tui/config.toml
server_url = "http://localhost:8000"
username = "admin"
EOF

# Run TUI - will prompt for password
jlo-tui
```

### Example 2: CI/CD Pipeline

```bash
#!/bin/bash
# Check logs in CI pipeline

# Get password from secret manager
export JLO_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id prod/jlo-password \
  --query SecretString \
  --output text)

# Auto-login and check for errors
jlo-tui \
  --server https://logs.production.example.com \
  --username ci-bot

# Clear password from environment
unset JLO_PASSWORD
```

### Example 3: Quick Script

```bash
#!/bin/bash
# Quick script to export today's error logs

# Set password for this script only
export JLO_PASSWORD="your-password"

# Run TUI (will auto-login)
jlo-tui \
  --username admin \
  --server http://localhost:8000

# TUI will open, you can:
# 1. Press 'f' to open filters
# 2. Select ERROR level
# 3. Choose "Last 24 hours"
# 4. Press Enter to apply
# 5. Press 'e' to export
# 6. Choose JSON
# 7. Press 'q' to quit

# Password is cleared when script exits
```

### Example 4: Multiple Environments

```bash
#!/bin/bash
# Connect to different environments

function jlo-dev() {
    export JLO_PASSWORD="dev-password"
    jlo-tui --server http://localhost:8000 --username admin
    unset JLO_PASSWORD
}

function jlo-staging() {
    export JLO_PASSWORD="$(vault read -field=password secret/staging/jlo)"
    jlo-tui --server https://logs.staging.example.com --username admin
    unset JLO_PASSWORD
}

function jlo-prod() {
    export JLO_PASSWORD="$(vault read -field=password secret/prod/jlo)"
    jlo-tui --server https://logs.production.example.com --username readonly
    unset JLO_PASSWORD
}

# Usage:
# jlo-dev
# jlo-staging
# jlo-prod
```

---

## Troubleshooting

### Password not working

1. **Check if password is set**:
   ```bash
   echo $JLO_PASSWORD  # Should show your password (be careful!)
   ```

2. **Check server connectivity**:
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **Test credentials with curl**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   ```

### Auto-login not working

Auto-login requires **both** username and password:

```bash
# ✅ This works (both provided)
JLO_PASSWORD="pass" jlo-tui --username admin

# ❌ This won't auto-login (no username)
JLO_PASSWORD="pass" jlo-tui

# ❌ This won't auto-login (no password)
jlo-tui --username admin
```

### Clearing credentials from shell history

```bash
# Clear last command from history
history -d $(history 1 | awk '{print $1}')

# Or clear entire history
history -c
```

---

## FAQ

**Q: Can I store the password in the config file?**  
A: No, this is intentionally not supported for security reasons. Use environment variables or interactive login instead.

**Q: How do I use jlo-tui in a cron job?**  
A: Use an environment variable and source it from a protected file:
```bash
# /etc/cron.d/jlo-check
0 * * * * user JLO_PASSWORD=$(cat /secure/jlo-pass) /usr/local/bin/jlo-tui --username admin
```

**Q: Is the password sent securely?**  
A: Passwords are sent via HTTPS if your server URL uses `https://`. Always use HTTPS in production.

**Q: Can I use API keys instead of passwords?**  
A: Currently, jlo-tui only supports username/password authentication. API keys are for log ingestion, not web UI access.

**Q: What if I forget my password?**  
A: Contact your just-logs administrator to reset it via the web UI or database.

---

## Summary

**Choose the right method**:
- 🏆 **Interactive**: For daily use (most secure)
- 🤖 **Environment Variable**: For automation (secure enough)
- 🚫 **CLI Argument**: Never use (except quick local tests)

**Remember**: Security is a shared responsibility. Always follow your organization's security policies and best practices.
