#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/badrpk/xerus.git"
DEST="${XERUS_INSTALL_HOME:-$HOME/.local/share/xerus}"
VENV="$DEST/.venv"

have(){ command -v "$1" >/dev/null 2>&1; }
need(){ have "$1" || { echo "Missing required command: $1" >&2; exit 2; }; }

need git
need python3

if [ -d "$DEST/.git" ]; then
  test -z "$(git -C "$DEST" status --porcelain)" || { echo "Refusing update: $DEST has local changes" >&2; exit 3; }
  git -C "$DEST" fetch origin --tags --prune
  git -C "$DEST" checkout main
  git -C "$DEST" pull --ff-only origin main
elif [ -e "$DEST" ]; then
  echo "Refusing overwrite: $DEST exists and is not a Git repository" >&2
  exit 3
else
  git clone --branch main "$REPO" "$DEST"
fi

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install "$DEST"

BIN_DIR="${XERUS_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/xerus" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/xerus" "\$@"
EOF
chmod +x "$BIN_DIR/xerus"

echo "Xerus installed at $DEST"
echo "CLI: $BIN_DIR/xerus"
echo "Try: xerus status"
