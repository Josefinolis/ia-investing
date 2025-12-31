# IA Trading - VPS Setup Guide (IONOS)

## Arquitectura

```
GitHub Actions (build) → GitHub Container Registry → VPS (pull + run)
```

- El código se compila en GitHub Actions
- La imagen se sube a ghcr.io
- El VPS solo descarga y ejecuta la imagen

## 1. Configurar secrets en GitHub

En el repositorio, ir a **Settings > Secrets and variables > Actions** y añadir:

| Secret | Valor |
|--------|-------|
| `VPS_HOST` | IP de tu VPS IONOS |
| `VPS_USER` | `root` (o tu usuario) |
| `VPS_SSH_KEY` | Tu clave SSH privada |

### Generar clave SSH (si no tienes)
```bash
ssh-keygen -t ed25519 -C "github-actions"
# Copiar el contenido de ~/.ssh/id_ed25519 a VPS_SSH_KEY
# Copiar el contenido de ~/.ssh/id_ed25519.pub al VPS en ~/.ssh/authorized_keys
```

## 2. Preparar el VPS (solo primera vez)

```bash
ssh root@TU_IP_VPS

# Instalar Docker
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# Crear directorio
mkdir -p /opt/ia-trading
cd /opt/ia-trading

# Crear docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  api:
    image: ghcr.io/josefinolis/ia-investing:latest
    container_name: ia-trading-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ia_trading:${POSTGRES_PASSWORD}@db:5432/ia_trading
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SCHEDULER_ENABLED=${SCHEDULER_ENABLED:-true}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - ia-trading-network

  db:
    image: postgres:16-alpine
    container_name: ia-trading-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=ia_trading
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=ia_trading
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ia_trading -d ia_trading"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - ia-trading-network

networks:
  ia-trading-network:
    driver: bridge

volumes:
  postgres_data:
EOF

# Crear .env
cat > .env << 'EOF'
POSTGRES_PASSWORD=tu_password_seguro
ALPHA_VANTAGE_API_KEY=tu_api_key
GEMINI_API_KEY=tu_api_key
SCHEDULER_ENABLED=true
LOG_LEVEL=INFO
EOF

# Editar con tus valores reales
nano .env

# Iniciar por primera vez
docker compose -f docker-compose.prod.yml up -d
```

## 3. Deploy automático

A partir de ahora, cada push a `master` desplegará automáticamente:

1. GitHub Actions construye la imagen
2. La sube a ghcr.io
3. Se conecta al VPS por SSH
4. Hace pull de la nueva imagen
5. Reinicia el contenedor

## 4. Verificar

```bash
# En el VPS
curl http://localhost:8000/health

# Desde fuera
curl http://TU_IP_VPS:8000/health
```

## Comandos útiles

```bash
# Ver logs
docker compose -f docker-compose.prod.yml logs -f api

# Reiniciar
docker compose -f docker-compose.prod.yml restart api

# Parar todo
docker compose -f docker-compose.prod.yml down

# Ver estado
docker compose -f docker-compose.prod.yml ps

# Backup DB
docker compose -f docker-compose.prod.yml exec db pg_dump -U ia_trading ia_trading > backup.sql
```

## Configurar dominio (opcional)

1. En IONOS, añadir registro A: `api.tudominio.com` → `TU_IP_VPS`
2. Instalar Caddy (proxy reverso con SSL automático):

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy

# Configurar Caddy
cat > /etc/caddy/Caddyfile << 'EOF'
api.tudominio.com {
    reverse_proxy localhost:8000
}
EOF

systemctl restart caddy
```

Caddy obtiene certificados SSL automáticamente.
