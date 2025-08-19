# author : chris-jyp
chmod +x usehook.sh
echo "Setting up git hooks path to .githooks"
git config core.hooksPath .githooks
echo "check pre-push hook"
git config core.hooksPath
