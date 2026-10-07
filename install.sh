#!/bin/sh
# Q-SIM GATEWAY installer — local install from the repository root.
# Installs the ZEPHIRUM prototype + gateway to $ZEPHIRUM_HOME (default: ~/.zephirum)
# and creates `qsim-gateway` + `zephirum-decide` launchers. Pure Python 3, no dependencies.
set -e
DEST="${ZEPHIRUM_HOME:-$HOME/zephirum}"
mkdir -p "$DEST" "$DEST/bin"
cp -r prototype examples docs "$DEST"/ 2>/dev/null || true
cat > "$DEST/bin/qsim-gateway" << LAUNCH
#!/bin/sh
exec python3 "$DEST/prototype/qsim_gateway.py" "\$@"
LAUNCH
chmod +x "$DEST/bin/qsim-gateway"
cat > "$DEST/bin/zephirum-decide" << LAUNCH2
#!/bin/sh
exec python3 "$DEST/prototype/zephirum_decide.py" "\$@"
LAUNCH2
chmod +x "$DEST/bin/zephirum-decide"
LBD="$HOME/.local/bin"
if [ -d "$LBD" ] && echo ":$PATH:" | grep -q ":$LBD:"; then
    ln -sf "$DEST/bin/qsim-gateway" "$LBD/qsim-gateway"
    ln -sf "$DEST/bin/zephirum-decide" "$LBD/zephirum-decide"
    echo "Installed. Commands on PATH: qsim-gateway, zephirum-decide"
else
    echo "Installed in: $DEST"
    echo "Add to PATH:  export PATH=\"$DEST/bin:\$PATH\""
fi
