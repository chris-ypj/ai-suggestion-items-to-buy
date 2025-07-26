#!/bin/bash

set -e  #if error, exit immediately


BRANCH=${1:-feature/0.5.0-shopping-chris}  # if no branch is specified, use the default branch

echo "🚀 pull repository from $BRANCH..."
git checkout $BRANCH
git pull origin   $BRANCH

echo "✅ git pull finished, entry directory：$LOCAL_DIR"
echo "🐳 start build Docker image..."
if ! docker info | grep -q "Username: kris888777"; then
  echo "🔐 docker login..."
  docker login
else
  echo "✅  Docker Hub user：kris888777"
fi

echo "🐳 build  Docker image and push to Docker Hub..."
docker buildx build --platform linux/amd64 -t kris888777/aisuggestion:latest --push .

echo "🚁 Using Fly.io deploy command to deploy the service..."
/Users/c/.fly/bin/fly deploy --image kris888777/aisuggestion:latest

echo "🎉 deploy done, you can visit：https://aisuggestion.fly.dev"