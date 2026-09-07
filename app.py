#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>AETHERWAVE · 12色时辰 | 深度记忆电台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        /* ========== 12色时辰主题变量 ========== */
        body.theme-0 { --text-primary: #aaccff; --text-secondary: #88aadd; --accent-green: #2ecc71; --accent-orange: #f39c12; --accent-cyan: #00d2ff; --quote-color: #ccf6ff; --status-color: #aaffdd; --glass-bg: rgba(10, 20, 35, 0.7); --card-bg: #0a0f1fcc; --glow-green: rgba(46, 204, 113, 0.3); }
        body.theme-2 { --text-primary: #99bbee; --text-secondary: #7799cc; --accent-green: #27ae60; --accent-orange: #e67e22; --accent-cyan: #00b4d8; --quote-color: #bbe6ff; --status-color: #99eebb; --glass-bg: rgba(8, 12, 28, 0.75); --card-bg: #080c1ccc; --glow-green: rgba(39, 174, 96, 0.3); }
        body.theme-4 { --text-primary: #ddbbff; --text-secondary: #ccaaee; --accent-green: #9b59b6; --accent-orange: #f1c40f; --accent-cyan: #7f8c8d; --quote-color: #f0e6ff; --status-color: #e0ccff; --glass-bg: rgba(30, 20, 40, 0.7); --card-bg: #18102ccc; --glow-green: rgba(155, 89, 182, 0.3); }
        body.theme-6 { --text-primary: #ffde9c; --text-secondary: #ffcc77; --accent-green: #f1c40f; --accent-orange: #e67e22; --accent-cyan: #85c1e9; --quote-color: #fff2cc; --status-color: #ffe0aa; --glass-bg: rgba(45, 30, 15, 0.7); --card-bg: #2a1e12cc; --glow-green: rgba(241, 196, 15, 0.3); }
        body.theme-8 { --text-primary: #ffe0aa; --text-secondary: #ffcc88; --accent-green: #2ecc71; --accent-orange: #f39c12; --accent-cyan: #48c9b0; --quote-color: #fff8e7; --status-color: #ffefbf; --glass-bg: rgba(35, 40, 25, 0.7); --card-bg: #1f2a18cc; --glow-green: rgba(46, 204, 113, 0.25); }
        body.theme-10 { --text-primary: #fff0cc; --text-secondary: #ffe0aa; --accent-green: #2ecc71; --accent-orange: #f1c40f; --accent-cyan: #3498db; --quote-color: #fffae6; --status-color: #fff0cc; --glass-bg: rgba(50, 45, 25, 0.7); --card-bg: #2a2818cc; --glow-green: rgba(46, 204, 113, 0.3); }
        body.theme-12 { --text-primary: #eef5ff; --text-secondary: #d0e4ff; --accent-green: #1abc9c; --accent-orange: #e67e22; --accent-cyan: #00e5ff; --quote-color: #f0ffff; --status-color: #ccffe0; --glass-bg: rgba(30, 40, 55, 0.7); --card-bg: #1e2a33cc; --glow-green: rgba(26, 188, 156, 0.25); }
        body.theme-14 { --text-primary: #ffddb5; --text-secondary: #ffc88a; --accent-green: #e67e22; --accent-orange: #d35400; --accent-cyan: #f5b041; --quote-color: #ffefd6; --status-color: #ffdbb5; --glass-bg: rgba(55, 40, 20, 0.7); --card-bg: #2f2818cc; --glow-green: rgba(230, 126, 34, 0.25); }
        body.theme-16 { --text-primary: #ffc99e; --text-secondary: #ffb37b; --accent-green: #f39c12; --accent-orange: #e67e22; --accent-cyan: #f7dc6f; --quote-color: #ffe5cc; --status-color: #ffd4b0; --glass-bg: rgba(50, 35, 20, 0.7); --card-bg: #2f2418cc; --glow-green: rgba(243, 156, 18, 0.3); }
        body.theme-18 { --text-primary: #ffaa77; --text-secondary: #ff9466; --accent-green: #ff8c42; --accent-orange: #ff5722; --accent-cyan: #ffaa66; --quote-color: #ffe0cc; --status-color: #ffccaa; --glass-bg: rgba(55, 30, 15, 0.75); --card-bg: #2a1c10cc; --glow-green: rgba(255, 140, 66, 0.3); }
        body.theme-20 { --text-primary: #ccb5ff; --text-secondary: #b095e6; --accent-green: #9b59b6; --accent-orange: #e84393; --accent-cyan: #48c9b0; --quote-color: #e6ddff; --status-color: #d5c5ff; --glass-bg: rgba(25, 20, 45, 0.75); --card-bg: #18122ccc; --glow-green: rgba(155, 89, 182, 0.25); }
        body.theme-22 { --text-primary: #8899cc; --text-secondary: #6677aa; --accent-green: #2c3e50; --accent-orange: #c0392b; --accent-cyan: #5dade2; --quote-color: #cce0ff; --status-color: #aaccff; --glass-bg: rgba(8, 10, 25, 0.8); --card-bg: #0a0c1ccc; --glow-green: rgba(52, 152, 219, 0.2); }

        body {
            background: radial-gradient(circle at 30% 10%, #0a0a14, #010105);
            font-family: 'Share Tech Mono', 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            transition: background 0.6s ease, color 0.3s ease;
            color: var(--text-primary);
        }
        .radio-chassis {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            background: var(--card-bg);
            border-radius: 48px 48px 36px 36px;
            box-shadow: 0 30px 45px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.08);
            border: 1px solid rgba(80,80,110,0.4);
            overflow: hidden;
            backdrop-filter: blur(2px);
        }
        .glass-header {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--accent-green);
            flex-wrap: wrap;
            gap: 8px;
        }
        .brand {
            color: var(--accent-green);
            text-shadow: 0 0 5px var(--accent-green);
            font-weight: bold;
            letter-spacing: 1.5px;
            font-size: 1.1rem;
            display: flex;
            align-items: baseline;
            gap: 12px;
            flex-wrap: wrap;
        }
        .word-rotator {
            font-size: 0.65rem;
            color: #ffdd99;
            background: #0a0a1288;
            padding: 2px 8px;
            border-radius: 30px;
            letter-spacing: 1px;
        }
        .clock-panel, .header-btn {
            background: #000000aa;
            padding: 4px 12px;
            border-radius: 30px;
            font-family: monospace;
            font-size: 0.9rem;
            color: var(--accent-cyan);
            box-shadow: inset 0 0 8px rgba(0,229,255,0.3);
        }
        .country-tuner, .layout-mode-switch, .mute-header-btn {
            background: #0a0a12;
            border: 1px solid #4a4a5a;
            color: var(--accent-orange);
            padding: 4px 10px;
            border-radius: 28px;
            font-family: monospace;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.7rem;
            transition: all 0.2s;
        }
        .layout-mode-switch:hover, .mute-header-btn:hover {
            background: #1a1a2a;
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
        }
        .dual-panel, .triple-panel {
            display: flex;
            gap: 16px;
            padding: 16px 16px 6px 16px;
            flex-wrap: wrap;
        }
        .channel-section {
            flex: 0.4;
            min-width: 170px;
            background: #020208cc;
            border-radius: 28px;
            border: 1px solid #2f2f3e;
            backdrop-filter: blur(4px);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .spectrum-quote-panel, .spectrum-card {
            background: #000000;
            border-radius: 28px;
            border: 2px solid #2b2b3a;
            box-shadow: 0 0 16px rgba(0,255,122,0.18);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .triple-panel .channel-section { flex: 1; }
        .triple-panel .spectrum-card { flex: 2; }
        .triple-panel .control-card { flex: 1; background: #020208cc; border-radius: 28px; border: 1px solid #2f2f3e; backdrop-filter: blur(4px); overflow-y: auto; }
        .section-title {
            background: #0b0b14;
            padding: 8px 12px;
            font-size: 0.65rem;
            color: var(--text-secondary);
            border-bottom: 1px solid #2a2a36;
            letter-spacing: 2px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .station-list {
            flex: 1;
            overflow-y: auto;
            padding: 6px 4px;
            max-height: 340px;
        }
        .channel-item {
            padding: 6px 6px;
            margin: 4px 3px;
            background: #0b0b12;
            border-left: 4px solid #2c2c3c;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.65rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-primary);
        }
        .channel-item.active {
            background: linear-gradient(90deg, #1a2a1a, #0a120a);
            border-left-color: var(--accent-green);
            color: var(--accent-green);
            text-shadow: 0 0 3px var(--accent-green);
        }
        .quote-header {
            background: rgba(8, 8, 16, 0.85);
            padding: 6px 12px;
            border-bottom: 1px solid #2b2b3a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            backdrop-filter: blur(4px);
        }
        .time-slot-title {
            color: var(--accent-orange);
            text-shadow: 0 0 4px var(--accent-orange);
            font-weight: bold;
            font-size: 0.65rem;
        }
        .radio-status {
            color: var(--status-color);
            font-family: monospace;
            font-size: 0.6rem;
        }
        .viz-wrapper {
            position: relative;
            background: #010105;
            min-height: 180px;
            height: 180px;
            width: 100%;
        }
        canvas { width: 100%; height: 180px; display: block; }
        #waveCanvas { position: absolute; top:0; left:0; z-index:1; }
        #spectrumCanvas { position: absolute; top:0; left:0; z-index:2; opacity:0.92; }
        .crt-overlay {
            position: absolute;
            top:0; left:0; right:0; bottom:0;
            background: repeating-linear-gradient(0deg, rgba(0,255,100,0.05) 0px, rgba(0,255,100,0.05) 2px, transparent 2px, transparent 8px);
            pointer-events: none;
            z-index:3;
        }
        .quote-scroll-area {
            background: rgba(2,2,10,0.94);
            border-top: 1px solid #2f8a4e;
            padding: 8px 12px;
            backdrop-filter: blur(8px);
            min-height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .rolling-quote {
            font-size: 0.7rem;
            color: var(--quote-color);
            text-shadow: 0 0 5px #0eaaff;
            text-align: center;
            transition: all 0.2s ease;
        }
        .eq-bands-panel {
            background: rgba(5,5,12,0.2);
            border-radius: 24px;
            margin: 8px 12px;
            padding: 8px 12px;
            border: 1px solid rgba(58,122,106,0.5);
            backdrop-filter: blur(4px);
        }
        .bands-title {
            display: flex;
            justify-content: space-between;
            font-size: 0.55rem;
            color: #bbffdd;
            margin-bottom: 8px;
        }
        .bands-grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 4px;
        }
        .band-item {
            flex: 1;
            min-width: 50px;
            text-align: center;
            background: #0c0c1a;
            border-radius: 28px;
            padding: 5px 2px;
            border-bottom: 2px solid #3a8a6a;
        }
        .band-gain { font-size: 0.75rem; font-weight:800; color:#ffffbb; }
        .control-deck, .control-deck-compact {
            background: linear-gradient(145deg, #12121c, #0a0a10);
            border-radius: 36px 36px 32px 32px;
            padding: 16px 20px 22px;
            margin-top: 4px;
        }
        .dual-control-layout {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: flex-start;
            gap: 12px;
            margin-bottom: 20px;
        }
        .freq-group-dual {
            display: flex;
            align-items: center;
            gap: 6px;
            background: #010108aa;
            border-radius: 40px;
            padding: 4px 12px;
        }
        .right-control-group {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            flex: 1;
        }
        .preset-strip-dual {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .dual-action-stack {
            display: flex;
            gap: 6px;
        }
        .freq-arrow-mini {
            background: #1c1c2a;
            border: 1px solid #5a5a7a;
            border-radius: 40px;
            width: 36px;
            height: 36px;
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--accent-orange);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: 0.05s linear;
        }
        .freq-arrow-mini:active { transform: scale(0.94); }
        .freq-num-mini {
            font-size: 1.2rem;
            font-family: 'Orbitron', monospace;
            color: var(--accent-orange);
            font-weight: bold;
            min-width: 60px;
            text-align: center;
        }
        .triple-control-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            padding: 0 8px;
        }
        .triple-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .preset-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .action-btn, .preset-btn {
            background: linear-gradient(145deg, #1c1c28, #0f0f18);
            border: 1px solid #3a3a4e;
            border-radius: 60px;
            font-family: monospace;
            font-weight: bold;
            font-size: 0.65rem;
            color: #7df9ff;
            text-shadow: 0 0 5px #00aaff;
            cursor: pointer;
            transition: 0.1s ease;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            width: 52px;
            padding: 4px 0;
            box-shadow: 0 2px 0 #030308;
        }
        .preset-btn {
            background: #1c1c28;
            color: #3a86ff;
        }
        .action-btn:active, .preset-btn:active {
            transform: translateY(2px);
            box-shadow: 0 0px 0 #030308;
        }
        .action-btn.surround-active {
            background: radial-gradient(ellipse at 30% 30%, #2a6f3a, #0f3a1a);
            border-color: var(--accent-green);
            color: var(--accent-green);
            text-shadow: 0 0 6px #0eff7a;
        }
        .preset-btn.saved {
            color: var(--accent-orange);
            border-bottom: 2px solid #ff7032;
            background: linear-gradient(180deg, #1c1c28, #2a1f14);
        }
        .eq-label, .preset-label {
            font-size: 0.45rem;
            display: block;
            opacity: 0.8;
        }
        .freq-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            background: #010108aa;
            border-radius: 60px;
            padding: 6px 16px;
            margin: 12px 0;
        }
        .freq-arrow {
            background: #1c1c2a;
            border: 1px solid #5a5a7a;
            border-radius: 40px;
            width: 44px;
            height: 44px;
            font-size: 1.6rem;
            font-weight: bold;
            color: var(--accent-orange);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .freq-arrow:active { transform: scale(0.94); }
        .freq-num {
            font-size: 32px;
            font-family: 'Orbitron', monospace;
            color: var(--accent-orange);
            font-weight: bold;
            min-width: 100px;
            text-align: center;
        }
        .freq-unit {
            font-size: 14px;
            color: #ccaaff;
            margin-left: 5px;
        }
        .stacked-container {
            background: #0a0a14cc;
            border-radius: 24px;
            padding: 8px 12px;
            margin-top: 16px;
            backdrop-filter: blur(4px);
        }
        .stacked-title { font-size:0.55rem; color:var(--accent-cyan); margin-bottom:6px; }
        .stacked-chips { display:flex; flex-wrap:wrap; gap:6px; }
        .stack-chip {
            background:#2a2a3a; border-radius:40px; padding:3px 10px; font-size:0.55rem;
            display:inline-flex; align-items:center; gap:6px; color:#bbffdd;
            border-left:3px solid var(--accent-green); cursor:pointer;
        }
        .stack-chip .remove-stack { color:#ff8866; font-weight:bold; cursor:pointer; }
        .modal {
            position:fixed; top:0; left:0; width:100%; height:100%;
            background:rgba(0,0,0,0.3); backdrop-filter:blur(3px); z-index:2000;
            display:flex; justify-content:center; align-items:center;
            visibility:hidden; opacity:0; transition:visibility 0.2s, opacity 0.2s;
        }
        .modal.active { visibility:visible; opacity:1; }
        .modal-content {
            background:rgba(10,10,20,0.7); backdrop-filter:blur(8px);
            border-radius:44px; padding:20px; width:320px; max-width:85vw;
            border:2px solid rgba(42,138,94,0.6); max-height:80vh; overflow-y:auto;
        }
        .modal-item {
            background:rgba(20,20,35,0.6); margin:6px 0; padding:8px 12px;
            border-radius:60px; cursor:pointer; font-size:0.7rem;
            display:flex; align-items:center; gap:10px; color:#ccddff;
            border:1px solid rgba(51,68,85,0.5);
        }
        .modal-item.selected { background:rgba(42,106,58,0.6); border-left:4px solid var(--accent-green); }
        .modal-item.multi-selected { background:#2a4a3a; border-left:4px solid #ffaa33; }
        .badge-icon { font-size:0.55rem; background:#ffaa33; color:#000; border-radius:20px; padding:2px 6px; margin-left:6px; }
        .close-modal { text-align:center; margin-top:16px; padding:8px; cursor:pointer; font-size:0.7rem; border-top:1px solid #334455; color:#ff5555; }
        @media (max-width:700px) {
            .action-btn, .preset-btn { width:44px; font-size:0.6rem; }
            .freq-arrow-mini { width:32px; height:32px; font-size:1rem; }
            .freq-num-mini { font-size:1rem; min-width:50px; }
            .station-list { max-height:280px; }
        }

        /* 注册覆盖层 */
        #powerOverlay {
            position: fixed; top:0; left:0; width:100%; height:100%;
            background: radial-gradient(ellipse at center,#02020b,#000);
            z-index:3000; display:flex; justify-content:center; align-items:center;
            backdrop-filter:blur(14px);
        }
        .register-box {
            background:rgba(20,20,40,0.9); border-radius:48px; padding:30px 25px;
            text-align:center; width:320px; max-width:85vw;
            box-shadow:0 0 30px rgba(100,255,150,0.3); border:1px solid #4affaa;
        }
        .register-box input {
            background:#0a0a12; border:1px solid #6a7a9a; color:#ffdd99;
            padding:12px; border-radius:40px; width:100%; font-family:monospace;
            text-align:center; margin:15px 0; outline:none;
        }
        .register-box button {
            background:linear-gradient(145deg,#222232,#0e0e18); border:1px solid #4a6a7a;
            border-radius:60px; padding:10px 20px; font-family:monospace;
            font-weight:bold; font-size:1rem; color:#c0ffff; cursor:pointer; width:100%;
        }
        .error-msg { color:#ff8866; font-size:0.75rem; margin-top:12px; min-height:40px; }
        .hidden { display:none !important; }
    </style>
</head>
<body>

<!-- 注册覆盖层（时间戳授权） -->
<div id="powerOverlay">
    <div class="register-box">
        <h2>⏻ AETHERWAVE</h2>
        <p style="color:#ccddff;">请输入注册码🎵💘🎗💞</p>
        <input type="text" id="licenseCode" placeholder="10位数字" maxlength="10" inputmode="numeric">
        <button id="verifyAndStartBtn">🎧 验证并开机</button>
        <div class="error-msg" id="licenseError"></div>
        <div class="info-text">💡 输入有效注册码即可激活</div>
    </div>
</div>

<div id="radioApp" style="opacity:0; transition:opacity 0.7s ease;">
    <div class="radio-chassis">
        <div class="glass-header">
            <div class="brand">
                ◢ AETHERWAVE 
                <span class="word-rotator" id="wordRotator">--</span>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="clock-panel" id="liveClock">--:--:--</span>
                <select id="countrySelect" class="country-tuner">
                    <option value="China">🇨🇳 中国之声</option>
                    <option value="United States">🇺🇸 自由之音</option>
                    <option value="Japan">🇯🇵 J-WAVE</option>
                    <option value="United Kingdom">🇬🇧 英伦电波</option>
                    <option value="Germany">🇩🇪 德意志频率</option>
                    <option value="France">🇫🇷 法式香颂</option>
                </select>
                <button id="globalLayoutSwitch" class="layout-mode-switch">⟲ 双列</button>
                <button id="globalMuteBtn" class="mute-header-btn">🔇 静音</button>
            </div>
        </div>
        <div id="layoutRoot"></div>
    </div>
</div>
<div id="eqModal" class="modal">
    <div class="modal-content">
        <h3>🎛️ 智能环绕音效库 · 点击多选叠加</h3>
        <div id="presetList"></div>
        <div class="close-modal" id="closeModal">✖ 关闭</div>
    </div>
</div>

<script>
    (function(){
        // ========== 注册码验证（时间戳模式） ==========
        const LICENSE_KEY = "aetherwave_ts_license";
        function getCurrentSecond(){ return Math.floor(Date.now()/1000); }
        function checkStoredLicense(){
            let data = localStorage.getItem(LICENSE_KEY);
            if(!data) return null;
            try{
                let {expiry} = JSON.parse(data);
                if(getCurrentSecond() < expiry) return expiry;
                else localStorage.removeItem(LICENSE_KEY);
            }catch(e){}
            return null;
        }
        function saveLicense(expiry){
            localStorage.setItem(LICENSE_KEY, JSON.stringify({expiry: expiry}));
        }
        function verifyCode(code){
            if(!/^\d{10}$/.test(code)) return false;
            let ts = parseInt(code,10);
            if(getCurrentSecond() >= ts) return false;
            saveLicense(ts);
            return true;
        }
        let isLicensed = false;
        let powerOverlay = document.getElementById('powerOverlay');
        let radioAppDiv = document.getElementById('radioApp');
        function showLicensedUI(){
            if(powerOverlay) powerOverlay.classList.add('hidden');
            if(radioAppDiv) radioAppDiv.style.opacity = "1";
            isLicensed = true;
            startMainApp();
        }
        const storedExp = checkStoredLicense();
        if(storedExp){
            showLicensedUI();
        } else {
            const verifyBtn = document.getElementById('verifyAndStartBtn');
            const codeInput = document.getElementById('licenseCode');
            const errSpan = document.getElementById('licenseError');
            verifyBtn.onclick = () => {
                let code = codeInput.value.trim();
                if(verifyCode(code)){
                    errSpan.innerHTML = "✅ 授权成功！";
                    showLicensedUI();
                } else {
                    errSpan.innerHTML = "❌ 无效授权码";
                }
            };
            codeInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') verifyBtn.click(); });
        }

        // ========== 原有全局变量 ==========
        let isPowered=true, currentIdx=-1;
        let stationsList=[];
        let presetUrls=new Array(9).fill("");
        let audioCtx=null, radioPlayer=new Audio(), analyser=null, masterGain=null, drcCompressor=null, stereoPanner=null, reverbNode=null, reverbDry=null, reverbWet=null;
        let eqFilters=[];
        let currentEffect="Original";
        let volumeRotation=-35;
        let fineOffset=0;
        let frameId=null;
        let currentLayoutMode='triple';
        let autoLayout=true;
        let isSurroundEnabled=false;
        let stackedEffects=[];
        let hasPlayedStartupSound = false;
        let isMuted = false;
        let previousVolume = 0.85;
        let autoPlayChecker = null;
        let wordRotatorInterval = null;

        // ========== 三维海浪环绕引擎 (全新替换) ==========
        let panner3D = null;
        let surroundAnimationId = null;
        function getLowFreqEnergy(){
            if(!analyser) return 0.3;
            const freqData = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(freqData);
            let sum=0, bins=Math.min(20,freqData.length);
            for(let i=0;i<bins;i++) sum+=freqData[i];
            let avg=sum/bins/255;
            return Math.min(0.85, Math.max(0.1, avg*1.2));
        }
        function insert3DPanner(){
            if(!audioCtx || !eqFilters.length) return false;
            const lastFilter = eqFilters[eqFilters.length-1];
            if(panner3D && lastFilter && lastFilter.connect){
                try{
                    lastFilter.disconnect(analyser);
                    lastFilter.connect(panner3D);
                    panner3D.connect(analyser);
                    return true;
                }catch(e){}
            }
            if(!panner3D){
                panner3D = audioCtx.createPanner();
                panner3D.panningModel = 'HRTF';
                panner3D.distanceModel = 'inverse';
                panner3D.refDistance = 1;
                panner3D.maxDistance = 8;
                panner3D.rolloffFactor = 0.6;
                panner3D.positionX.value = 0;
                panner3D.positionY.value = 0;
                panner3D.positionZ.value = 1.5;
            }
            try{
                lastFilter.disconnect(analyser);
                lastFilter.connect(panner3D);
                panner3D.connect(analyser);
                return true;
            }catch(e){ return false; }
        }
        function remove3DPanner(){
            if(!audioCtx || !eqFilters.length) return;
            const lastFilter = eqFilters[eqFilters.length-1];
            if(panner3D){
                try{
                    lastFilter.disconnect(panner3D);
                    panner3D.disconnect(analyser);
                    lastFilter.connect(analyser);
                }catch(e){}
            }
            if(panner3D) { panner3D.positionX.value = 0; panner3D.positionY.value = 0; panner3D.positionZ.value = 0; }
        }
        function start3DSurround(){
            if(!audioCtx) return;
            const success = insert3DPanner();
            if(!success) return;
            if(surroundAnimationId) cancelAnimationFrame(surroundAnimationId);
            let angle = 0, fastAngle = 0, lastTime = 0;
            function animate(t){
                if(!isSurroundEnabled){
                    if(surroundAnimationId){ cancelAnimationFrame(surroundAnimationId); surroundAnimationId = null; remove3DPanner(); }
                    return;
                }
                if(!lastTime) lastTime = t;
                let dt = Math.min(0.05, (t-lastTime)/1000);
                lastTime = t;
                let energy = getLowFreqEnergy();
                let baseSpeed = 1.2 + energy * 1.8;
                angle += baseSpeed * dt;
                fastAngle += (baseSpeed * 2.3) * dt;
                let radius = 1.0 + energy * 1.5;
                let x = Math.cos(angle) * radius;
                let z = Math.sin(angle) * radius;
                let yAmp = 0.6 + energy * 1.2;
                let y = Math.sin(angle * 1.7) * yAmp + Math.sin(fastAngle * 1.2) * 0.5;
                let chaseX = Math.sin(angle * 2.2) * 0.5 * energy;
                let chaseZ = Math.cos(angle * 2.5) * 0.5 * energy;
                x += chaseX; z += chaseZ;
                let pulse = Math.sin(angle * 4.0) * 0.4 * energy;
                x += pulse * Math.cos(angle);
                z += pulse * Math.sin(angle);
                x = Math.min(3.0, Math.max(-3.0, x));
                z = Math.min(3.0, Math.max(-3.0, z));
                y = Math.min(2.5, Math.max(-2.5, y));
                if(panner3D){
                    panner3D.positionX.value = x;
                    panner3D.positionY.value = y;
                    panner3D.positionZ.value = z;
                }
                surroundAnimationId = requestAnimationFrame(animate);
            }
            surroundAnimationId = requestAnimationFrame(animate);
        }
        function stopSurround(){
            if(surroundAnimationId){ cancelAnimationFrame(surroundAnimationId); surroundAnimationId = null; }
            remove3DPanner();
        }

        // 音效预设
        const EFFECT_PRESETS = { "Original":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0,reverb:0,gain:0},"headset":{eq:[2,1,0,2,3,2,1,0,0,0],drc:false,stereo:0,reverb:0,gain:0},"headset2":{eq:[12,10,8,3,0,-2,-3,-2,0,0],drc:false,stereo:0,reverb:0,gain:0},"headset3":{eq:[8,6,4,-2,-4,-6,-4,-2,0,2],drc:false,stereo:0,reverb:0,gain:0},"speaker":{eq:[-12,-12,-6,-3,0,2,3,4,3,2],drc:false,stereo:0,reverb:0,gain:0},"voice_clean":{eq:[-6,-4,-2,-1,2,5,3,1,0,-1],drc:false,stereo:0,reverb:0,gain:5},"bass_enhance":{eq:[10,8,6,2,0,-1,-2,-1,0,0],drc:false,stereo:0,reverb:0,gain:0},"stereo_enhance":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0.8,reverb:0,gain:0},"360_all":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0.5,reverb:0.25,gain:0},"hifi_live":{eq:[0,0,1,2,2,3,3,2,1,0],drc:false,stereo:0.2,reverb:0.3,gain:0},"vibrant_electronic":{eq:[4,3,2,1,0,0,2,4,5,4],drc:false,stereo:0.3,reverb:0.28,gain:10},"vinyl":{eq:[-8,-6,-4,-2,0,2,1,0,-2,-4],drc:false,stereo:0,reverb:0.15,gain:2},"rock":{eq:[8,6,4,2,0,1,2,4,6,8],drc:false,stereo:0,reverb:0,gain:0},"intelligent":{eq:[3,2,1,0,0,1,2,3,4,3],drc:true,stereo:0.15,reverb:0.1,gain:0},
            "🌊 三维海浪环绕":{eq:[1,1,1,0,0,1,2,3,3,2],drc:false,stereo:0.2,reverb:0.15,gain:0} };
        const EFFECT_NAMES = Object.keys(EFFECT_PRESETS);
        const FREQ_BANDS = ["31Hz","62Hz","125Hz","250Hz","500Hz","1kHz","2kHz","4kHz","8kHz","14kHz"];

        function mergeEffects(effectsList) { if(!effectsList.length) return EFFECT_PRESETS["Original"]; let sumEq=new Array(10).fill(0), drcFlag=false, stereoSum=0, reverbMax=0, gainSum=0; for(let name of effectsList){ let p=EFFECT_PRESETS[name]; if(!p) continue; for(let i=0;i<10;i++) sumEq[i]+=p.eq[i]; if(p.drc) drcFlag=true; stereoSum+=p.stereo; if(p.reverb>reverbMax) reverbMax=p.reverb; gainSum+=p.gain; } let count=effectsList.length; for(let i=0;i<10;i++) sumEq[i]=Math.min(20,Math.max(-20,sumEq[i])); return { eq:sumEq, drc:drcFlag, stereo:stereoSum/count, reverb:reverbMax, gain:gainSum }; }
        function applyMergedSurround(){ if(!eqFilters.length) return; let merged=mergeEffects(stackedEffects); for(let i=0;i<10;i++) eqFilters[i].gain.value=merged.eq[i]; if(stereoPanner) stereoPanner.pan.value=merged.stereo; if(drcCompressor){ if(merged.drc) { drcCompressor.threshold.value=-16.8; drcCompressor.ratio.value=3.15; } else { drcCompressor.threshold.value=-100; drcCompressor.ratio.value=1; } } if(reverbWet && reverbDry){ reverbWet.gain.value=merged.reverb*0.5; reverbDry.gain.value=1-merged.reverb*0.3; } if(masterGain){ applyVolume(); } renderBandsUIWithEq(merged.eq); updateEqLabelSurround(); refreshWordRotatorContent(); }
        function renderBandsUIWithEq(eqVals){ let container=document.getElementById("bandsGrid"); if(!container) return; container.innerHTML=""; for(let i=0;i<FREQ_BANDS.length;i++){ let val=eqVals[i]; let bandDiv=document.createElement("div"); bandDiv.className="band-item"; bandDiv.innerHTML=`<div class="band-freq">${FREQ_BANDS[i]}</div><div class="band-gain">${val>0?'+'+val:val}<span class="band-db">dB</span></div>`; container.appendChild(bandDiv); } }
        function updateEqLabelSurround(){ let lab=document.getElementById("eqLabel"); if(lab) lab.innerText=isSurroundEnabled?`环绕+${stackedEffects.length}`:currentEffect; }
        function renderStackedChips(){ let container = document.getElementById(currentLayoutMode==='triple'?'stackedEffectsContainer':'stackedEffectsContainerDual'); if(!container) return; if(!isSurroundEnabled || stackedEffects.length===0){ container.innerHTML=`<div class="stacked-title">🌀 智能环绕未激活，点击EQ选择叠加音效</div>`; return; } let html=`<div class="stacked-title">🔊 已叠加 (点击移除)</div><div class="stacked-chips">`; stackedEffects.forEach(eff=>{ html+=`<div class="stack-chip" data-effect="${eff}">${eff} <span class="remove-stack" data-effect="${eff}">✖</span></div>`; }); html+=`</div>`; container.innerHTML=html; document.querySelectorAll(".remove-stack").forEach(el=>{ el.addEventListener("click",(e)=>{ e.stopPropagation(); let name=el.getAttribute("data-effect"); if(name){ let idx=stackedEffects.indexOf(name); if(idx!==-1) stackedEffects.splice(idx,1); if(stackedEffects.length===0) applyMergedSurround(); else applyMergedSurround(); renderStackedChips(); if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti(); refreshWordRotatorContent(); } }); }); }
        
        // 环绕键新逻辑: 控制三维海浪引擎
        function toggleSurroundMode(){
            isSurroundEnabled = !isSurroundEnabled;
            if(isSurroundEnabled){
                if(!stackedEffects.includes(currentEffect) && currentEffect!=="Original") stackedEffects.unshift(currentEffect);
                else if(stackedEffects.length===0 && currentEffect!=="Original") stackedEffects.push(currentEffect);
                applyMergedSurround();
                start3DSurround();   // 启动三维环绕
            } else {
                let lastSingle=stackedEffects.length>0?stackedEffects[stackedEffects.length-1]:currentEffect;
                currentEffect=lastSingle;
                applyEffectSingle();
                stackedEffects=[];
                stopSurround();      // 停止三维环绕
            }
            let toggleBtn=document.getElementById(currentLayoutMode==='triple'?'surroundToggleBtn':'surroundToggleBtnDual');
            if(toggleBtn) toggleBtn.classList.toggle('surround-active',isSurroundEnabled);
            let span=toggleBtn?.querySelector('span');
            if(span) span.innerText=isSurroundEnabled?'ON':'OFF';
            renderStackedChips();
            updateEqLabelSurround();
            if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti();
            refreshWordRotatorContent();
        }

        function applyEffectSingle(){ if(!eqFilters.length) return; let preset=EFFECT_PRESETS[currentEffect]; for(let i=0;i<10;i++) eqFilters[i].gain.value=preset.eq[i]; if(stereoPanner) stereoPanner.pan.value=preset.stereo||0; if(drcCompressor){ if(preset.drc) { drcCompressor.threshold.value=-16.8; drcCompressor.ratio.value=3.15; } else { drcCompressor.threshold.value=-100; drcCompressor.ratio.value=1; } } if(reverbWet && reverbDry){ reverbWet.gain.value=(preset.reverb||0)*0.5; reverbDry.gain.value=1-(preset.reverb||0)*0.3; } if(masterGain){ applyVolume(); } renderBandsUIWithEq(preset.eq); updateEqLabelSurround(); refreshWordRotatorContent(); }
        
        function setEffect(effectName){ 
            if(isSurroundEnabled){ 
                if(stackedEffects.includes(effectName)){ let idx=stackedEffects.indexOf(effectName); stackedEffects.splice(idx,1); if(stackedEffects.length===0) applyMergedSurround(); else applyMergedSurround(); } 
                else { stackedEffects.push(effectName); applyMergedSurround(); } 
                renderStackedChips(); 
                if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti(); 
            } else { 
                if(currentEffect===effectName) return; 
                currentEffect=effectName; 
                applyEffectSingle(); 
                showMsg(`音效: ${effectName}`); 
            } 
            refreshWordRotatorContent(); 
        }
        
        function renderEQModalMulti(){ let listDiv=document.getElementById("presetList"); if(!listDiv) return; listDiv.innerHTML=""; EFFECT_NAMES.forEach(name=>{ let item=document.createElement("div"); let isSelected=isSurroundEnabled?stackedEffects.includes(name):(currentEffect===name); item.className=`modal-item ${isSelected?(isSurroundEnabled?"multi-selected":"selected"):""}`; let preset=EFFECT_PRESETS[name]; let badge=""; if(preset.drc) badge='<span class="badge-icon">DRC</span>'; else if(preset.reverb>0) badge='<span class="badge-icon">RVB</span>'; else if(preset.stereo>0) badge='<span class="badge-icon">STEREO</span>'; item.innerHTML=`<span class="sound-icon">🎵</span><span>${name}</span>${badge}`; item.onclick=()=>{ setEffect(name); renderEQModalMulti(); }; listDiv.appendChild(item); }); }
        
        function showMsg(m){ let st=document.getElementById("radioStatus"); if(st){ st.innerHTML=`📢 ${m}`; setTimeout(()=>{ if(stationsList[currentIdx] && !radioPlayer.paused) st.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${stationsList[currentIdx]?.name?.substring(0,18)}`; else if(stationsList[currentIdx]) st.innerHTML=stationsList[currentIdx]?.name?.substring(0,20); else st.innerHTML="AETHERWAVE"; },2000); } }
        function updateFreqDisplay(raw){ let base=raw/10; let final=base+fineOffset; final=Math.min(108,Math.max(87,final)); let spanTriple=document.getElementById("frequencyValue"); if(spanTriple) spanTriple.innerText=final.toFixed(1); let spanDual=document.getElementById("frequencyValueDual"); if(spanDual) spanDual.innerText=final.toFixed(1); }
        function prevStation(){ if(!stationsList.length) return; let newIdx=currentIdx-1; if(newIdx<0) newIdx=stationsList.length-1; selectStation(newIdx); }
        function nextStation(){ if(!stationsList.length) return; let newIdx=currentIdx+1; if(newIdx>=stationsList.length) newIdx=0; selectStation(newIdx); }
        function selectStation(idx){ if(!stationsList[idx]) return; currentIdx=idx; let st=stationsList[idx]; radioPlayer.pause(); radioPlayer.src=''; setTimeout(()=>{ radioPlayer.src=st.url_resolved; radioPlayer.load(); radioPlayer.play().catch(err=>console.warn("播放失败",err)); },50); let pseudo=875+(idx%25)*7.2; updateFreqDisplay(pseudo); renderStationList(); let statusSpan=document.getElementById("radioStatus"); if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${st.name.substring(0,20)}`; localStorage.setItem("aetherwave_last_station", st.url_resolved); startQuoteRotation(st.name); refreshWordRotatorContent(); }
        function renderStationList(){ let cont=document.getElementById("stationListArea"); if(!cont) return; cont.innerHTML=''; stationsList.forEach((st,idx)=>{ let div=document.createElement("div"); div.className=`channel-item ${currentIdx===idx?'active':''}`; div.innerHTML=`<span>${(87+idx*0.45).toFixed(1)} MHz • ${st.name.substring(0,28)}</span>`; div.onclick=()=>selectStation(idx); cont.appendChild(div); }); }
        function bindPresetButton(btn, idx) { btn.addEventListener('click', (e) => { e.stopPropagation(); recallPreset(idx); }); btn.addEventListener('dblclick', (e) => { e.stopPropagation(); saveCurrentPreset(idx); }); }
        function recallPreset(i){ let url=presetUrls[i]; if(!url) { showMsg(`P${i+1} 无预设`); return; } radioPlayer.pause(); radioPlayer.src = url; radioPlayer.load(); radioPlayer.play().catch(err => console.warn("播放预设失败", err)); let matchedIdx = stationsList.findIndex(s => s.url_resolved === url); if(matchedIdx !== -1) { currentIdx = matchedIdx; renderStationList(); let statusSpan = document.getElementById("radioStatus"); if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${stationsList[matchedIdx].name.substring(0,20)}`; startQuoteRotation(stationsList[matchedIdx].name); let pseudo = 875 + (matchedIdx % 25) * 7.2; updateFreqDisplay(pseudo); localStorage.setItem("aetherwave_last_station", url); } else { currentIdx = -1; renderStationList(); let statusSpan = document.getElementById("radioStatus"); if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | 外部电台`; startQuoteRotation(null); } refreshWordRotatorContent(); }
        function saveCurrentPreset(i){ let currentUrl = radioPlayer.src; if(!currentUrl || currentUrl === "") { if(currentIdx !== -1 && stationsList[currentIdx]) { currentUrl = stationsList[currentIdx].url_resolved; } else { showMsg("请先选择或播放一个电台"); return; } } presetUrls[i] = currentUrl; localStorage.setItem("aetherwave_presets", JSON.stringify(presetUrls)); updatePresetUI(); showMsg(`已存入 P${i+1}`); }
        function updatePresetUI(){ document.querySelectorAll(".preset-btn").forEach((btn,i)=>{ let url=presetUrls[i]; let label=btn.querySelector(".preset-label"); if(url && url !== "") { let station = stationsList.find(s => s.url_resolved === url); if(station) { label.innerText = station.name.slice(0,4); btn.classList.add("saved"); } else { label.innerText = "★"; btn.classList.add("saved"); } } else { label.innerText = ""; btn.classList.remove("saved"); } }); }
        function applyVolume(){ if(!masterGain) return; if(isMuted){ masterGain.gain.value = 0; } else { let norm = (volumeRotation + 135) / 180; let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; if(isSurroundEnabled){ let merged = mergeEffects(stackedEffects); vol = vol * Math.pow(10, merged.gain / 20); } else { let preset = EFFECT_PRESETS[currentEffect]; vol = vol * Math.pow(10, (preset.gain || 0) / 20); } previousVolume = vol; masterGain.gain.value = vol; } }
        function toggleMute(){ isMuted = !isMuted; if(isMuted){ previousVolume = masterGain.gain.value; masterGain.gain.value = 0; } else { masterGain.gain.value = previousVolume; } updateMuteUI(); showMsg(isMuted ? "已静音" : "已取消静音"); refreshWordRotatorContent(); }
        function updateMuteUI(){ const headerBtn = document.getElementById('globalMuteBtn'); if(headerBtn) headerBtn.innerHTML = isMuted ? "🎤 开启" : "🔇 静音"; }
        function setVolumeFromKnob(deg){ volumeRotation = deg; if(!masterGain) return; if(!isMuted){ let norm = (volumeRotation + 135) / 180; let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; if(isSurroundEnabled){ let merged = mergeEffects(stackedEffects); vol = vol * Math.pow(10, merged.gain / 20); } else { let preset = EFFECT_PRESETS[currentEffect]; vol = vol * Math.pow(10, (preset.gain || 0) / 20); } masterGain.gain.value = vol; previousVolume = vol; } else { let norm = (volumeRotation + 135) / 180; let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; previousVolume = vol; } }
        function attachKnob(el, cb, minR, maxR, init) { let deg = init, drag = false, startY = 0, startDeg = 0; const mark = el.querySelector('.knob-mark'); if(mark) mark.style.transform = `rotate(${deg}deg)`; const upd = (d) => { deg = Math.min(maxR, Math.max(minR, d)); if(mark) mark.style.transform = `rotate(${deg}deg)`; if(cb) cb(deg); }; const onDown = (e) => { e.preventDefault(); drag = true; startY = e.clientY || (e.touches ? e.touches[0].clientY : 0); startDeg = deg; el.setPointerCapture(e.pointerId); }; const onMove = (e) => { if(!drag) return; e.preventDefault(); let nowY = e.clientY || (e.touches ? e.touches[0].clientY : 0); let delta = (startY - nowY) * 2; upd(startDeg + delta); }; const onUp = () => { drag = false; if(cb) cb(deg); }; el.addEventListener('pointerdown', onDown); window.addEventListener('pointermove', onMove); window.addEventListener('pointerup', onUp); }
        function startQuoteRotation(stationName=null){ let qDiv=document.getElementById("rollingQuote"); if(qDiv){ let msg=stationName?`🎧 收听 ${stationName.substring(0,26)} 🎧`:"✨ AETHERWAVE · 三维海浪环绕 ✨"; qDiv.innerText=msg; } }
        function refreshWordRotatorContent(){ let el=document.getElementById("wordRotator"); if(!el) return; let stationName = (currentIdx !== -1 && stationsList[currentIdx]) ? stationsList[currentIdx].name.substring(0, 18) : "未选择"; let effectName = isSurroundEnabled? (stackedEffects.length?stackedEffects.join('+'):"标准") : currentEffect; let surroundStatus = isSurroundEnabled ? "🌐 ON" : "⬜ OFF"; let hour = new Date().getHours(); let themeIdx = 0; let themeNames=["🌙 玄墨·夜阑","🌌 深靛·星沉","🌄 破晓·紫气","🌅 晨曦·鎏金","🍃 朝露·清欢","☀️ 曜日·煌煌","🌞 正午·炽白","🌇 午后·琥珀","🌤️ 夕照·熔岩","🌆 暮色·绛霞","🌠 夜澜·星河","🌚 子夜·霜天"]; let hourMap=[0,2,4,6,8,10,12,14,16,18,20,22]; for(let i=hourMap.length-1;i>=0;i--) if(hour>=hourMap[i]){ themeIdx=i; break; } el.innerText = `📻 ${stationName} · 🎛️ ${effectName} · ${surroundStatus} · ${themeNames[themeIdx]}`; }
        function startWordRotator(){ if(wordRotatorInterval) clearInterval(wordRotatorInterval); refreshWordRotatorContent(); wordRotatorInterval = setInterval(refreshWordRotatorContent, 3000); }
        function getSpectrumCardHTML(){ return `<div class="spectrum-card"><div class="quote-header"><span class="time-slot-title" id="slotTitle">☀️ 白昼疗愈</span><span class="radio-status" id="radioStatus">AETHERWAVE</span></div><div class="viz-wrapper"><canvas id="waveCanvas" width="700" height="180"></canvas><canvas id="spectrumCanvas" width="700" height="180"></canvas><div class="crt-overlay"></div></div><div class="quote-scroll-area"><div class="rolling-quote" id="rollingQuote">✨ 点击EQ选择ByteAudio完整音效 ✨</div></div><div class="eq-bands-panel"><div class="bands-title"><span>🎛️ ByteAudio专业EQ（10段）</span><span>libbyteaudio</span></div><div class="bands-grid" id="bandsGrid"></div></div></div>`; }
        function getStationListHTML(){ return `<div class="channel-section"><div class="section-title">📡 全球频谱 · 实时电台</div><div class="station-list" id="stationListArea"></div></div>`; }
        function getTripleControlCard(){ return `<div class="control-card"><div class="section-title"><span>🎮 控制面板</span><span>智能环绕多选</span></div><div class="control-deck"><div class="triple-control-header"><div class="triple-actions"><div class="action-btn" id="eqToggleBtn">🎛️ 音效<br><span class="eq-label" id="eqLabel">Original</span></div><div class="action-btn" id="surroundToggleBtn">🌀 环绕<br><span style="font-size:0.45rem;">OFF</span></div></div></div><div class="triple-preset-area"><div class="preset-row" id="presetRowTriple1"></div><div class="preset-row" id="presetRowTriple2"></div></div><div class="freq-row"><div class="freq-arrow" id="freqStepLeft">◀</div><span class="freq-num" id="frequencyValue">99.5</span><span class="freq-unit">MHz</span><div class="freq-arrow" id="freqStepRight">▶</div></div><div id="stackedEffectsContainer" class="stacked-container"></div></div></div>`; }
        function getDualControlCard(){ return `<div class="control-deck-compact"><div class="dual-control-layout"><div class="freq-group-dual"><div class="freq-arrow-mini" id="freqStepLeftDual">◀</div><span class="freq-num-mini" id="frequencyValueDual">99.5</span><div class="freq-arrow-mini" id="freqStepRightDual">▶</div></div><div class="right-control-group"><div class="preset-strip-dual" id="presetStripDual"></div><div class="dual-action-stack"><div class="action-btn" id="eqToggleBtnDual">🎛️ 音效<br><span class="eq-label" id="eqLabelDual">Original</span></div><div class="action-btn" id="surroundToggleBtnDual">🌀 环绕<br><span style="font-size:0.45rem;">OFF</span></div></div></div></div><div id="stackedEffectsContainerDual" class="stacked-container"></div></div>`; }
        function renderTripleLayout(){ layoutRoot.innerHTML = `<div class="triple-panel">${getStationListHTML()}${getSpectrumCardHTML()}${getTripleControlCard()}</div>`; }
        function renderDualLayout(){ layoutRoot.innerHTML = `<div class="dual-panel">${getStationListHTML()}<div class="spectrum-quote-panel"><div class="quote-header"><span class="time-slot-title" id="slotTitle">☀️ 白昼疗愈</span><span class="radio-status" id="radioStatus">AETHERWAVE</span></div><div class="viz-wrapper"><canvas id="waveCanvas" width="700" height="180"></canvas><canvas id="spectrumCanvas" width="700" height="180"></canvas><div class="crt-overlay"></div></div><div class="quote-scroll-area"><div class="rolling-quote" id="rollingQuote">✨ 点击EQ选择ByteAudio完整音效 ✨</div></div><div class="eq-bands-panel"><div class="bands-title"><span>🎛️ ByteAudio专业EQ（10段）</span><span>libbyteaudio</span></div><div class="bands-grid" id="bandsGrid"></div></div></div></div>${getDualControlCard()}</div>`; }
        function refreshLayout(){ if(currentLayoutMode==='triple') renderTripleLayout(); else renderDualLayout(); rebindAllEvents(); setTimeout(()=>window.dispatchEvent(new Event('resize')),50); }
        function setLayoutMode(mode, fromUser=false){ if(mode===currentLayoutMode) return; currentLayoutMode=mode; if(fromUser) autoLayout=false; refreshLayout(); updateGlobalSwitchButton(); }
        function handleOrientation(){ if(!autoLayout) return; let isLandscape=window.matchMedia("(orientation: landscape)").matches; if(isLandscape && currentLayoutMode!=='triple') setLayoutMode('triple', false); else if(!isLandscape && currentLayoutMode!=='dual') setLayoutMode('dual', false); }
        function onToggleLayout(){ setLayoutMode(currentLayoutMode==='triple'?'dual':'triple', true); }
        function updateGlobalSwitchButton(){ let btn = document.getElementById('globalLayoutSwitch'); if(btn) btn.innerText = currentLayoutMode==='triple'?'⟲ 双列':'⟲ 三列'; }
        function rebindAllEvents(){
            renderStationList();
            if(currentLayoutMode==='triple'){
                let eqBtn=document.getElementById('eqToggleBtn'); if(eqBtn) eqBtn.onclick=()=>{ renderEQModalMulti(); document.getElementById('eqModal').classList.add('active'); };
                let surroundBtn=document.getElementById('surroundToggleBtn'); if(surroundBtn) surroundBtn.onclick=()=>{ toggleSurroundMode(); };
                let leftArrow=document.getElementById('freqStepLeft'); if(leftArrow) leftArrow.onclick=()=>{ if(stationsList.length) prevStation(); };
                let rightArrow=document.getElementById('freqStepRight'); if(rightArrow) rightArrow.onclick=()=>{ if(stationsList.length) nextStation(); };
                let row1=document.getElementById('presetRowTriple1'); let row2=document.getElementById('presetRowTriple2');
                if(row1 && row2){ row1.innerHTML=''; row2.innerHTML=''; for(let i=0;i<6;i++){ let btn=document.createElement('button'); btn.className='preset-btn'; btn.innerHTML=`P${i+1}<span class="preset-label"></span>`; bindPresetButton(btn, i); row1.appendChild(btn); } for(let i=6;i<9;i++){ let btn=document.createElement('button'); btn.className='preset-btn'; btn.innerHTML=`P${i+1}<span class="preset-label"></span>`; bindPresetButton(btn, i); row2.appendChild(btn); } updatePresetUI(); }
            } else {
                let eqBtn=document.getElementById('eqToggleBtnDual'); if(eqBtn) eqBtn.onclick=()=>{ renderEQModalMulti(); document.getElementById('eqModal').classList.add('active'); };
                let surroundBtn=document.getElementById('surroundToggleBtnDual'); if(surroundBtn) surroundBtn.onclick=()=>{ toggleSurroundMode(); };
                let leftArrow=document.getElementById('freqStepLeftDual'); if(leftArrow) leftArrow.onclick=()=>{ if(stationsList.length) prevStation(); };
                let rightArrow=document.getElementById('freqStepRightDual'); if(rightArrow) rightArrow.onclick=()=>{ if(stationsList.length) nextStation(); };
                let strip=document.getElementById('presetStripDual'); if(strip){ strip.innerHTML=''; for(let i=0;i<9;i++){ let btn=document.createElement('button'); btn.className='preset-btn'; btn.innerHTML=`P${i+1}<span class="preset-label"></span>`; bindPresetButton(btn, i); strip.appendChild(btn); } updatePresetUI(); }
            }
            let closeModalBtn = document.getElementById('closeModal'); if(closeModalBtn) closeModalBtn.onclick = () => document.getElementById('eqModal').classList.remove('active');
            let eqModal = document.getElementById('eqModal'); if(eqModal) eqModal.onclick = (e) => { if(e.target === eqModal) eqModal.classList.remove('active'); };
            if(isSurroundEnabled) applyMergedSurround(); else applyEffectSingle();
            renderStackedChips();
        }
        async function fetchStations(country){ try{ let res=await fetch(`https://de1.api.radio-browser.info/json/stations/bycountry/${encodeURIComponent(country)}?limit=35&order=clickcount&reverse=true`); let data=await res.json(); stationsList=data.filter(s=>s.url_resolved && s.url_resolved.startsWith("http")).slice(0,35); renderStationList(); let last=localStorage.getItem("aetherwave_last_station"); let idx=last?stationsList.findIndex(s=>s.url_resolved===last):-1; if(idx!==-1) selectStation(idx); else if(stationsList.length) selectStation(0); updatePresetUI(); refreshWordRotatorContent(); } catch(e){ let area=document.getElementById("stationListArea"); if(area) area.innerHTML="<div style='padding:20px;'>📡 信号弱</div>"; } }
        function startVisuals(){ function draw(){ if(!isPowered||!analyser){ frameId=requestAnimationFrame(draw); return; } let wc=document.getElementById("waveCanvas"), sc=document.getElementById("spectrumCanvas"); if(!wc||!sc){ frameId=requestAnimationFrame(draw); return; } let w=wc.clientWidth, h=wc.clientHeight; if(w<=0||h<=0){ frameId=requestAnimationFrame(draw); return; } wc.width=w; sc.width=w; wc.height=h; sc.height=h; let wctx=wc.getContext("2d"), sctx=sc.getContext("2d"); let timeData=new Uint8Array(analyser.fftSize); let freqData=new Uint8Array(analyser.frequencyBinCount); analyser.getByteTimeDomainData(timeData); wctx.fillStyle="#010103"; wctx.fillRect(0,0,w,h); wctx.beginPath(); wctx.lineWidth=1.8; wctx.strokeStyle="#8effaa"; let step=w/timeData.length, x=0; for(let i=0;i<timeData.length;i+=2){ let v=timeData[i]/128.0; let y=v*h/1.4+h/3.5; if(i===0) wctx.moveTo(x,y); else wctx.lineTo(x,y); x+=step*2; } wctx.stroke(); analyser.getByteFrequencyData(freqData); sctx.clearRect(0,0,w,h); let bars=45, stepIdx=Math.floor(freqData.length/bars), barW=w/bars; for(let i=0;i<bars;i++){ let avg=0; for(let j=0;j<stepIdx;j++) avg+=freqData[i*stepIdx+j]||0; avg/=stepIdx; let barH=Math.min(h-4,(avg/220)*h*0.75); if(barH<2) barH=1; let grad=sctx.createLinearGradient(i*barW,h-barH,i*barW,h); grad.addColorStop(0,"#88ffaa"); grad.addColorStop(1,"#ffaa66"); sctx.fillStyle=grad; sctx.fillRect(i*barW,h-barH,barW-1,barH); } frameId=requestAnimationFrame(draw); } frameId=requestAnimationFrame(draw); }
        async function initAudioChain(){ if(audioCtx) return; audioCtx=new (window.AudioContext||window.webkitAudioContext)(); await audioCtx.resume(); radioPlayer.crossOrigin="anonymous"; let source=audioCtx.createMediaElementSource(radioPlayer); analyser=audioCtx.createAnalyser(); analyser.fftSize=1024; masterGain=audioCtx.createGain(); masterGain.gain.value=0.85; stereoPanner=audioCtx.createStereoPanner(); drcCompressor=audioCtx.createDynamicsCompressor(); drcCompressor.threshold.value=-100; drcCompressor.ratio.value=1; reverbDry=audioCtx.createGain(); reverbWet=audioCtx.createGain(); let sampleRate=audioCtx.sampleRate; let length=sampleRate*1.2; let impulse=audioCtx.createBuffer(2,length,sampleRate); let left=impulse.getChannelData(0),right=impulse.getChannelData(1); for(let i=0;i<length;i++){ let n=i/length, decay=Math.exp(-n*4.5); left[i]=(Math.random()-0.5)*decay*0.5; right[i]=(Math.random()-0.5)*decay*0.5; } reverbNode=audioCtx.createConvolver(); reverbNode.buffer=impulse; reverbDry.gain.value=1; reverbWet.gain.value=0; let freqs=[31,62,125,250,500,1000,2000,4000,8000,14000]; let prevNode=source; eqFilters=[]; for(let i=0;i<10;i++){ let f=audioCtx.createBiquadFilter(); f.type="peaking"; f.frequency.value=freqs[i]; f.Q.value=1; f.gain.value=0; prevNode.connect(f); eqFilters.push(f); prevNode=f; } prevNode.connect(stereoPanner); stereoPanner.connect(drcCompressor); drcCompressor.connect(reverbDry); drcCompressor.connect(reverbNode); reverbNode.connect(reverbWet); reverbDry.connect(analyser); reverbWet.connect(analyser); analyser.connect(masterGain); masterGain.connect(audioCtx.destination); if(isSurroundEnabled) applyMergedSurround(); else applyEffectSingle(); }
        function startMainApp(){
            let pre=localStorage.getItem("aetherwave_presets"); if(pre) try{ let arr=JSON.parse(pre); if(arr.length<9) arr=[...arr, ...new Array(9-arr.length).fill("")]; presetUrls=arr; }catch(e){}
            startQuoteRotation(); fetchStations(document.getElementById("countrySelect").value); startVisuals(); updatePresetUI(); currentLayoutMode='triple'; autoLayout=true; refreshLayout(); handleOrientation(); window.matchMedia("(orientation: landscape)").addEventListener('change',handleOrientation); setInterval(()=>{ let now=new Date(); document.getElementById("liveClock").innerText=now.toLocaleTimeString(); let hour=now.getHours(); let themeMap=[0,2,4,6,8,10,12,14,16,18,20,22]; let idx=0; for(let i=themeMap.length-1;i>=0;i--) if(hour>=themeMap[i]){ idx=i; break; } document.body.classList.remove(...themeMap.map(h=>`theme-${h}`)); document.body.classList.add(`theme-${themeMap[idx]}`); let slotSpan=document.getElementById("slotTitle"); if(slotSpan) slotSpan.innerHTML = ["🌙 玄墨·夜阑","🌌 深靛·星沉","🌄 破晓·紫气","🌅 晨曦·鎏金","🍃 朝露·清欢","☀️ 曜日·煌煌","🌞 正午·炽白","🌇 午后·琥珀","🌤️ 夕照·熔岩","🌆 暮色·绛霞","🌠 夜澜·星河","🌚 子夜·霜天"][idx]; }, 1000); startWordRotator(); let switchBtn = document.getElementById('globalLayoutSwitch'); if(switchBtn) switchBtn.onclick = onToggleLayout; let headerMuteBtn = document.getElementById('globalMuteBtn'); if(headerMuteBtn) headerMuteBtn.onclick = toggleMute; let volKnob = document.getElementById('volKnob'); if(volKnob) attachKnob(volKnob, (deg)=>{ setVolumeFromKnob(deg); }, -135, 45, -35); }
        function globalAudioActivator(){ if(audioCtx && audioCtx.state==='suspended') audioCtx.resume(); if(radioPlayer.paused && radioPlayer.src) radioPlayer.play().catch(()=>{}); }
        if(isLicensed){
            window.addEventListener('load',()=>{ startMainApp(); document.body.addEventListener('click',globalAudioActivator); document.body.addEventListener('touchstart',globalAudioActivator); initAudioChain().then(()=>{ if(radioPlayer.src && radioPlayer.paused) radioPlayer.play().catch(()=>{}); }); });
        }
        const layoutRoot = document.getElementById('layoutRoot');
    })();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"\n{'='*60}")
    print("  🎵 AETHERWAVE · 12色时辰电台")
    print("="*60)
    print(f"  🌐 访问地址: http://localhost:{port}")
    print("  📻 全球电台 · 三维海浪环绕")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
