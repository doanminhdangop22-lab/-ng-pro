package com.betafight2.hack.hooks;

import com.betafight2.hack.core.HackConfig;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class MainHook implements IXposedHookLoadPackage {

    private static final String TAG = "BF2Hack";

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) {
        if (!lpparam.packageName.equals(HackConfig.TARGET_PACKAGE)) return;

        XposedBridge.log(TAG + ": loaded into " + lpparam.packageName);

        hookPlayerHealth(lpparam.classLoader);
        hookPlayerDamage(lpparam.classLoader);
        hookCurrency(lpparam.classLoader);
        hookEnergy(lpparam.classLoader);
        hookGameSpeed(lpparam.classLoader);
        hookBattleResult(lpparam.classLoader);
    }

    // ─── God Mode: player takes 0 damage ────────────────────────────────────
    private void hookPlayerHealth(ClassLoader cl) {
        try {
            // SF2 Unity IL2CPP — class names via dump.cs or GameGuardian offset
            // Common pattern: PlayerController or CharacterBase has TakeDamage(float)
            Class<?> playerClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.PlayerController", cl);

            XposedHelpers.findAndHookMethod(playerClass, "TakeDamage", float.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            if (HackConfig.godMode) {
                                param.args[0] = 0f;
                            }
                        }
                    });

            // Hook getHealth getter so UI shows full HP
            XposedHelpers.findAndHookMethod(playerClass, "GetCurrentHealth",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.godMode) {
                                param.setResult(param.thisObject);
                                // Return max health — read maxHealth field
                                try {
                                    float max = (float) XposedHelpers.getFloatField(
                                            param.thisObject, "maxHealth");
                                    param.setResult(max);
                                } catch (Throwable ignored) {}
                            }
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookPlayerHealth: " + t.getMessage());
        }
    }

    // ─── One Hit Kill + Max Damage ───────────────────────────────────────────
    private void hookPlayerDamage(ClassLoader cl) {
        try {
            Class<?> weaponClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.WeaponBase", cl);

            XposedHelpers.findAndHookMethod(weaponClass, "CalculateDamage",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.oneHitKill) {
                                param.setResult(999999f);
                            } else if (HackConfig.maxDamage) {
                                float orig = (float) param.getResult();
                                param.setResult(orig * 100f);
                            }
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookPlayerDamage: " + t.getMessage());
        }
    }

    // ─── Unlimited Coins & Gems ──────────────────────────────────────────────
    private void hookCurrency(ClassLoader cl) {
        try {
            Class<?> walletClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.PlayerWallet", cl);

            // Hook getCoins / getGems getters
            XposedHelpers.findAndHookMethod(walletClass, "GetCoins",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedCoins)
                                param.setResult(HackConfig.UNLIMITED_COINS);
                        }
                    });

            XposedHelpers.findAndHookMethod(walletClass, "GetGems",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedGems)
                                param.setResult(HackConfig.UNLIMITED_GEMS);
                        }
                    });

            // Block spend methods
            XposedHelpers.findAndHookMethod(walletClass, "SpendCoins", int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedCoins) param.setResult(true);
                        }
                    });

            XposedHelpers.findAndHookMethod(walletClass, "SpendGems", int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedGems) param.setResult(true);
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookCurrency: " + t.getMessage());
        }
    }

    // ─── Unlimited Energy ────────────────────────────────────────────────────
    private void hookEnergy(ClassLoader cl) {
        try {
            Class<?> energyClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.EnergySystem", cl);

            XposedHelpers.findAndHookMethod(energyClass, "GetCurrentEnergy",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedEnergy)
                                param.setResult(HackConfig.UNLIMITED_ENERGY);
                        }
                    });

            XposedHelpers.findAndHookMethod(energyClass, "ConsumeEnergy", int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            if (HackConfig.unlimitedEnergy) param.setResult(null);
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookEnergy: " + t.getMessage());
        }
    }

    // ─── Speed Hack ──────────────────────────────────────────────────────────
    private void hookGameSpeed(ClassLoader cl) {
        try {
            // Unity Time.timeScale proxy
            Class<?> timeClass = XposedHelpers.findClass(
                    "com.unity3d.player.UnityPlayer", cl);

            XposedHelpers.findAndHookMethod(timeClass, "UnitySendMessage",
                    String.class, String.class, String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            // Intercept timeScale messages
                            if ("GameController".equals(param.args[0])
                                    && "SetTimeScale".equals(param.args[1])
                                    && HackConfig.speedHack) {
                                param.args[2] = String.valueOf(HackConfig.speedMultiplier);
                            }
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookGameSpeed: " + t.getMessage());
        }
    }

    // ─── Auto Win: force battle result to WIN ────────────────────────────────
    private void hookBattleResult(ClassLoader cl) {
        try {
            Class<?> battleClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.BattleController", cl);

            XposedHelpers.findAndHookMethod(battleClass, "GetBattleResult",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.autoWin) {
                                // 1 = WIN, 0 = LOSE (reverse-engineered enum)
                                param.setResult(1);
                            }
                        }
                    });

            // Also hook enemy health to 0 when autoWin active
            Class<?> enemyClass = XposedHelpers.findClass(
                    "com.nekki.shadowfight.game.EnemyController", cl);

            XposedHelpers.findAndHookMethod(enemyClass, "GetCurrentHealth",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (HackConfig.autoWin) param.setResult(0f);
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " hookBattleResult: " + t.getMessage());
        }
    }
}
