# Deploy na AWS

Guia de deploy pra uma instância **EC2** rodando a aplicação com
`docker-compose` (o mesmo `docker-compose.yml` já usado em desenvolvimento,
com alguns ajustes de produção). É a opção mais simples pro tamanho atual
do projeto -- sem precisar de ECS/EKS nem RDS, o próprio Postgres roda em
container na mesma instância, com um volume persistente.

Se o tráfego crescer a ponto de precisar separar o banco (alta
disponibilidade, backups gerenciados, etc.), o caminho natural depois é
trocar o serviço `postgres` do compose por uma instância do **RDS** e
apontar o `DATABASE_URL` pra ela -- o resto do guia não muda.

## 1. Pré-requisitos

- Conta AWS
- Um par de chaves (key pair) criado em EC2 → "Key Pairs", pra acessar a instância via SSH
- (Opcional, mas recomendado) um domínio próprio apontando pra instância -- necessário pra HTTPS de verdade, que por sua vez é necessário pro cookie de autenticação em produção (`AMBIENTE=production` exige `secure=True`) e pro webhook do Mercado Pago

## 2. Provisionar a instância EC2

1. EC2 → "Launch instance"
2. AMI: **Ubuntu Server 24.04 LTS**
3. Tipo: `t3.micro` (elegível pro free tier; dá pra subir depois se precisar)
4. Storage: 20 GB já é confortável pro tamanho do projeto
5. Key pair: a que você criou no passo 1
6. **Security Group** -- libera:
   - `22` (SSH) -- restrito ao seu IP, não `0.0.0.0/0`
   - `80` (HTTP) -- `0.0.0.0/0`
   - `443` (HTTPS) -- `0.0.0.0/0`
   - **Não precisa abrir a `8000`** pro mundo -- só o Nginx (passo 6) fica exposto, e ele repassa pra API internamente
7. Depois de criada, aloque um **Elastic IP** e associe à instância (sem isso, o IP muda toda vez que ela reinicia)
8. Se tiver domínio, aponte o registro `A` dele pro Elastic IP

## 3. Instalar Docker na instância

Conecta via SSH (`ssh -i sua-chave.pem ubuntu@<elastic-ip>`) e roda:

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# desconecta e reconecta o SSH pra o grupo "docker" valer
```

## 4. Trazer o projeto pra instância

```bash
git clone https://github.com/nicolasdepaulla/Conecta-Empresas-py.git
cd Conecta-Empresas-py
```

(Se o repositório continuar privado, configura uma chave SSH de deploy no
GitHub, ou clona via HTTPS com um Personal Access Token.)

## 5. Configurar o `.env` de produção

```bash
cp .env.example .env
nano .env
```

Pontos que **mudam** em relação ao `.env` de desenvolvimento:

| Variável | Valor em produção |
|---|---|
| `AMBIENTE` | `production` (ativa o cookie `secure=True` e reduz o nível de log pra `INFO`) |
| `JWT_SECRET_KEY` | uma chave forte e única -- gera com `openssl rand -hex 32`, nunca reaproveita a de dev |
| `PUBLIC_BASE_URL` | `https://seu-dominio.com` (ou `https://<elastic-ip>` se ainda não tiver domínio) -- usada nos links de redefinição de senha |
| `PAYMENT_PROVIDER_API_KEY` / `PAYMENT_PROVIDER_WEBHOOK_SECRET` | as credenciais de **produção** do Mercado Pago (não as de sandbox/teste) |
| `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM_EMAIL` | credenciais reais do Gmail (sem isso, o link de redefinição de senha não é enviado -- e em produção ele nem aparece no log, por segurança) |

`DATABASE_URL` pode ficar como está no `.env.example` -- o `docker-compose.yml`
já sobrescreve com o endereço interno do serviço `postgres`.

**Importante:** o `docker-compose.yml` atual tem a senha do Postgres
(`conecta`/`conecta`) escrita direto no arquivo, pensada só pro ambiente de
dev. Em produção, sobrescreve isso com uma senha forte usando um arquivo
`docker-compose.override.yml` (o Docker Compose aplica ele por cima do
principal automaticamente, sem precisar editar o `docker-compose.yml`
versionado):

