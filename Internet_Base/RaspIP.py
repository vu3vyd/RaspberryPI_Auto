#!/usr/bin/env python3
"""Monitor Raspberry Pi IP addresses and email updates on change."""

import json
import logging
import os
import socket
import subprocess
import sys
import time
import smtplib
from email.message import EmailMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

STATE_FILE = os.getenv("RASPI_IP_STATE_FILE", "raspip_last_ips.json")
SMTP_SERVER = os.getenv("RASPI_IP_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("RASPI_IP_SMTP_PORT", "587"))
SMTP_USER = os.getenv("RASPI_IP_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("RASPI_IP_SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("RASPI_IP_EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("RASPI_IP_EMAIL_TO", "")
EMAIL_SUBJECT = os.getenv("RASPI_IP_EMAIL_SUBJECT", "Raspberry Pi IP address update")
DEVICE_NAME = os.getenv("RASPI_IP_DEVICE_NAME", socket.gethostname())
CHECK_INTERVAL_SECONDS = int(os.getenv("RASPI_IP_CHECK_INTERVAL_SECONDS", "3600"))


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
        logger.error("SMTP authentication failed. Check RASPI_IP_SMTP_USER and RASPI_IP_SMTP_PASSWORD. Error: %s", str(e))
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
    """Validate all required configuration before starting."""
    errors = []
    
    if not EMAIL_TO:
        errors.append("RASPI_IP_EMAIL_TO environment variable not set (recipient email)")
    
    if not SMTP_USER:
        errors.append("RASPI_IP_SMTP_USER environment variable not set (sender email)")
    
    if not SMTP_PASSWORD:
        errors.append("RASPI_IP_SMTP_PASSWORD environment variable not set (Gmail app password)")
    
    if not EMAIL_FROM:
        errors.append("RASPI_IP_EMAIL_FROM environment variable not set (from address)")
    
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
    logger.info("Device Name: %s", DEVICE_NAME)
    logger.info("State File: %s", os.path.abspath(STATE_FILE))
    logger.info("Check Interval: %d seconds (%d minutes)", CHECK_INTERVAL_SECONDS, CHECK_INTERVAL_SECONDS // 60)
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
