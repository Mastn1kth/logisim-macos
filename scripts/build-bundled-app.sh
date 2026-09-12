#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
DIST_DIR="$ROOT_DIR/dist"
INPUT_DIR="$DIST_DIR/jpackage-input"
APP_DIR="$DIST_DIR/Logisim.app"

cd "$ROOT_DIR"

case "$(uname -m)" in
    arm64)
        ARCH_NAME=arm64
        MIN_MACOS=11.0.0
        ;;
    x86_64)
        ARCH_NAME=x64
        MIN_MACOS=11.0.0
        ;;
    *)
        printf 'Unsupported Mac architecture: %s\n' "$(uname -m)" >&2
        exit 1
        ;;
esac

STAGE_DIR="$DIST_DIR/dmg-$ARCH_NAME"

for command_name in java jpackage jar plutil codesign lipo ditto hdiutil; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'Required command is missing: %s\n' "$command_name" >&2
        exit 1
    fi
done

rm -rf "$INPUT_DIR" "$APP_DIR" "$STAGE_DIR"
mkdir -p "$INPUT_DIR"
cp "$ROOT_DIR/Logisim.app/Contents/Resources/Java/logisim.jar" "$INPUT_DIR/"
cp "$ROOT_DIR/Logisim.app/Contents/Resources/LogisimDoc.icns" "$INPUT_DIR/"

jpackage \
    --type app-image \
    --dest "$DIST_DIR" \
    --input "$INPUT_DIR" \
    --name Logisim \
    --main-jar logisim.jar \
    --main-class com.cburch.logisim.Main \
    --app-version 2.7.1 \
    --vendor "Carl Burch" \
    --icon "$ROOT_DIR/Logisim.app/Contents/Resources/LogisimApp.icns" \
    --mac-package-identifier com.cburch.logisim \
    --file-associations "$ROOT_DIR/packaging/logisim.properties" \
    --add-modules java.base,java.desktop,java.logging,java.prefs \
    --java-options -Dapple.laf.useScreenMenuBar=true \
    --java-options -Dcom.apple.mrj.application.apple.menu.about.name=Logisim

PLIST_PATH="$APP_DIR/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Delete :LSMinimumSystemVersion' "$PLIST_PATH" >/dev/null 2>&1 || true
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $MIN_MACOS" "$PLIST_PATH"
codesign --force --deep --sign - "$APP_DIR"

plutil -lint "$PLIST_PATH"
jar tf "$APP_DIR/Contents/app/logisim.jar" >/dev/null
lipo -verify_arch "$(uname -m)" "$APP_DIR/Contents/MacOS/Logisim"
codesign --verify --deep --strict "$APP_DIR"
VERSION_OUTPUT=$("$APP_DIR/Contents/MacOS/Logisim" -version)
if [ "$VERSION_OUTPUT" != "2.7.1" ]; then
    printf 'Unexpected Logisim version: %s\n' "$VERSION_OUTPUT" >&2
    exit 1
fi

DMG_PATH="$DIST_DIR/Logisim-2.7.1-macos-$ARCH_NAME.dmg"
ZIP_PATH="$DIST_DIR/Logisim-2.7.1-macos-$ARCH_NAME.zip"
rm -f "$DMG_PATH" "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_DIR" "$ZIP_PATH"
mkdir -p "$STAGE_DIR"
ditto "$APP_DIR" "$STAGE_DIR/Logisim.app"
hdiutil create -quiet -fs HFS+ -format UDZO \
    -volname "Logisim 2.7.1" \
    -srcfolder "$STAGE_DIR" \
    "$DMG_PATH"
hdiutil verify -quiet "$DMG_PATH"

printf 'Created %s\n' "$ZIP_PATH"
printf 'Created %s\n' "$DMG_PATH"
