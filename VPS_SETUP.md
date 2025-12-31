# IA Trading - VPS Deployment

## Arquitectura

```
Push a master → GitHub Actions → Build imagen → Push a ghcr.io → SSH al VPS → docker run
```

- El código se compila en GitHub Actions
- La imagen se sube a GitHub Container Registry (ghcr.io)
- GitHub Actions se conecta por SSH al VPS y ejecuta `docker run`
- No se requiere docker-compose en el VPS

## Infraestructura actual

- **VPS:** IONOS Debian 12
- **IP:** 195.20.235.94
- **Puerto:** 80 (HTTP)
- **API URL:** http://195.20.235.94

## Secrets de GitHub

En el repositorio: **Settings → Secrets and variables → Actions**

| Secret | Descripción |
|--------|-------------|
| `VPS_HOST` | IP del VPS (195.20.235.94) |
| `VPS_USER` | Usuario SSH (root) |
| `VPS_SSH_KEY` | Clave SSH privada para conectarse al VPS |
| `GHCR_TOKEN` | Personal Access Token con permisos `read:packages`, `write:packages` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL |
| `ALPHA_VANTAGE_API_KEY` | API key de Alpha Vantage |
| `GEMINI_API_KEY` | API key de Google Gemini |

## Despliegue automático

Cada push a `master` dispara el workflow que:

1. Construye la imagen Docker
2. La sube a ghcr.io/josefinolis/ia-investing
3. Se conecta al VPS por SSH
4. Para y elimina el contenedor anterior
5. Ejecuta el nuevo contenedor
6. Verifica el health check

## Comandos útiles en el VPS

```bash
# Ver contenedores
docker ps -a

# Ver logs del API
docker logs ia-trading-api -f

# Ver logs de PostgreSQL
docker logs ia-trading-db -f

# Reiniciar API
docker restart ia-trading-api

# Parar todo
docker stop ia-trading-api ia-trading-db

# Backup de la base de datos
docker exec ia-trading-db pg_dump -U ia_trading ia_trading > backup.sql

# Restaurar backup
docker exec -i ia-trading-db psql -U ia_trading ia_trading < backup.sql
```

## Configuración inicial del VPS (solo primera vez)

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Crear red de Docker
docker network create ia-trading-network

# Crear volumen para PostgreSQL
docker volume create ia-trading-postgres

# Iniciar PostgreSQL
docker run -d \
  --name ia-trading-db \
  --network ia-trading-network \
  --restart unless-stopped \
  -e POSTGRES_USER=ia_trading \
  -e POSTGRES_PASSWORD=TU_PASSWORD \
  -e POSTGRES_DB=ia_trading \
  -v ia-trading-postgres:/var/lib/postgresql/data \
  postgres:16-alpine
```

El contenedor del API se despliega automáticamente desde GitHub Actions.
