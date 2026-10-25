#!/bin/bash
# dump_offsets.sh — pull libil2cpp.so from device and dump method offsets
# Usage: ./scripts/dump_offsets.sh com.nekki.shadowfight
# Output: offsets.txt

PKG="${1:-com.nekki.shadowfight}"
OUT="offsets_$(date +%Y%m%d_%H%M%S).txt"

echo "[*] Pulling libil2cpp.so from $PKG ..."
adb shell "su -c 'cp /data/app/$PKG*/lib/arm64/libil2cpp.so /sdcard/libil2cpp.so'"
adb pull /sdcard/libil2cpp.so .
adb shell rm /sdcard/libil2cpp.so

echo "[*] Dumping symbols ..."
# Requires nm or readelf on host
if command -v nm &>/dev/null; then
    nm -D --defined-only libil2cpp.so 2>/dev/null | grep -iE \
        "PlayerController|PlayerWallet|EnergySystem|WeaponBase|BattleController|GetCoins|GetGems|TakeDamage|CalculateDamage|GetCurrentHealth|GetBattleResult" \
        | tee "$OUT"
elif command -v readelf &>/dev/null; then
    readelf -Ws libil2cpp.so 2>/dev/null | grep -iE \
        "PlayerController|PlayerWallet|EnergySystem|WeaponBase|BattleController|GetCoins|GetGems|TakeDamage|CalculateDamage|GetCurrentHealth|GetBattleResult" \
        | tee "$OUT"
else
    echo "[!] Install binutils: sudo apt install binutils"
    exit 1
fi

echo ""
echo "[✓] Offsets written to $OUT"
echo "    Copy hex addresses into MemPatcher.Offsets constants"
