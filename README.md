## Technologies Used
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![OpenProject](https://img.shields.io/badge/OpenProject-0773B5?style=for-the-badge&logo=openproject&logoColor=white)
![GLPI](https://img.shields.io/badge/GLPI-0066CC?style=for-the-badge&logo=glpi&logoColor=white)
![llama.cpp](https://img.shields.io/badge/llama.cpp-000000?style=for-the-badge&logo=llama.cpp&logoColor=white)

# PROJECT DEFINITION
# Cross-Platform Project & Ops Dashboard with AI Insights:
A self-hosted AI-powered management dashboard that connects IT service management, development workflows, and organizational knowledge into a unified operational view. The platform integrates GLPI (incidents and requests), OpenProject (development tasks and project progress), and XWiki (knowledge base) to provide AI-generated summaries, trend analysis, and weekly operational reports. A locally hosted LLM analyzes data from connected systems while keeping business information private. The platform is deployed on a single server using Ansible and developed with FastAPI.

# Demo Showcase:
### Real time usage demo recording: (takes few seconds to load the gif file)
![demo](screenshots/demo.webp)
### Dashboard:
![title](screenshots/title.png)
### Summary on the Dashboard:
![summary](screenshots/summary.png)
### Project Status Report on the Dashboard:
![summary](screenshots/report.png)
### Incident analysis on the Dashboard:
![inc-analysis](screenshots/inc-analysis.png)
### Example demo Dev tasks on OpenProject:
![op-tasks](screenshots/op-tasks.png)
### Example demo incidents on GLPI:
![incidents](screenshots/incidents.png)

### FastAPI Status page:
![fastapi](screenshots/fastapi.png)

## how to start uvicorn:
```
# while in project root:
.venv/bin/uvicorn backend.app.main:app --reload --port 3536
```

```
AI Dashboard url: http://<ip address>:3536  
FastAPI url: http://<ip address>:3536/docs  
GLPI url: http://<ip address>:7001  
OpenProject url: http://<ip address>:7003  
XWiki url: http://<ip address>:7002  
```

<!--
## enabling api for glpi:
https://help.glpi-project.org/tutorials/readme-1/api-v2
![enable glpi api](screenshots/glpi-token/1glpi-enable-api.png)
![get api token](screenshots/glpi-token/2glpi-get-token.png)

## glpi id and token
include the id and token in .env file. (rename .env.example to .env)
```
GLPI_CLIENT_ID=
GLPI_CLIENT_SECRET=
GLPI_USERNAME=glpi
GLPI_PASSWORD=glpi
```-->
