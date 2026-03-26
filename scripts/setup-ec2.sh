#!/bin/bash
# scripts/setup-ec2.sh
# Run this once on a fresh Ubuntu 22.04 EC2 instance.
# Usage: bash setup-ec2.sh

set -e

echo "=== [1/6] System update ==="
sudo apt-get update -y && sudo apt-get upgrade -y

echo "=== [2/6] Install Docker ==="
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow running docker without sudo
sudo usermod -aG docker $USER

echo "=== [3/6] Enable Docker on boot ==="
sudo systemctl enable docker
sudo systemctl start docker

echo "=== [4/6] Clone repository ==="
# Replace with your actual repo URL
read -rp "Enter your GitHub repo URL (e.g. https://github.com/user/chatbot-app): " REPO_URL
git clone "$REPO_URL" ~/chatbot-app
cd ~/chatbot-app

echo "=== [5/6] Set up environment file ==="
cp backend/.env.example backend/.env
echo ""
echo ">>> Edit backend/.env now with your real API keys:"
echo "    nano backend/.env"
echo ""
echo ">>> Also edit the root .env for Postgres credentials:"
cat > .env <<'EOF'
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=changeme_use_a_strong_password
POSTGRES_DB=personal_ai
EOF
echo "    nano .env"
echo ""
read -rp "Press Enter once you have updated both .env files..."

echo "=== [6/6] Build and start ==="
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "✓ Done! Backend is running."
echo ""
echo "  Health check:  curl http://localhost/health"
echo ""
echo "  Next steps:"
echo "  1. Open port 80 (and 443) in your EC2 Security Group"
echo "  2. Set NEXT_PUBLIC_API_URL=http://<your-ec2-public-ip> in Vercel"
echo "  3. Update ALLOWED_ORIGINS in backend/.env to your Vercel URL"
echo "  4. Optionally set up a domain + SSL: see docs/ssl.md"
