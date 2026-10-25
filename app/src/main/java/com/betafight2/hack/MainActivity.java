package com.betafight2.hack;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.betafight2.hack.menu.OverlayService;

public class MainActivity extends AppCompatActivity {

    private static final int REQ_OVERLAY = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        TextView tvStatus = findViewById(R.id.tvStatus);

        // Check Xposed active
        boolean xposedActive = isXposedActive();
        tvStatus.setText(xposedActive
                ? "✅ Xposed/LSPosed ACTIVE — hooks loaded"
                : "⚠️  Xposed NOT detected — overlay mode only");

        Button btnStart = findViewById(R.id.btnStart);
        btnStart.setOnClickListener(v -> {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                    && !Settings.canDrawOverlays(this)) {
                requestOverlayPermission();
            } else {
                startOverlay();
            }
        });

        Button btnLaunchGame = findViewById(R.id.btnLaunchGame);
        btnLaunchGame.setOnClickListener(v -> {
            try {
                Intent i = getPackageManager()
                        .getLaunchIntentForPackage("com.nekki.shadowfight");
                if (i != null) startActivity(i);
                else Toast.makeText(this, "Game not installed", Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Toast.makeText(this, "Launch failed: " + e.getMessage(),
                        Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void startOverlay() {
        Intent svc = new Intent(this, OverlayService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(svc);
        } else {
            startService(svc);
        }
        Toast.makeText(this, "Mod menu started", Toast.LENGTH_SHORT).show();
        finish();
    }

    private void requestOverlayPermission() {
        Intent i = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName()));
        startActivityForResult(i, REQ_OVERLAY);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == REQ_OVERLAY) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                    && Settings.canDrawOverlays(this)) {
                startOverlay();
            }
        }
    }

    // If Xposed is running, this method gets replaced by the hook
    private boolean isXposedActive() {
        return false;
    }
}
