# RaspIP.py vs sync.sh: Configuration Comparison

## TL;DR — Shared `~/.msmtprc`, One Extra Env Var

Both tools read SMTP credentials from **the same `~/.msmtprc` file**.
The only difference is that RaspIP.py also requires the `RASPI_IP_EMAIL_TO`
environment variable (the recipient address), while sync.sh has its `TO`
address hardcoded inside the script.

---

## Side-by-Side Comparison

| Aspect | RaspIP.py | sync.sh |
|--------|-----------|---------|
| **Purpose** | Monitor IP addresses | GitHub repository sync |
| **SMTP credentials** | Reads `~/.msmtprc` | Uses msmtp with `~/.msmtprc` |
| **Recipient address** | `RASPI_IP_EMAIL_TO` env var | `TO` variable inside script |
| **Email mechanism** | Python smtplib (reads .msmtprc directly) | `mail` command via msmtp |
| **Additional config** | Optional `RASPI_IP_*` env vars | Edit variables inside sync.sh |
| **Dependencies** | Python 3.6+ | bash, msmtp package |
| **State files** | raspip_last_ips.json | sync.log |
| **Trigger** | Continuous loop (checks every N seconds) | Cron job (nightly) |

---

## Configuration Checklist

### Shared setup (required for BOTH tools)

- Create `~/.msmtprc` from the `.msmtprc.template` in the repo root
- Fill in `from`, `user`, and `password` with your Gmail credentials
- Set permissions: `chmod 600 ~/.msmtprc`
- Enable 2-Step Verification on your Gmail account
- Generate a Gmail App Password (NOT your regular password)

### Additional setup for RaspIP.py only

- Set `RASPI_IP_EMAIL_TO` environment variable (recipient address)
- Optionally set `RASPI_IP_DEVICE_NAME`, `RASPI_IP_CHECK_INTERVAL_SECONDS`, etc.

### Additional setup for sync.sh only

- Edit `TO` and `FROM` variables inside `sync.sh`
- Install msmtp: `sudo apt-get install msmtp msmtp-mta`
- Set up cron job

### Running both together

- One `~/.msmtprc` serves both tools
- Set `RASPI_IP_EMAIL_TO` for RaspIP.py
- Edit `TO`/`FROM` inside sync.sh
- They run independently and do not interfere with each other

---

## Common Mistakes to Avoid

### Mistake 1: Setting RASPI_IP_SMTP_USER / RASPI_IP_SMTP_PASSWORD env vars

```bash
# WRONG — these environment variables do not exist in the code
export RASPI_IP_SMTP_USER="your@gmail.com"
export RASPI_IP_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"

# RIGHT — put credentials in ~/.msmtprc (same as sync.sh)
# Then set only the recipient:
export RASPI_IP_EMAIL_TO="recipient@gmail.com"
```

### Mistake 2: Forgetting RASPI_IP_EMAIL_TO

```bash
# WRONG — script exits with "RASPI_IP_EMAIL_TO environment variable not set"
python3 RaspIP.py

# RIGHT
export RASPI_IP_EMAIL_TO="recipient@gmail.com"
python3 RaspIP.py
```

### Mistake 3: Using Gmail regular password

```
# WRONG — Gmail no longer allows regular passwords for SMTP
password       your_regular_gmail_password

# RIGHT — use a Gmail App Password (16 chars, no spaces required in .msmtprc)
password       abcdefghijklmnop
```

### Mistake 4: Forgetting to enable 2FA before creating App Password

```
If the "App passwords" option is missing from your Google account:
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification"
3. Return to https://myaccount.google.com/apppasswords
```

---

## Email Flow Comparison

### RaspIP.py Email Flow

```
RaspIP.py
  -> Reads ~/.msmtprc (custom Python parser)
  -> Connects to smtp.gmail.com:587 via smtplib
  -> Authenticates with user/password from .msmtprc
  -> Sends to RASPI_IP_EMAIL_TO
```

### sync.sh Email Flow

```
sync.sh
  -> Pipes message to `mail` command
  -> mail calls msmtp, which reads ~/.msmtprc
  -> Connects to smtp.gmail.com:587
  -> Sends to TO variable defined in sync.sh
```

Both tools share `~/.msmtprc` but use it via different mechanisms.

---

## Troubleshooting Quick Links

**For RaspIP.py issues:** See [SETUP_RASPIP.md](SETUP_RASPIP.md)

**For sync.sh issues:** Check your `~/.msmtprc`:

```bash
# Test msmtp configuration
echo "Test email" | msmtp -v recipient@gmail.com

# Check file exists with correct permissions
ls -la ~/.msmtprc
chmod 600 ~/.msmtprc
```

---

## Summary

| Question | Answer |
|----------|--------|
| Do I need two separate config files? | No — one `~/.msmtprc` for SMTP, plus `RASPI_IP_EMAIL_TO` env var for RaspIP.py |
| Can I use RaspIP.py without sync.sh? | Yes |
| Can I use sync.sh without RaspIP.py? | Yes |
| Will they interfere if I run both? | No |
| Do they share `~/.msmtprc`? | Yes — that is the intended design |
| Can they use the same Gmail account? | Yes — one App Password in `~/.msmtprc` serves both |
| Which should I set up first? | Set up `~/.msmtprc` first; it enables both tools |