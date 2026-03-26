# EC2 Deployment Guide

## Architecture

```
Browser → Vercel (Next.js) → EC2 Nginx → FastAPI → PostgreSQL
                                                  → Pinecone (cloud)
```

---

## 1. Launch EC2 Instance

| Setting | Value |
|---------|-------|
| AMI | Ubuntu 22.04 LTS |
| Instance type | `t3.micro` (free tier) or `t3.small` for production |
| Storage | 20 GB gp3 |
| Key pair | Create or use existing `.pem` |

**Security Group rules (inbound):**

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP only | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP / Let's Encrypt |
| 443 | TCP | 0.0.0.0/0 | HTTPS (after SSL setup) |

> Do **not** expose port 8000 publicly — Nginx proxies it.

---

## 2. Run the Setup Script

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/<user>/chatbot-app/main/scripts/setup-ec2.sh | bash
```

Or manually:

```bash
git clone https://github.com/<user>/chatbot-app.git ~/chatbot-app
cd ~/chatbot-app
bash scripts/setup-ec2.sh
```

---

## 3. Configure Environment Variables

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://ai_user:your_password@db:5432/personal_ai

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_AI_PROVIDER=openai

PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-memory

# Set this to your Vercel frontend URL
ALLOWED_ORIGINS=https://your-app.vercel.app

LOG_LEVEL=INFO
```

Edit root `.env` (Postgres credentials):

```env
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=use_a_strong_password_here
POSTGRES_DB=personal_ai
```

---

## 4. Start the Stack

```bash
cd ~/chatbot-app
docker compose -f docker-compose.prod.yml up -d --build
```

Verify it's running:

```bash
curl http://localhost/health
# {"status":"healthy","services":{"vector_store":true,"llm":true}}
```

---

## 5. Connect Vercel to EC2

In your Vercel project → **Settings → Environment Variables**, add:

```
NEXT_PUBLIC_API_URL = http://<EC2-PUBLIC-IP>
```

Redeploy Vercel for the change to take effect.

---

## 6. Optional: Add a Domain + SSL

If you have a domain pointed at your EC2 IP:

```bash
# Get a free SSL cert via Let's Encrypt
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d your-domain.com --email you@email.com --agree-tos --no-eff-email
```

Then uncomment the HTTPS block in `nginx/nginx.conf`, replace `YOUR_DOMAIN`, and reload:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

Update Vercel env var to use HTTPS:

```
NEXT_PUBLIC_API_URL = https://your-domain.com
```

---

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart backend after a code change
git pull
docker compose -f docker-compose.prod.yml up -d --build backend

# Stop everything
docker compose -f docker-compose.prod.yml down

# Database shell
docker compose -f docker-compose.prod.yml exec db psql -U ai_user -d personal_ai
```

---

## Keeping the App Running After Reboot

Docker is already set to `restart: unless-stopped` in the compose file and enabled on boot via `systemctl enable docker`, so the stack will auto-start on instance reboot.
