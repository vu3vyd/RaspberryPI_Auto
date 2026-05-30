#!/usr/bin/env python3
"""Monitor Raspberry Pi IP addresses and email updates on change.

Configuration: ~/.raspi_config (shared with sync.sh)
- All settings live in one file: sender, password, recipient, device name, subject
- Monitors IP addresses across all interfaces and emails on change
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
import shutil
import urllib.request
import ipaddress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.expanduser("~/.raspi_config")

# Defaults — all overridable via CONFIG_FILE
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = None
SMTP_PASSWORD = None
EMAIL_FROM = None
EMAIL_TO = None
DEVICE_NAME = socket.gethostname()
EMAIL_SUBJECT = "Raspberry Pi IP address update"
CHECK_INTERVAL_SECONDS = 3600
STATE_FILE = "raspip_last_ips.json"


def parse_config():
    """Parse ~/.raspi_config (KEY="value" format, # for comments).

    Returns dict of key/value pairs, or None if the file is missing/unreadable.
    """
    if not os.path.isfile(CONFIG_FILE):
        logger.error("Config file not found: %s", CONFIG_FILE)
        logger.error("  Create it: cp ~/RaspberryPI_Auto/raspi_config.template ~/.raspi_config")
        return None

    config = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes (single or double)
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                config[key] = value
        return config
    except Exception as e:
        logger.error("Error reading %s: %s", CONFIG_FILE, str(e))
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

    # Add router (gateway + public IP) info under a special key
    gw_v4 = get_default_gateway(False)
    gw_v6 = get_default_gateway(True)
    pub_v4 = get_public_ip(False)
    pub_v6 = get_public_ip(True)

    router_ipv4 = []
    if gw_v4:
        router_ipv4.append(gw_v4)
    if pub_v4 and pub_v4 not in router_ipv4:
        router_ipv4.append(pub_v4)

    router_ipv6 = []
    if gw_v6:
        router_ipv6.append(gw_v6)
    if pub_v6 and pub_v6 not in router_ipv6:
        router_ipv6.append(pub_v6)

    result["__router__"] = {"ipv4": router_ipv4, "ipv6": router_ipv6}

    return result



def _parse_default_gateway(output):
    # parse lines like: "default via 192.168.1.1 dev eth0"
    for line in output.splitlines():
        parts = line.split()
        if "via" in parts:
            try:
                return parts[parts.index("via") + 1]
            except Exception:
                continue
    return None


def get_default_gateway(ipv6=False):
    cmd = ["ip", "-6" if ipv6 else "-4", "route", "show", "default"]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return _parse_default_gateway(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_public_ip(ipv6=False, timeout=5):
    # Prefer curl if available so we can force -4/-6. Fall back to urllib.
    curl = shutil.which("curl")
    if curl:
        url = "https://api.ipify.org"
        args = [curl, "-s", "-4" if not ipv6 else "-6", url]
        try:
            out = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip()
            # validate
            ipaddress.ip_address(out)
            return out
        except Exception:
            pass

    # urllib fallback
    try:
        url = "https://api64.ipify.org" if ipv6 else "https://api.ipify.org"
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            out = resp.read().decode().strip()
            try:
                ipaddress.ip_address(out)
                return out
            except Exception:
                return None
    except Exception:
        return None


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
        # Keep special keys (internal/router) in original order; sort real interfaces
        if str(iface).startswith("__"):
            ipv4 = data.get("ipv4", [])
            ipv6 = data.get("ipv6", [])
        else:
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
    # Print non-router interfaces first, then router info
    keys = [k for k in state.keys() if k != "__router__"]
    for iface in sorted(keys):
        lines.append(f"Interface: {iface}")
        if state[iface].get("ipv4"):
            lines.append("  IPv4: " + ", ".join(state[iface]["ipv4"]))
        if state[iface].get("ipv6"):
            lines.append("  IPv6: " + ", ".join(state[iface]["ipv6"]))
        lines.append("")

    # Router (gateway + public)
    router = state.get("__router__")
    if router:
        lines.append("Router:")
        r4 = router.get("ipv4", [])
        if r4:
            if len(r4) >= 1:
                lines.append(f"  IPv4 Gateway: {r4[0]}")
            if len(r4) >= 2:
                lines.append(f"  IPv4 Public : {r4[1]}")
        r6 = router.get("ipv6", [])
        if r6:
            if len(r6) >= 1:
                lines.append(f"  IPv6 Gateway: {r6[0]}")
            if len(r6) >= 2:
                lines.append(f"  IPv6 Public : {r6[1]}")
        lines.append("")
    return "\n".join(lines).strip()


def send_email(subject, body):
    if not EMAIL_TO or not SMTP_USER or not SMTP_PASSWORD or not EMAIL_FROM:
        logger.error(
            "Email configuration incomplete. Missing: %s",
            ", ".join(k for k, v in [
                ("RECIPIENT_EMAIL", EMAIL_TO),
                ("SENDER_EMAIL", SMTP_USER),
                ("SMTP_PASSWORD", SMTP_PASSWORD),
            ] if not v)
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
        logger.error("SMTP authentication failed. Check SENDER_EMAIL and SMTP_PASSWORD in ~/.raspi_config. Error: %s", str(e))
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
    """Load ~/.raspi_config and validate all required settings."""
    global SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO
    global DEVICE_NAME, EMAIL_SUBJECT, CHECK_INTERVAL_SECONDS, STATE_FILE

    errors = []

    config = parse_config()
    if config is None:
        errors.append(f"Cannot read config file: {CONFIG_FILE}")
        errors.append("  Create it: cp ~/RaspberryPI_Auto/raspi_config.template ~/.raspi_config")
        errors.append("  Then edit: nano ~/.raspi_config")
    else:
        SMTP_USER  = config.get("SENDER_EMAIL", "")
        EMAIL_FROM = config.get("SENDER_EMAIL", "")
        SMTP_PASSWORD  = config.get("SMTP_PASSWORD", "")
        EMAIL_TO       = config.get("RECIPIENT_EMAIL", "")

        if config.get("DEVICE_NAME"):
            DEVICE_NAME = config["DEVICE_NAME"]
        if config.get("EMAIL_SUBJECT"):
            EMAIL_SUBJECT = config["EMAIL_SUBJECT"]
        if config.get("STATE_FILE"):
            STATE_FILE = config["STATE_FILE"]
        if config.get("CHECK_INTERVAL_SECONDS"):
            try:
                CHECK_INTERVAL_SECONDS = int(config["CHECK_INTERVAL_SECONDS"])
            except ValueError:
                errors.append("CHECK_INTERVAL_SECONDS in ~/.raspi_config must be a whole number")

    # Validate required fields
    if not SMTP_USER:
        errors.append("SENDER_EMAIL missing or empty in ~/.raspi_config")
    if not SMTP_PASSWORD:
        errors.append("SMTP_PASSWORD missing or empty in ~/.raspi_config")
    if not EMAIL_TO:
        errors.append("RECIPIENT_EMAIL missing or empty in ~/.raspi_config")

    # Verify state file directory is writable
    state_dir = os.path.dirname(STATE_FILE) or "."
    if not os.path.exists(state_dir):
        try:
            os.makedirs(state_dir, exist_ok=True)
        except OSError as e:
            errors.append(f"Cannot create state file directory {state_dir}: {e}")

    if os.path.exists(state_dir) and not os.access(state_dir, os.W_OK):
        errors.append(f"State file directory {state_dir} is not writable")

    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error("  %s", error)
        return False

    logger.info("Configuration validated successfully")
    logger.info("Config file      : %s", CONFIG_FILE)
    logger.info("Device name      : %s", DEVICE_NAME)
    logger.info("State file       : %s", os.path.abspath(STATE_FILE))
    logger.info("Check interval   : %d seconds (%d minutes)", CHECK_INTERVAL_SECONDS, CHECK_INTERVAL_SECONDS // 60)
    logger.info("SMTP server      : %s:%d", SMTP_SERVER, SMTP_PORT)
    logger.info("Sender           : %s", EMAIL_FROM)
    logger.info("Recipient        : %s", EMAIL_TO)
    logger.info("Email subject    : %s", EMAIL_SUBJECT)
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
                subject = f"{DEVICE_NAME} — {EMAIL_SUBJECT}"

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
