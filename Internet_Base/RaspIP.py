#!/usr/bin/env python3
"""Monitor Raspberry Pi IP addresses and email updates on change."""

import json
import os
import socket
import subprocess
import time
import smtplib
from email.message import EmailMessage

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
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


def save_state(path, state):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2, sort_keys=True)
    except OSError:
        pass


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
        return

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


def main():
    previous = load_previous_state(STATE_FILE)
    while True:
        current = get_ip_addresses()
        if addresses_changed(previous, current):
            body = f"IP address change detected on {DEVICE_NAME}.\n\n" + build_message(current)
            subject = EMAIL_SUBJECT.replace("Raspberry Pi", DEVICE_NAME) if "Raspberry Pi" in EMAIL_SUBJECT else f"{DEVICE_NAME} - {EMAIL_SUBJECT}"
            send_email(subject, body)
            save_state(STATE_FILE, current)
            previous = current
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
