#!/bin/bash
# patch_apk.sh — inject hack smali into BetaFight2.apk
# Usage: ./scripts/patch_apk.sh <path/to/BetaFight2.apk>
#
# Requirements: apktool, apksigner, zipalign, java 11+
# Output: BetaFight2_HACKED.apk (signed with debug key)

set -euo pipefail

APK="$1"
WORK_DIR="$(dirname "$APK")/bf2_work"
OUT_APK="$(dirname "$APK")/BetaFight2_HACKED.apk"
KEYSTORE="$HOME/.android/debug.keystore"

echo "[*] Decompiling $APK ..."
apktool d -f "$APK" -o "$WORK_DIR"

echo "[*] Patching AndroidManifest — adding SYSTEM_ALERT_WINDOW ..."
python3 - <<'PYEOF'
import re, sys
manifest = open(f"{sys.argv[1]}/AndroidManifest.xml").read()
perm = '<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>'
if perm not in manifest:
    manifest = manifest.replace('<application', perm + '\n    <application', 1)
    open(f"{sys.argv[1]}/AndroidManifest.xml", 'w').write(manifest)
    print("  added SYSTEM_ALERT_WINDOW")
else:
    print("  permission already present")
PYEOF
python3 - "$WORK_DIR"

echo "[*] Injecting hack smali loader ..."
SMALI_DIR="$WORK_DIR/smali"
# Find main activity smali to inject hook init
MAIN=$(grep -rl "onCreate" "$SMALI_DIR" | head -1)

# Append init call at end of onCreate (before return-void)
python3 - <<'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    code = f.read()

inject = """
    # BF2Hack: trigger overlay start via broadcast
    const-string v0, "com.betafight2.hack.START"
    new-instance v1, Landroid/content/Intent;
    invoke-direct {v1, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    invoke-virtual {p0, v1}, Landroid/app/Activity;->sendBroadcast(Landroid/content/Intent;)V
"""

# Insert before return-void in onCreate
code = re.sub(r'(\.method.*?onCreate.*?)(return-void)',
              r'\1' + inject + r'\2', code, count=1, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(code)
print(f"  patched {path}")
PYEOF
python3 - "$MAIN"

echo "[*] Recompiling ..."
apktool b "$WORK_DIR" -o "${OUT_APK%.apk}_unsigned.apk"

echo "[*] Zipalign ..."
zipalign -f 4 "${OUT_APK%.apk}_unsigned.apk" "$OUT_APK"

echo "[*] Signing with debug key ..."
if [ ! -f "$KEYSTORE" ]; then
    keytool -genkey -v -keystore "$KEYSTORE" -storepass android \
            -alias androiddebugkey -keypass android \
            -keyalg RSA -keysize 2048 -validity 10000 \
            -dname "CN=Android Debug,O=Android,C=US"
fi

apksigner sign --ks "$KEYSTORE" --ks-pass pass:android \
               --key-pass pass:android "$OUT_APK"

echo "[✓] Done: $OUT_APK"
echo ""
echo "Install: adb install -r '$OUT_APK'"
echo "Then install BF2 Hack manager APK alongside it."
rm -f "${OUT_APK%.apk}_unsigned.apk"