```yaml
# docker-compose.override.yml (não comitar -- já fica de fora do git
# por boa prática, mas confira o .gitignore se for criar um)
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: <uma-senha-forte-aqui>
  api:
    environment:
      DATABASE_URL: postgresql+asyncpg://conecta:<a-mesma-senha-forte-aqui>@postgres:5432/conecta_empresas
```

## 6. Subir a aplicação

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head   # cria as tabelas
docker compose exec api python -m scripts.seed # popula os pacotes (só na primeira vez)
docker compose exec api python -m scripts.set_admin <seu-username>  # depois de criar sua conta pelo site
```

Nesse ponto a API já responde em `http://<elastic-ip>:8000`, mas ainda sem
HTTPS -- próximo passo.

## 7. HTTPS com Nginx + Let's Encrypt

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Cria `/etc/nginx/sites-available/conecta` com:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/conecta /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d seu-dominio.com   # emite o certificado e já reconfigura o Nginx pra HTTPS
```

O certbot configura renovação automática sozinho. Depois disso, confirma que
`PUBLIC_BASE_URL` no `.env` está como `https://seu-dominio.com` e reinicia a
API (`docker compose restart api`) se tiver mudado.

## 8. Apontar o webhook do Mercado Pago pra produção

No painel do Mercado Pago (modo produção, não sandbox), configura a URL de
notificação do webhook como `https://seu-dominio.com/pagamentos/webhook` --
substitui o link do ngrok usado em desenvolvimento.

## 9. Garantir que a aplicação sobe sozinha depois de um reboot

O Docker já reinicia os containers sozinho por padrão nesse projeto? Não --
adiciona a política de restart no `docker-compose.override.yml` do passo 5:

```yaml
services:
  api:
    restart: unless-stopped
  postgres:
    restart: unless-stopped
```

## 10. Backup agendado

`scripts/backup.py` já existe no projeto -- só falta agendar. Com a
aplicação rodando em Docker, o jeito mais simples é um cron no host que
executa o `pg_dump` de dentro do container e copia o arquivo pra fora:

```bash
crontab -e
```

Adiciona (backup diário às 3h da manhã):

```cron
0 3 * * * cd /home/ubuntu/Conecta-Empresas-py && docker compose exec -T api python -m scripts.backup
```

Os arquivos ficam em `backups/` dentro do container -- se quiser guardá-los
fora da instância (recomendado, pra sobreviver mesmo se a instância for
perdida), monta esse caminho como volume no `docker-compose.override.yml`:

```yaml
services:
  api:
    volumes:
      - ./backups:/app/backups
```

e depois, periodicamente, copia `backups/` pra um S3:

```bash
aws s3 sync /home/ubuntu/Conecta-Empresas-py/backups s3://seu-bucket/backups/
```

(requer o AWS CLI configurado na instância com uma role/credenciais que só
tenham permissão de escrita nesse bucket).

## 11. Atualizando a aplicação (deploy de uma nova versão)

```bash
cd Conecta-Empresas-py
git pull origin main
docker compose up -d --build
docker compose exec api alembic upgrade head   # aplica migrations novas, se houver
```

## 12. Troubleshooting

- **`alembic upgrade head` reclama que não encontra o `alembic.ini`**: confirma
  que a imagem foi reconstruída depois do fix no `Dockerfile` que copia
  `alembic/`/`alembic.ini` (`docker compose up -d --build`, não só `up -d`).
- **Erro de conexão recusada com o Postgres**: `docker compose ps` pra conferir
  se o serviço `postgres` está `healthy`; se acabou de subir, espera alguns
  segundos (o `healthcheck` do compose já faz a API esperar o Postgres ficar
  pronto antes de iniciar).
- **Cookie de login não funciona em produção**: confirma que `AMBIENTE=production`
  está de fato no `.env` *e* que o site está sendo acessado via `https://`
  -- com `secure=True`, o navegador descarta o cookie se a conexão não for HTTPS.
