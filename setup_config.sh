#!/bin/bash
# setup_config.sh — Interactive configuration setup for RaspberryPI_Auto
#
# This script helps set up the SINGLE configuration file for:
# - RaspIP.py (IP monitoring)
# - sync.sh (Git sync)
#
# Both tools use the same ~/.msmtprc file for Gmail configuration
#
# Usage: bash setup_config.sh

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  RaspberryPI_Auto Configuration Setup                             ║"
echo "║  Configure ~/.msmtprc for both RaspIP.py and sync.sh              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Detect home directory
HOME_DIR="${HOME:-~}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Ask what to do
echo "What would you like to do?"
echo "1) Create/Update ~/.msmtprc (for both RaspIP.py and sync.sh)"
echo "2) Just view current configuration"
read -p "Enter choice (1-2): " CHOICE

case $CHOICE in
    1)
        # Get Gmail credentials
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "GMAIL ACCOUNT SETUP"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        print_info "You need a Gmail account with 2-Factor Authentication enabled"
        print_info "and a Gmail App Password (NOT your regular Gmail password)"
        echo ""
        
        read -p "Enter your Gmail address: " GMAIL_USER
        
        # Validate Gmail format
        if [[ ! "$GMAIL_USER" =~ ^[a-zA-Z0-9._%+-]+@gmail\.com$ ]]; then
            print_error "Invalid Gmail address format"
            exit 1
        fi
        
        read -sp "Enter Gmail App Password (16 chars with spaces): " GMAIL_PASSWORD
        echo ""
        
        if [[ ${#GMAIL_PASSWORD} -lt 10 ]]; then
            print_error "App password seems too short (should be ~19 chars with spaces)"
            exit 1
        fi
        
        read -p "Enter recipient email address (or press Enter to skip): " RECIPIENT_EMAIL
        
        if [[ -n "$RECIPIENT_EMAIL" ]]; then
            if [[ ! "$RECIPIENT_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                print_error "Invalid email address format"
                exit 1
            fi
        fi
        
        read -p "Enter device name (default: $(hostname)): " DEVICE_NAME
        DEVICE_NAME="${DEVICE_NAME:-$(hostname)}"
        
        ;;
    2)
        echo ""
        echo "Current configuration files:"
        echo ""
        if [ -f "$HOME_DIR/.msmtprc" ]; then
            print_success "~/.msmtprc exists"
            echo "   Gmail User: $(grep '^user' ~/.msmtprc | head -1 | cut -d' ' -f2)"
            echo "   Permissions: $(stat -c '%a' ~/.msmtprc 2>/dev/null || stat -f '%A' ~/.msmtprc 2>/dev/null)"
        else
            print_warning "~/.msmtprc not found"
        fi
        
        echo ""
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Create .msmtprc file (used by both RaspIP.py and sync.sh)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "CREATING CONFIGURATION"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Create .msmtprc file
cat > "$HOME_DIR/.msmtprc" << EOF
# Gmail SMTP configuration for RaspIP.py and sync.sh
# Do NOT commit this file to git - it contains your password!

defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        ~/.msmtp.log

account        gmail
host           smtp.gmail.com
port           587
from           $GMAIL_USER
user           $GMAIL_USER
password       $GMAIL_PASSWORD

account default : gmail
EOF

chmod 600 "$HOME_DIR/.msmtprc"
print_success "Created ~/.msmtprc with secure permissions (600)"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "TESTING CONFIGURATION"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

print_info "Testing msmtp configuration..."
if echo "Test message from RaspberryPI_Auto setup" | msmtp -v "$GMAIL_USER" 2>&1 | grep -q "sent"; then
    print_success "msmtp configuration works!"
else
    print_warning "Could not verify msmtp setup, but configuration file created"
    print_info "Test later with: echo 'Test' | msmtp -v $GMAIL_USER"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

print_success "Configuration file created: ~/.msmtprc"
echo "   Gmail User: $GMAIL_USER"
if [[ -n "$RECIPIENT_EMAIL" ]]; then
    echo "   Recipient: $RECIPIENT_EMAIL"
fi
echo ""

echo "NEXT STEPS:"
echo ""
echo "1. For RaspIP.py (IP monitoring):"
echo "   export RASPI_IP_EMAIL_TO='$RECIPIENT_EMAIL'"
echo "   export RASPI_IP_DEVICE_NAME='$DEVICE_NAME'"
echo "   python3 ~/RaspberryPI_Auto/Internet_Base/RaspIP.py"
echo ""
echo "2. For sync.sh (GitHub sync):"
echo "   Edit ~/RaspberryPI_Auto/sync.sh"
echo "   Set: TO='$RECIPIENT_EMAIL'"
echo "   Then: bash ~/RaspberryPI_Auto/sync.sh"
echo ""
echo "3. To make it permanent, add to ~/.bashrc:"
echo "   export RASPI_IP_EMAIL_TO='$RECIPIENT_EMAIL'"
echo "   export RASPI_IP_DEVICE_NAME='$DEVICE_NAME'"
echo ""
print_info "See FILES_CONFIGURATION.md for more details"

