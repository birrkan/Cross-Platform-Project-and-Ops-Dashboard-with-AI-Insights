# Ansible — How to run playbooks

## Prerequisites

On your **dev machine** (where you run commands):

```bash
# 1. Install Ansible
pip install ansible

# 2. Install the Docker collection (needed by docker role)
ansible-galaxy collection install -r ansible/requirements.yml
```

## Run a playbook

```bash
cd /home/birkan/Programs/codes-and-stuff/ai-ops-project/ai-ops-project

# Install Docker on the server
ansible-playbook -i ansible/inventory/server.yml ansible/playbooks/00-bootstrap.yml
```

Replace `00-bootstrap.yml` with the playbook you want to run.

## Playbook order

| # | Playbook | What it does |
|---|---|---|
| 00 | bootstrap.yml | Create ansible user + sudo + SSH key |
| 01 | docker.yml | Install Docker + create ai-ops-net network |
| 02 | llamacpp.yml | Install llama.cpp natively + systemd service |
| 03 | postgres.yml | Deploy PostgreSQL (PGVector) container |
| 04 | glpi.yml | Deploy GLPI + MariaDB containers |
| 05 | xwiki.yml | Deploy XWiki + DB containers |
| 06 | openproject.yml | Deploy OpenProject + DB containers |

## Verify a playbook without running it

```bash
ansible-playbook -i ansible/inventory/server.yml ansible/playbooks/00-bootstrap.yml --check
```
