#!/bin/bash
# setup_config.sh — Interactive configuration setup for RaspberryPI_Auto
#
# This script helps set up configuration for:
# - RaspIP.py (IP monitoring)
# - sync.sh (Git sync)
# - Both systems use Gmail but with different configuration methods
#
# Usage: bash setup_config.sh

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  RaspberryPI_Auto Configuration Setup                             ║"
echo "║  Set up email for RaspIP.py and/or sync.sh                        ║"
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

# Ask what to configure
echo "What would you like to configure?"
echo "1) RaspIP.py (IP address monitoring)"
echo "2) sync.sh (GitHub synchronization)"
echo "3) Both"
echo "4) Just view current configuration"
read -p "Enter choice (1-4): " CHOICE

case $CHOICE in
    1|2|3)
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
        
        read -p "Enter recipient email address: " RECIPIENT_EMAIL
        
        if [[ ! "$RECIPIENT_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            print_error "Invalid email address format"
            exit 1
        fi
        
        read -p "Enter device name (default: $(hostname)): " DEVICE_NAME
        DEVICE_NAME="${DEVICE_NAME:-$(hostname)}"
        
        ;;
    4)
        echo ""
        echo "Current configuration files:"
        echo ""
        if [ -f "$HOME_DIR/.raspi_env" ]; then
            print_success "~/.raspi_env exists"
            echo "   Device: $(grep RASPI_IP_DEVICE_NAME ~/.raspi_env | cut -d= -f2 | tr -d '\"')"
        else
            print_warning "~/.raspi_env not found"
        fi
        
        if [ -f "$HOME_DIR/.msmtprc" ]; then
            print_success "~/.msmtprc exists"
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

# Configure RaspIP.py
if [[ "$CHOICE" == "1" || "$CHOICE" == "3" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "CONFIGURING RASPIP.PY"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    
    # Create .raspi_env file
    cat > "$HOME_DIR/.raspi_env" << EOF
#!/bin/bash
# RaspIP.py configuration
export RASPI_IP_SMTP_USER="$GMAIL_USER"
export RASPI_IP_SMTP_PASSWORD="$GMAIL_PASSWORD"
export RASPI_IP_EMAIL_FROM="$GMAIL_USER"
export RASPI_IP_EMAIL_TO="$RECIPIENT_EMAIL"
export RASPI_IP_DEVICE_NAME="$DEVICE_NAME"
export RASPI_IP_CHECK_INTERVAL_SECONDS="3600"
export RASPI_IP_STATE_FILE="$HOME_DIR/.raspi_state.json"
EOF
    
    chmod 600 "$HOME_DIR/.raspi_env"
    print_success "Created ~/.raspi_env with restrictive permissions (600)"
    
    echo ""
    print_info "To run RaspIP.py, use:"
    echo "  source ~/.raspi_env"
    echo "  python3 /path/to/Internet_Base/RaspIP.py"
    echo ""
    print_info "Or add to crontab for automatic startup:"
    echo "  @reboot source ~/.raspi_env && python3 /path/to/Internet_Base/RaspIP.py"
    echo ""
fi

# Configure sync.sh
if [[ "$CHOICE" == "2" || "$CHOICE" == "3" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "CONFIGURING SYNC.SH"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    
    # Create .msmtprc file
    cat > "$HOME_DIR/.msmtprc" << EOF
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
    print_success "Created ~/.msmtprc with restrictive permissions (600)"
    
    echo ""
    print_info "Testing msmtp configuration..."
    if echo "Test message" | msmtp -v "$RECIPIENT_EMAIL" 2>&1 | grep -q "sent"; then
        print_success "msmtp configuration works!"
    else
        print_warning "Could not verify msmtp setup, but configuration file created"
        print_info "Test with: echo 'Test' | msmtp -v $RECIPIENT_EMAIL"
    fi
    
    echo ""
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

if [[ "$CHOICE" == "1" || "$CHOICE" == "3" ]]; then
    print_success "RaspIP.py configured"
    echo "   Device: $DEVICE_NAME"
    echo "   Email To: $RECIPIENT_EMAIL"
    echo "   Config File: ~/.raspi_env"
    echo ""
fi

if [[ "$CHOICE" == "2" || "$CHOICE" == "3" ]]; then
    print_success "sync.sh configured"
    echo "   Config File: ~/.msmtprc"
    echo "   Gmail User: $GMAIL_USER"
    echo ""
fi

echo "Next steps:"
echo "1. Keep your configuration files safe (never commit to git)"
echo "2. Test the tools before running them in production"
echo "3. For RaspIP.py: source ~/.raspi_env && python3 Internet_Base/RaspIP.py"
echo "4. For sync.sh: Run sync.sh manually or set up cron job"
echo ""
print_info "See documentation for more details"
