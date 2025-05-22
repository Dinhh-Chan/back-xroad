# Dockerize version 7.6.1 with automatically config for X-Road

## Central Service

### Modules

- Central Server
- Management Security Server

### Start Central Service

Change IP address in `CA_HOST`, `CS_HOST` and `SSM_HOST` in `.env` file.

```bash
cd central-service
docker compose up -d
```

## Security Server

### Start Security Server

Change IP address in `CA_HOST`, `CS_HOST` and `SS_HOST` in `.env` file.

Change content in file `security-server/init/internal-anchor.xml` with the file download from Central Server

```bash
cd security-server
docker compose up -d
```
