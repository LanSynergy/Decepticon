#!/bin/bash
set -e

echo "🚀 Installing Go and building Decepticon CLI..."

# 1. Download and install Go
echo "📦 Downloading Go 1.23.4..."
cd /tmp
wget -q https://go.dev/dl/go1.23.4.linux-amd64.tar.gz

echo "📂 Installing Go to /usr/local/go..."
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz

# 2. Set up environment
echo "🔧 Setting up environment variables..."
if ! grep -q '/usr/local/go/bin' ~/.bashrc; then
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    echo 'export GOPATH=$HOME/go' >> ~/.bashrc
    echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
fi
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go

# 3. Verify Go installation
echo "✅ Verifying Go installation..."
go version

# 4. Build Decepticon CLI
echo "🔨 Building Decepticon CLI..."
cd /home/zeez/gitcloned/Decepticon/clients/launcher
go mod download
go build -o decepticon

# 5. Install CLI
echo "📦 Installing CLI to ~/.local/bin..."
mkdir -p ~/.local/bin
mv decepticon ~/.local/bin/
if ! grep -q '$HOME/.local/bin' ~/.bashrc; then
    echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
fi

echo "✅ Installation complete!"
echo ""
echo "Run 'source ~/.bashrc' to update your PATH, then:"
echo "  decepticon --version"
echo "  decepticon onboard"
