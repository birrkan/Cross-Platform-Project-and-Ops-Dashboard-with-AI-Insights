#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# establish-ssh-connection.sh — Set up SSH key for Ansible
# ─────────────────────────────────────────────────────────
# Run this once before using Ansible.
# It generates an SSH key (if missing) and copies it to the server.
#
# Usage: bash ansible/establish-ssh-connection.sh
# ─────────────────────────────────────────────────────────

set -e

SERVER_IPS=(
    "192.168.122.10"
)

SERVER_USER="debian"
SSH_KEY="${HOME}/.ssh/id_ed25519"

echo "=== Step 1: Check for existing SSH key ==="
if [ -f "${SSH_KEY}" ]; then
    echo "SSH key found at ${SSH_KEY}"
else
    echo "No SSH key found. Generating one..."
    ssh-keygen -t ed25519 -f "${SSH_KEY}" -N ""
    echo "SSH key generated."
fi

echo ""
echo "=== Step 2: Copy public key to all servers ==="
for IP in "${SERVER_IPS[@]}"; do
    echo "--- Copying key to ${SERVER_USER}@${IP} ---"
    ssh-copy-id -o StrictHostKeyChecking=accept-new "${SERVER_USER}@${IP}"
done

echo ""
echo "=== Step 3: Test passwordless login on all servers ==="
for IP in "${SERVER_IPS[@]}"; do
    echo "--- Testing ${SERVER_USER}@${IP} ---"
    ssh "${SERVER_USER}@${IP}" "echo 'Connection successful.'"
done

echo ""
echo "=== Done ==="
