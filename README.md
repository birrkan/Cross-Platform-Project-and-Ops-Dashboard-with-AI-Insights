

## how to start FASTAPI:
```
# while in project root:
.venv/bin/uvicorn backend.app.main:app --reload --port 3536
```

## enabling api for glpi:
https://help.glpi-project.org/tutorials/readme-1/api-v2
![enable glpi api](screenshots/glpi/1glpi-enable-api.png)
![get api token](screenshots/glpi/2glpi-get-token.png)

## glpi id and token
include the id and token in .env file
```
GLPI_CLIENT_ID=
GLPI_CLIENT_SECRET=
GLPI_USERNAME=glpi
GLPI_PASSWORD=glpi
```
