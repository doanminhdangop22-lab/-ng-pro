package com.betafight2.hack.core;

public class HackConfig {
    public static final String TARGET_PACKAGE = "com.nekki.shadowfight";

    // Feature toggles (shared with overlay menu)
    public static volatile boolean godMode         = false;
    public static volatile boolean oneHitKill      = false;
    public static volatile boolean unlimitedCoins  = false;
    public static volatile boolean unlimitedGems   = false;
    public static volatile boolean unlimitedEnergy = false;
    public static volatile boolean speedHack       = false;
    public static volatile float   speedMultiplier = 2.0f;
    public static volatile boolean maxDamage       = false;
    public static volatile boolean noKnockback     = false;
    public static volatile boolean autoWin         = false;

    // Coin/gem values injected when toggled
    public static final int UNLIMITED_COINS = 9999999;
    public static final int UNLIMITED_GEMS  = 9999999;
    public static final int UNLIMITED_ENERGY = 100;
}
