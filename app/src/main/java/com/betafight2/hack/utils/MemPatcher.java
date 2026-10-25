package com.betafight2.hack.utils;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Direct /proc/<pid>/mem patcher.
 * Requires root. Used when Xposed hooks miss a native IL2CPP offset.
 *
 * Usage:
 *   MemPatcher p = new MemPatcher(targetPid);
 *   p.writeFloat(offset, 999999f);  // patch coin value at known offset
 */
public class MemPatcher {

    private final int pid;
    private final String memPath;

    public MemPatcher(int pid) {
        this.pid = pid;
        this.memPath = "/proc/" + pid + "/mem";
    }

    public static int findPid(String packageName) throws Exception {
        Process ps = Runtime.getRuntime().exec("su -c pidof " + packageName);
        byte[] buf = ps.getInputStream().readAllBytes();
        String s = new String(buf).trim();
        if (s.isEmpty()) throw new RuntimeException("Process not found: " + packageName);
        return Integer.parseInt(s.split("\\s+")[0]);
    }

    public void writeFloat(long addr, float value) throws Exception {
        byte[] bytes = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                .putFloat(value).array();
        writeBytes(addr, bytes);
    }

    public void writeInt(long addr, int value) throws Exception {
        byte[] bytes = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(value).array();
        writeBytes(addr, bytes);
    }

    public float readFloat(long addr) throws Exception {
        byte[] bytes = readBytes(addr, 4);
        return ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getFloat();
    }

    public int readInt(long addr) throws Exception {
        byte[] bytes = readBytes(addr, 4);
        return ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getInt();
    }

    private void writeBytes(long addr, byte[] data) throws Exception {
        // dd via root shell — fallback when /proc/mem write blocked
        String hex = bytesToHex(data);
        String cmd = String.format(
                "su -c 'printf \\x%s | dd of=%s bs=1 seek=%d conv=notrunc 2>/dev/null'",
                hex, memPath, addr);
        Runtime.getRuntime().exec(cmd).waitFor();
    }

    private byte[] readBytes(long addr, int len) throws Exception {
        // Read via dd
        String tmp = "/data/local/tmp/bf2mem_" + System.currentTimeMillis();
        String cmd = String.format(
                "su -c 'dd if=%s of=%s bs=1 skip=%d count=%d 2>/dev/null'",
                memPath, tmp, addr, len);
        Runtime.getRuntime().exec(cmd).waitFor();
        RandomAccessFile f = new RandomAccessFile(tmp, "r");
        byte[] buf = new byte[len];
        f.read(buf);
        f.close();
        new File(tmp).delete();
        return buf;
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02x", b));
        return sb.toString();
    }

    // ── Known IL2CPP offsets (dump.cs derived, version-specific) ────────────
    // Re-derive with: apktool d game.apk && strings libil2cpp.so | grep -i "coins\|gems\|health"
    // Or use GameGuardian fuzzy search on known value then freeze.
    public static class Offsets {
        // BetaFight2 / SF2 mod — patch these after running offset_dump.sh
        public static long PLAYER_HP       = 0x0L; // float
        public static long PLAYER_MAX_HP   = 0x0L; // float
        public static long COINS           = 0x0L; // int32
        public static long GEMS            = 0x0L; // int32
        public static long ENERGY          = 0x0L; // int32
        public static long TIMESCALE       = 0x0L; // float (Unity Time.timeScale)
        public static long ENEMY_HP        = 0x0L; // float
    }
}
