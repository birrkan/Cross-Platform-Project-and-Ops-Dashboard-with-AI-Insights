#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# run-ansible.sh — Run Ansible playbooks step by step
# ─────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 00-bootstrap: Create ansible user ==="
ansible-playbook -i inventory/bootstrap.yml playbooks/00-bootstrap.yml --ask-vault-pass

# from here on, playbooks will use the ansible user as
# ansible.cfg sets it as default

echo ""
echo "=== 01-docker: Install Docker ==="
ansible-playbook playbooks/01-docker.yml

echo ""
echo "=== 02-llamacpp: Install llama.cpp ==="
ansible-playbook playbooks/02-llamacpp.yml

echo ""
echo "=== 03-postgres: Deploy PostgreSQL ==="
ansible-playbook playbooks/03-postgres.yml --ask-vault-pass
