package com.betafight2.hack.utils;

import android.util.Log;

import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * Dumps IL2CPP class/method offsets from libil2cpp.so at runtime.
 * Run once per game version to populate MemPatcher.Offsets.
 */
public class OffsetDumper {

    private static final String TAG = "BF2OffsetDump";

    /**
     * Find method offset in libil2cpp.so via /proc/<pid>/maps + nm/readelf.
     * Requires root + binutils on device (or frida-server).
     */
    public static long findMethodOffset(String className, String methodName, int pid) {
        try {
            // Locate libil2cpp.so base address from maps
            long base = getLibBase(pid, "libil2cpp.so");
            if (base == 0) return 0;

            // Dump symbols and grep
            Process p = Runtime.getRuntime().exec(new String[]{
                    "su", "-c",
                    "readelf -Ws /proc/" + pid + "/root/lib/arm64-v8a/libil2cpp.so"
                            + " 2>/dev/null | grep -i \"" + className + "_" + methodName + "\""
            });
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = br.readLine()) != null) {
                // readelf line: "   Num: addr size FUNC GLOBAL DEFAULT  n Name"
                String[] parts = line.trim().split("\\s+");
                if (parts.length >= 2) {
                    try {
                        long offset = Long.parseLong(parts[1], 16);
                        Log.d(TAG, className + "::" + methodName + " offset=0x" + Long.toHexString(offset));
                        return base + offset;
                    } catch (NumberFormatException ignored) {}
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "dump failed: " + e.getMessage());
        }
        return 0;
    }

    public static long getLibBase(int pid, String libName) {
        try {
            Process p = Runtime.getRuntime().exec(new String[]{
                    "su", "-c", "cat /proc/" + pid + "/maps"
            });
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = br.readLine()) != null) {
                if (line.contains(libName) && line.contains("r-xp")) {
                    String addrRange = line.split("-")[0];
                    return Long.parseLong(addrRange, 16);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "getLibBase failed: " + e.getMessage());
        }
        return 0;
    }

    /** Run all dumps and log offsets to logcat — filter: adb logcat -s BF2OffsetDump */
    public static void dumpAll(int pid) {
        String[] targets = {
            "PlayerController:TakeDamage",
            "PlayerController:GetCurrentHealth",
            "PlayerController:GetMaxHealth",
            "PlayerWallet:GetCoins",
            "PlayerWallet:GetGems",
            "EnergySystem:GetCurrentEnergy",
            "WeaponBase:CalculateDamage",
            "BattleController:GetBattleResult",
        };
        for (String t : targets) {
            String[] parts = t.split(":");
            findMethodOffset(parts[0], parts[1], pid);
        }
    }
}
