#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
DIST_DIR="$ROOT_DIR/dist"
STAGE_DIR="$DIST_DIR/system-java"
APP_DIR="$STAGE_DIR/Logisim.app"

cd "$ROOT_DIR"

for command_name in java jar plutil ditto hdiutil; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'Required command is missing: %s\n' "$command_name" >&2
        exit 1
    fi
done

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp -R "$ROOT_DIR/Logisim.app" "$APP_DIR"
chmod 755 "$APP_DIR/Contents/MacOS/Logisim"

plutil -lint "$APP_DIR/Contents/Info.plist"
jar tf "$APP_DIR/Contents/Resources/Java/logisim.jar" >/dev/null
VERSION_OUTPUT=$("$APP_DIR/Contents/MacOS/Logisim" -version)
if [ "$VERSION_OUTPUT" != "2.7.1" ]; then
    printf 'Unexpected Logisim version: %s\n' "$VERSION_OUTPUT" >&2
    exit 1
fi

rm -f "$DIST_DIR/Logisim-2.7.1-system-java.zip" \
      "$DIST_DIR/Logisim-2.7.1-system-java.dmg"
ditto -c -k --sequesterRsrc --keepParent \
    "$APP_DIR" "$DIST_DIR/Logisim-2.7.1-system-java.zip"
hdiutil create -quiet -fs HFS+ -format UDZO \
    -volname "Logisim 2.7.1" \
    -srcfolder "$STAGE_DIR" \
    "$DIST_DIR/Logisim-2.7.1-system-java.dmg"
hdiutil verify -quiet "$DIST_DIR/Logisim-2.7.1-system-java.dmg"

printf 'Created %s\n' "$DIST_DIR/Logisim-2.7.1-system-java.zip"
printf 'Created %s\n' "$DIST_DIR/Logisim-2.7.1-system-java.dmg"
