#!/bin/bash

set -e  #if error, exit immediately


BRANCH=${1:-feature/0.5.0-shopping-chris}  # if no branch is specified, use the default branch

echo "🚀 pull repository from $BRANCH..."
git checkout $BRANCH
git pull origin   $BRANCH

echo "✅ git pull finished, entry directory：$LOCAL_DIR"
echo "🐳 start build Docker image..."
if ! docker info | grep -q "Username: your username"; then    # you should use your own username of fly or other platform
  echo "🔐 docker login..."
  docker login
else
  echo "✅  Docker Hub user：your username"
fi

echo "🐳 build  Docker image and push to Docker Hub..."
docker buildx build --platform linux/amd64 -t your username/aisuggestion:latest --push .

echo "🚁 Using Fly.io deploy command to deploy the service..."
/Users/c/.fly/bin/fly deploy --image your username/aisuggestion:latest   # you should change the fly path into your local path ;you should use your own username of fly or other platform
echo "🎉 deploy done, you can visit：https://aisuggestion.xxx.xx"
