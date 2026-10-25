# Beta Fight 2 Hack — Mod Menu

Target: `com.nekki.shadowfight` (Beta Fight 2 mod build)

## Features

| Hack | Method |
|---|---|
| God Mode (vô địch) | Xposed hook TakeDamage → 0 |
| One Hit Kill | Hook CalculateDamage → 999999 |
| Max Damage ×100 | Hook CalculateDamage × 100 |
| Unlimited Coins | Hook GetCoins + block SpendCoins |
| Unlimited Gems | Hook GetGems + block SpendGems |
| Unlimited Energy | Hook GetCurrentEnergy + block ConsumeEnergy |
| Auto Win | Hook GetBattleResult → 1, EnemyHP → 0 |
| No Knockback | Hook knockback velocity → 0 |
| Speed Hack 1×–5× | UnitySendMessage intercept timeScale |
| Floating Mod Menu | Overlay service, draggable, toggle per feature |

## Build

```bash
# Android Studio or:
./gradlew assembleRelease
# APK: app/build/outputs/apk/release/app-release.apk
```

## Install (cần root + LSPosed/EdXposed)

```bash
# 1. Install hack APK
adb install app/build/outputs/apk/debug/app-debug.apk

# 2. Enable module in LSPosed → scope: Beta Fight 2

# 3. Reboot → launch BF2 Hack → tap "KÍCH HOẠT" → launch game
```

## Patch APK trực tiếp (không cần root)

```bash
# Đặt BetaFight2.apk cùng thư mục
./scripts/patch_apk.sh /path/to/BetaFight2.apk
# Output: BetaFight2_HACKED.apk
```

## Dump offsets (khi cần patch native IL2CPP)

```bash
./scripts/dump_offsets.sh com.nekki.shadowfight
# Cập nhật MemPatcher.Offsets với hex addresses từ output
```
