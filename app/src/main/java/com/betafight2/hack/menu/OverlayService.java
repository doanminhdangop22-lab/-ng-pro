package com.betafight2.hack.menu;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

import androidx.core.app.NotificationCompat;

import com.betafight2.hack.R;
import com.betafight2.hack.core.HackConfig;

public class OverlayService extends Service {

    private static final String CH_ID = "bf2_hack";
    private WindowManager wm;
    private View rootView;
    private View menuPanel;
    private boolean menuVisible = true;

    // drag state
    private float dragStartX, dragStartY, viewStartX, viewStartY;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        startForeground(1, buildNotification());
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        showOverlay();
    }

    private void showOverlay() {
        LayoutInflater inf = LayoutInflater.from(this);
        rootView = inf.inflate(R.layout.overlay_menu, null);
        menuPanel = rootView.findViewById(R.id.menuPanel);

        // ── toggles ──────────────────────────────────────────────────────────
        bindSwitch(rootView, R.id.swGodMode,         v -> HackConfig.godMode         = v);
        bindSwitch(rootView, R.id.swOneHit,          v -> HackConfig.oneHitKill      = v);
        bindSwitch(rootView, R.id.swMaxDamage,       v -> HackConfig.maxDamage       = v);
        bindSwitch(rootView, R.id.swUnlimitedCoins,  v -> HackConfig.unlimitedCoins  = v);
        bindSwitch(rootView, R.id.swUnlimitedGems,   v -> HackConfig.unlimitedGems   = v);
        bindSwitch(rootView, R.id.swUnlimitedEnergy, v -> HackConfig.unlimitedEnergy = v);
        bindSwitch(rootView, R.id.swAutoWin,         v -> HackConfig.autoWin         = v);
        bindSwitch(rootView, R.id.swNoKnockback,     v -> HackConfig.noKnockback     = v);

        // ── speed seekbar ─────────────────────────────────────────────────────
        Switch swSpeed = rootView.findViewById(R.id.swSpeed);
        SeekBar seekSpeed = rootView.findViewById(R.id.seekSpeed);
        TextView tvSpeed = rootView.findViewById(R.id.tvSpeedVal);
        seekSpeed.setMax(40); // 1x–5x mapped 0–40 (step 0.1)
        seekSpeed.setProgress(10); // default 2x
        swSpeed.setOnCheckedChangeListener((b, checked) -> {
            HackConfig.speedHack = checked;
            seekSpeed.setEnabled(checked);
        });
        seekSpeed.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar s, int p, boolean u) {
                float val = 1f + p * 0.1f;
                HackConfig.speedMultiplier = val;
                tvSpeed.setText(String.format("%.1fx", val));
            }
            @Override public void onStartTrackingTouch(SeekBar s) {}
            @Override public void onStopTrackingTouch(SeekBar s) {}
        });

        // ── toggle button ─────────────────────────────────────────────────────
        View btnToggle = rootView.findViewById(R.id.btnToggle);
        btnToggle.setOnClickListener(v -> {
            menuVisible = !menuVisible;
            menuPanel.setVisibility(menuVisible ? View.VISIBLE : View.GONE);
        });

        // ── drag ──────────────────────────────────────────────────────────────
        btnToggle.setOnTouchListener((v, ev) -> {
            WindowManager.LayoutParams lp =
                    (WindowManager.LayoutParams) rootView.getLayoutParams();
            switch (ev.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    dragStartX = ev.getRawX();
                    dragStartY = ev.getRawY();
                    viewStartX = lp.x;
                    viewStartY = lp.y;
                    return false;
                case MotionEvent.ACTION_MOVE:
                    lp.x = (int)(viewStartX + ev.getRawX() - dragStartX);
                    lp.y = (int)(viewStartY + ev.getRawY() - dragStartY);
                    wm.updateViewLayout(rootView, lp);
                    return true;
            }
            return false;
        });

        int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.START;
        params.x = 0;
        params.y = 100;

        wm.addView(rootView, params);
    }

    private void bindSwitch(View root, int id, BoolCallback cb) {
        Switch sw = root.findViewById(id);
        if (sw == null) return;
        sw.setOnCheckedChangeListener((b, checked) -> cb.set(checked));
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (rootView != null) wm.removeView(rootView);
    }

    @Override public IBinder onBind(Intent i) { return null; }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                    CH_ID, "BF2 Hack", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("Mod menu running");
            getSystemService(NotificationManager.class).createNotificationChannel(ch);
        }
    }

    private Notification buildNotification() {
        return new NotificationCompat.Builder(this, CH_ID)
                .setContentTitle("BF2 Hack Active")
                .setContentText("Mod menu is running")
                .setSmallIcon(android.R.drawable.ic_menu_info_details)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();
    }

    interface BoolCallback {
        void set(boolean val);
    }
}
