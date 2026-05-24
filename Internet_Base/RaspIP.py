#!/usr/bin/env python3
"""Monitor Raspberry Pi IP addresses and email updates on change.

Configuration: Uses ~/.msmtprc (same as sync.sh)
- Reads Gmail credentials from ~/.msmtprc
- Monitors IP addresses and sends email notifications on change
- Supports custom device naming
"""

import json
import logging
import os
import socket
import subprocess
import sys
import time
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration from environment or defaults
MSMTPRC_FILE = os.path.expanduser("~/.msmtprc")
STATE_FILE = os.getenv("RASPI_IP_STATE_FILE", "raspip_last_ips.json")
EMAIL_SUBJECT = os.getenv("RASPI_IP_EMAIL_SUBJECT", "Raspberry Pi IP address update")
DEVICE_NAME = os.getenv("RASPI_IP_DEVICE_NAME", socket.gethostname())
CHECK_INTERVAL_SECONDS = int(os.getenv("RASPI_IP_CHECK_INTERVAL_SECONDS", "3600"))

# Will be loaded from .msmtprc
SMTP_SERVER = None
SMTP_PORT = None
SMTP_USER = None
SMTP_PASSWORD = None
EMAIL_FROM = None
EMAIL_TO = None


def parse_msmtprc():
    """Parse ~/.msmtprc file using the native msmtp configuration format.

    msmtp uses its own line-oriented format (not INI), so configparser cannot
    be used. This parser handles: blank lines, #-comments (inline and full-line),
    'defaults' blocks, 'account NAME' blocks, and 'account default : NAME' aliases.

    Returns:
        dict with keys: smtp_server, smtp_port, smtp_user, smtp_password, email_from
        None if file not found or parsing fails
    """
    if not os.path.isfile(MSMTPRC_FILE):
        logger.error(".msmtprc file not found at %s", MSMTPRC_FILE)
        return None

    try:
        sections = {}
        current_section = None

        with open(MSMTPRC_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                if not line:
                    continue
                parts = line.split()
                keyword = parts[0].lower()

                if keyword == "defaults":
                    current_section = "defaults"
                    sections.setdefault(current_section, {})
                elif keyword == "account" and len(parts) >= 2:
                    if parts[1].lower() == "default":
                        continue
                    current_section = parts[1]
                    sections.setdefault(current_section, {})
                elif current_section is not None and len(parts) >= 2:
                    sections[current_section][keyword] = " ".join(parts[1:])

        # Prefer account named 'gmail'; otherwise use the first non-defaults account
        account_name = None
        if "gmail" in sections:
            account_name = "gmail"
        else:
            for name in sections:
                if name != "defaults":
                    account_name = name
                    break

        if account_name is None:
            logger.error("No account section found in .msmtprc")
            return None

        # Account values override defaults
        merged = {**sections.get("defaults", {}), **sections[account_name]}

        return {
            "smtp_server": merged.get("host", "smtp.gmail.com"),
            "smtp_port": int(merged.get("port", "587")),
            "smtp_user": merged.get("user", ""),
            "smtp_password": merged.get("password", ""),
            "email_from": merged.get("from", ""),
        }

    except Exception as e:
        logger.error("Error parsing .msmtprc: %s", str(e))
        return None


def get_ip_addresses():
    result = {}
    for version, flag in [("ipv4", "-4"), ("ipv6", "-6")]:
        try:
            output = subprocess.check_output(
                ["ip", flag, "-o", "addr", "show", "scope", "global"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            iface = parts[1]
            address = parts[3].split("/")[0]
            if iface == "lo":
                continue
            result.setdefault(iface, {"ipv4": [], "ipv6": []})
            if address not in result[iface][version]:
                result[iface][version].append(address)

    return result


def load_previous_state(path):
    if not os.path.isfile(path):
        logger.info("State file not found, starting with empty state")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            state = json.load(file)
            logger.info("Loaded previous state from %s", path)
            return state
    except (OSError, ValueError) as e:
        logger.warning("Failed to load state file %s: %s", path, str(e))
        return {}


def save_state(path, state):
    try:
        state_dir = os.path.dirname(path) or "."
        if not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2, sort_keys=True)
    except OSError as e:
        logger.error("Failed to save state file %s: %s", path, str(e))


def normalize_state(state):
    normalized = {}
    for iface, data in state.items():
        ipv4 = sorted(data.get("ipv4", []))
        ipv6 = sorted(data.get("ipv6", []))
        if ipv4 or ipv6:
            normalized[iface] = {"ipv4": ipv4, "ipv6": ipv6}
    return normalized


def addresses_changed(old, new):
    return normalize_state(old) != normalize_state(new)


def build_message(state):
    if not state:
        return f"Device: {DEVICE_NAME}\nNo global IPv4 or IPv6 addresses found."

    lines = [f"Device: {DEVICE_NAME}"]
    for iface in sorted(state):
        lines.append(f"Interface: {iface}")
        if state[iface].get("ipv4"):
            lines.append("  IPv4: " + ", ".join(state[iface]["ipv4"]))
        if state[iface].get("ipv6"):
            lines.append("  IPv6: " + ", ".join(state[iface]["ipv6"]))
        lines.append("")
    return "\n".join(lines).strip()


def send_email(subject, body):
    if not EMAIL_TO or not SMTP_USER or not SMTP_PASSWORD or not EMAIL_FROM:
        logger.error(
            "Email configuration incomplete. Missing: %s",
            ", ".join([
                "EMAIL_TO" if not EMAIL_TO else "",
                "SMTP_USER" if not SMTP_USER else "",
                "SMTP_PASSWORD" if not SMTP_PASSWORD else "",
                "EMAIL_FROM" if not EMAIL_FROM else "",
            ]).strip(", ")
        )
        return False

    try:
        message = EmailMessage()
        message["From"] = EMAIL_FROM
        message["To"] = EMAIL_TO
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(message)
        
        logger.info("Email sent successfully to %s", EMAIL_TO)
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed. Check .msmtprc credentials. Error: %s", str(e))
        return False
    except smtplib.SMTPException as e:
        logger.error("SMTP error while sending email: %s", str(e))
        return False
    except OSError as e:
        logger.error("Network error while connecting to %s:%s: %s", SMTP_SERVER, SMTP_PORT, str(e))
        return False
    except Exception as e:
        logger.error("Unexpected error sending email: %s", str(e))
        return False


def validate_configuration():
    """Validate all required configuration before starting.
    
    Loads configuration from ~/.msmtprc (same as sync.sh)
    """
    global SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO
    
    errors = []
    
    # Parse .msmtprc file
    config = parse_msmtprc()
    if config is None:
        errors.append(f"Cannot read .msmtprc from {MSMTPRC_FILE}")
        errors.append("  Create it: cp .msmtprc.template ~/.msmtprc && nano ~/.msmtprc")
        errors.append("  See: https://github.com/vu3vyd/RaspberryPI_Auto")
    else:
        SMTP_SERVER = config['smtp_server']
        SMTP_PORT = config['smtp_port']
        SMTP_USER = config['smtp_user']
        SMTP_PASSWORD = config['smtp_password']
        EMAIL_FROM = config['email_from']
        
        # EMAIL_TO can be overridden via environment variable
        if not EMAIL_TO:
            EMAIL_TO = os.getenv("RASPI_IP_EMAIL_TO", "")
    
    # Validate required fields
    if not SMTP_USER:
        errors.append(".msmtprc missing 'user' field in account section")

    if not SMTP_PASSWORD:
        errors.append(".msmtprc missing 'password' field in account section")

    if not EMAIL_FROM:
        errors.append(".msmtprc missing 'from' field in account section")
    
    if not EMAIL_TO:
        errors.append("RASPI_IP_EMAIL_TO environment variable not set (recipient email address)")
        errors.append("  Set it: export RASPI_IP_EMAIL_TO='recipient@gmail.com'")
    
    # Verify state file directory is writable
    state_dir = os.path.dirname(STATE_FILE) or "."
    if not os.path.exists(state_dir):
        try:
            os.makedirs(state_dir, exist_ok=True)
        except OSError as e:
            errors.append(f"Cannot create state file directory {state_dir}: {str(e)}")
    
    if not os.access(state_dir, os.W_OK):
        errors.append(f"State file directory {state_dir} is not writable")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error("  - %s", error)
        return False
    
    logger.info("Configuration validated successfully")
    logger.info("Configuration File: %s", MSMTPRC_FILE)
    logger.info("Device Name: %s", DEVICE_NAME)
    logger.info("State File: %s", os.path.abspath(STATE_FILE))
    logger.info("Check Interval: %d seconds (%d minutes)", CHECK_INTERVAL_SECONDS, CHECK_INTERVAL_SECONDS // 60)
    logger.info("SMTP Server: %s:%d", SMTP_SERVER, SMTP_PORT)
    logger.info("From: %s", EMAIL_FROM)
    logger.info("To: %s", EMAIL_TO)
    return True


def main():
    if not validate_configuration():
        logger.error("Cannot start RaspIP monitor due to configuration errors")
        sys.exit(1)
    
    logger.info("Starting RaspIP monitor for device: %s", DEVICE_NAME)
    previous = load_previous_state(STATE_FILE)
    
    while True:
        try:
            current = get_ip_addresses()
            if addresses_changed(previous, current):
                logger.info("IP address change detected")
                body = f"IP address change detected on {DEVICE_NAME}.\n\n" + build_message(current)
                subject = EMAIL_SUBJECT.replace("Raspberry Pi", DEVICE_NAME) if "Raspberry Pi" in EMAIL_SUBJECT else f"{DEVICE_NAME} - {EMAIL_SUBJECT}"
                
                if send_email(subject, body):
                    save_state(STATE_FILE, current)
                    previous = current
                else:
                    logger.warning("Email send failed, not updating state file")
            
            time.sleep(CHECK_INTERVAL_SECONDS)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down gracefully")
            break
        except Exception as e:
            logger.error("Unexpected error in main loop: %s", str(e), exc_info=True)
            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
