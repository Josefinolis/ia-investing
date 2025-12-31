# IA Trading - VPS Setup Guide (IONOS)

## 1. Preparar el VPS

### Conectarse al VPS
```bash
ssh root@TU_IP_VPS
```

### Instalar Docker y Docker Compose
```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Instalar Docker Compose plugin
apt install docker-compose-plugin -y

# Verificar instalación
docker --version
docker compose version
```

### Instalar Git y Certbot
```bash
apt install git certbot -y
```

## 2. Clonar el proyecto

```bash
cd /opt
git clone https://github.com/Josefinolis/ia-investing.git ia-trading
cd ia-trading
```

## 3. Configurar variables de entorno

```bash
cp .env.production.example .env
nano .env
```

Configurar:
- `POSTGRES_PASSWORD`: contraseña segura para PostgreSQL
- `ALPHA_VANTAGE_API_KEY`: tu API key
- `GEMINI_API_KEY`: tu API key
- `SCHEDULER_ENABLED`: true para activar el scheduler

## 4. Configurar dominio (opcional pero recomendado)

### En IONOS
1. Ir a Dominios > DNS
2. Añadir registro A: `api.tudominio.com` → `TU_IP_VPS`

### Obtener certificado SSL
```bash
certbot certonly --standalone -d api.tudominio.com
```

### Actualizar nginx.conf
```bash
nano nginx.conf
# Cambiar 'ia-trading.tudominio.com' por tu dominio real
```

## 5. Desplegar

### Primera vez (sin nginx/SSL)
```bash
docker compose up -d
```

### Con nginx/SSL
```bash
docker compose -f docker-compose.prod.yml up -d
```

## 6. Verificar

```bash
# Ver logs
docker compose logs -f api

# Probar health
curl http://localhost:8000/health

# Probar con dominio (si configuraste SSL)
curl https://api.tudominio.com/health
```

## 7. Actualizar la app móvil

En `ia_trading_mobile`, cambiar la URL del API:

**app/build.gradle.kts:**
```kotlin
productFlavors {
    create("device") {
        buildConfigField("String", "API_BASE_URL", "\"https://api.tudominio.com\"")
    }
}
```

## Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f api

# Reiniciar API
docker compose restart api

# Parar todo
docker compose down

# Ver estado
docker compose ps

# Entrar al contenedor de la DB
docker compose exec db psql -U ia_trading

# Backup de la base de datos
docker compose exec db pg_dump -U ia_trading ia_trading > backup.sql
```

## Renovar certificados SSL

Certbot renueva automáticamente, pero puedes forzarlo:
```bash
certbot renew
docker compose -f docker-compose.prod.yml restart nginx
```

## Actualizar el código

```bash
cd /opt/ia-trading
./deploy.sh
```
