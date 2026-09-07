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
        body {
            background: radial-gradient(circle at 30% 10%, #0a0a14, #010105);
            font-family: 'Share Tech Mono', 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            color: #aaccff;
        }
        .radio-chassis {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            background: rgba(10, 15, 31, 0.8);
            border-radius: 28px 28px 20px 20px;
            box-shadow: 0 30px 45px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.08);
            border: 1px solid rgba(80,80,110,0.4);
            overflow: hidden;
            backdrop-filter: blur(2px);
        }
        .glass-header {
            background: rgba(10, 20, 35, 0.7);
            backdrop-filter: blur(12px);
            padding: 8px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #2ecc71;
            flex-wrap: wrap;
            gap: 4px;
            cursor: pointer;
        }
        .glass-header:hover {
            background: rgba(20, 30, 50, 0.8);
        }
        .brand {
            color: #2ecc71;
            text-shadow: 0 0 5px #2ecc71;
            font-weight: bold;
            letter-spacing: 1px;
            font-size: 0.95rem;
            display: flex;
            align-items: baseline;
            gap: 8px;
            flex-wrap: wrap;
        }
        .word-rotator {
            font-size: 0.5rem;
            color: #ffdd99;
            background: #0a0a1288;
            padding: 2px 8px;
            border-radius: 30px;
            letter-spacing: 1px;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .brand .clock-panel {
            background: #000000aa;
            padding: 2px 10px;
            border-radius: 30px;
            font-family: monospace;
            font-size: 0.75rem;
            color: #00d2ff;
            box-shadow: inset 0 0 8px rgba(0,229,255,0.3);
            margin-left: 4px;
        }
        .header-right {
            display: flex;
            gap: 6px;
            align-items: center;
            flex-wrap: wrap;
            margin-left: auto;
        }
        .country-tuner {
            background: #0a0a12;
            border: 1px solid #4a4a5a;
            color: #f39c12;
            padding: 2px 8px;
            border-radius: 28px;
            font-family: monospace;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.55rem;
            transition: all 0.2s;
            background: #0a0a12;
        }
        .country-tuner:hover {
            background: #1a1a2a;
            border-color: #00d2ff;
            color: #00d2ff;
        }
        .country-tuner option {
            background: #1a1a2a;
            color: #aaccff;
        }
        .mute-header-btn {
            background: #0a0a12;
            border: 1px solid #4a4a5a;
            color: #f39c12;
            padding: 2px 8px;
            border-radius: 28px;
            font-family: monospace;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.55rem;
            transition: all 0.2s;
        }
        .mute-header-btn:hover {
            background: #1a1a2a;
            border-color: #00d2ff;
            color: #00d2ff;
        }
        .triple-panel {
            display: flex;
            gap: 10px;
            padding: 10px 10px 4px 10px;
            flex-wrap: wrap;
        }
        .triple-panel > * {
            flex: 1 1 0;
            min-width: 0;
        }
        .channel-section {
            background: #020208cc;
            border-radius: 20px;
            border: 1px solid #2f2f3e;
            backdrop-filter: blur(4px);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            max-height: 500px;
            min-height: 400px;
        }
        .spectrum-card {
            background: #000000;
            border-radius: 20px;
            border: 2px solid #2b2b3a;
            box-shadow: 0 0 16px rgba(0,255,122,0.18);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            max-height: 500px;
            min-height: 400px;
        }
        .control-card {
            background: #020208cc;
            border-radius: 20px;
            border: 1px solid #2f2f3e;
            backdrop-filter: blur(4px);
            overflow-y: auto;
            max-height: 500px;
            min-height: 400px;
            padding: 8px 10px;
        }
        .section-title {
            background: #0b0b14;
            padding: 5px 10px;
            font-size: 0.55rem;
            color: #88aadd;
            border-bottom: 1px solid #2a2a36;
            letter-spacing: 1px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .station-list {
            flex: 1;
            overflow-y: auto;
            padding: 4px 4px;
            min-height: 200px;
            max-height: 420px;
        }
        .station-list::-webkit-scrollbar {
            width: 3px;
        }
        .station-list::-webkit-scrollbar-track {
            background: #0a0a12;
            border-radius: 10px;
        }
        .station-list::-webkit-scrollbar-thumb {
            background: #2ecc71;
            border-radius: 10px;
        }
        .channel-item {
            padding: 4px 6px;
            margin: 2px 2px;
            background: #0b0b12;
            border-left: 3px solid #2c2c3c;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.55rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #aaccff;
            transition: all 0.2s;
        }
        .channel-item:hover {
            background: #141420;
        }
        .channel-item.active {
            background: linear-gradient(90deg, #1a2a1a, #0a120a);
            border-left-color: #2ecc71;
            color: #2ecc71;
            text-shadow: 0 0 3px #2ecc71;
        }
        .channel-item .play-icon {
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.45rem;
        }
        .channel-item.active .play-icon {
            opacity: 1;
            color: #2ecc71;
        }
        .quote-header {
            background: rgba(8, 8, 16, 0.85);
            padding: 4px 10px;
            border-bottom: 1px solid #2b2b3a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 4px;
            backdrop-filter: blur(4px);
            flex-shrink: 0;
        }
        .time-slot-title {
            color: #f39c12;
            text-shadow: 0 0 4px #f39c12;
            font-weight: bold;
            font-size: 0.55rem;
        }
        .radio-status {
            color: #aaffdd;
            font-family: monospace;
            font-size: 0.5rem;
            max-width: 180px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .viz-wrapper {
            position: relative;
            background: #010105;
            min-height: 120px;
            height: 120px;
            width: 100%;
            flex-shrink: 0;
            overflow: hidden;
        }
        .viz-wrapper canvas {
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            width: 100% !important;
            height: 120px !important;
        }
        #waveCanvas {
            z-index: 1;
        }
        #spectrumCanvas {
            z-index: 2;
            opacity: 0.92;
        }
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
            padding: 4px 10px;
            backdrop-filter: blur(8px);
            min-height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            flex-shrink: 0;
        }
        .rolling-quote {
            font-size: 0.6rem;
            color: #ccf6ff;
            text-shadow: 0 0 5px #0eaaff;
            text-align: center;
        }
        .eq-bands-panel {
            background: rgba(5,5,12,0.2);
            border-radius: 16px;
            margin: 4px 8px;
            padding: 4px 8px;
            border: 1px solid rgba(58,122,106,0.5);
            backdrop-filter: blur(4px);
            flex-shrink: 0;
        }
        .bands-title {
            display: flex;
            justify-content: space-between;
            font-size: 0.45rem;
            color: #bbffdd;
            margin-bottom: 2px;
        }
        .bands-grid {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 2px;
        }
        .band-item {
            flex: 1;
            min-width: 32px;
            text-align: center;
            background: #0c0c1a;
            border-radius: 16px;
            padding: 2px 2px;
            border-bottom: 2px solid #3a8a6a;
        }
        .band-freq { font-size: 0.4rem; color: #88aadd; }
        .band-gain { font-size: 0.55rem; font-weight:800; color:#ffffbb; }
        .control-deck {
            background: linear-gradient(145deg, #12121c, #0a0a10);
            border-radius: 24px 24px 20px 20px;
            padding: 8px 10px 10px;
            margin-top: 2px;
        }
        .triple-control-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
            padding: 0 2px;
        }
        .triple-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .triple-actions-right {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .preset-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 4px;
            margin-bottom: 4px;
        }
        .action-btn, .preset-btn {
            background: linear-gradient(145deg, #1c1c28, #0f0f18);
            border: 1px solid #3a3a4e;
            border-radius: 40px;
            font-family: monospace;
            font-weight: bold;
            font-size: 0.5rem;
            color: #7df9ff;
            text-shadow: 0 0 5px #00aaff;
            cursor: pointer;
            transition: 0.1s ease;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1px;
            width: 40px;
            padding: 2px 0;
            box-shadow: 0 2px 0 #030308;
        }
        .preset-btn {
            background: #1c1c28;
            color: #3a86ff;
            width: 38px;
            position: relative;
        }
        .preset-btn .click-badge {
            position: absolute;
            top: -4px;
            right: -4px;
            background: rgba(255,215,0,0.8);
            color: #000;
            border-radius: 50%;
            width: 14px;
            height: 14px;
            font-size: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .preset-btn .click-badge.show {
            opacity: 1;
        }
        .action-btn:active, .preset-btn:active {
            transform: translateY(2px);
            box-shadow: 0 0px 0 #030308;
        }
        .action-btn.surround-active {
            background: radial-gradient(ellipse at 30% 30%, #2a6f3a, #0f3a1a);
            border-color: #2ecc71;
            color: #2ecc71;
            text-shadow: 0 0 6px #0eff7a;
        }
        .preset-btn.saved {
            color: #f39c12;
            border-bottom: 2px solid #ff7032;
            background: linear-gradient(180deg, #1c1c28, #2a1f14);
        }
        .eq-label, .preset-label {
            font-size: 0.35rem;
            display: block;
            opacity: 0.8;
        }
        .freq-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #010108aa;
            border-radius: 40px;
            padding: 3px 12px;
            margin: 6px 0;
        }
        .freq-arrow {
            background: #1c1c2a;
            border: 1px solid #5a5a7a;
            border-radius: 40px;
            width: 32px;
            height: 32px;
            font-size: 1rem;
            font-weight: bold;
            color: #f39c12;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .freq-arrow:active { transform: scale(0.94); }
        .freq-num {
            font-size: 20px;
            font-family: 'Orbitron', monospace;
            color: #f39c12;
            font-weight: bold;
            min-width: 70px;
            text-align: center;
        }
        .freq-unit {
            font-size: 10px;
            color: #ccaaff;
            margin-left: 2px;
        }
        .stacked-container {
            background: #0a0a14cc;
            border-radius: 16px;
            padding: 4px 8px;
            margin-top: 6px;
            backdrop-filter: blur(4px);
            min-height: 28px;
        }
        .stacked-title { font-size:0.45rem; color:#00d2ff; margin-bottom:2px; }
        .stacked-chips { display:flex; flex-wrap:wrap; gap:3px; }
        .stack-chip {
            background:#2a2a3a; border-radius:20px; padding:1px 6px; font-size:0.45rem;
            display:inline-flex; align-items:center; gap:3px; color:#bbffdd;
            border-left:2px solid #2ecc71; cursor:pointer;
        }
        .stack-chip .remove-stack { color:#ff8866; font-weight:bold; cursor:pointer; font-size:0.6rem; }
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
            background:rgba(20,20,35,0.6); margin:4px 0; padding:6px 12px;
            border-radius:40px; cursor:pointer; font-size:0.65rem;
            display:flex; align-items:center; gap:8px; color:#ccddff;
            border:1px solid rgba(51,68,85,0.5);
        }
        .modal-item.selected { background:rgba(42,106,58,0.6); border-left:4px solid #2ecc71; }
        .modal-item.multi-selected { background:#2a4a3a; border-left:4px solid #ffaa33; }
        .badge-icon { font-size:0.45rem; background:#ffaa33; color:#000; border-radius:20px; padding:1px 5px; margin-left:4px; }
        .close-modal { text-align:center; margin-top:12px; padding:6px; cursor:pointer; font-size:0.6rem; border-top:1px solid #334455; color:#ff5555; }
        .toast {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.85);
            color: #fff;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.7rem;
            z-index: 999;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
            border: 1px solid rgba(255,215,0,0.2);
        }
        .toast.show { opacity: 1; }
        @media (max-width:900px) {
            .triple-panel { flex-direction: column; }
            .triple-panel > * { flex: none; width: 100%; }
            .channel-section, .spectrum-card, .control-card { max-height: 350px; min-height: 200px; }
            .station-list { max-height: 200px; min-height: 120px; }
            .viz-wrapper { height: 100px; min-height: 100px; }
            .viz-wrapper canvas { height: 100px !important; }
        }
        @media (max-width:480px) {
            .channel-section, .spectrum-card, .control-card { max-height: 300px; min-height: 160px; }
            .station-list { max-height: 150px; min-height: 100px; }
            .viz-wrapper { height: 80px; min-height: 80px; }
            .viz-wrapper canvas { height: 80px !important; }
            .channel-item { font-size: 0.45rem; padding: 3px 4px; }
            .brand { font-size: 0.7rem; }
            .glass-header { padding: 6px 10px; }
            .freq-num { font-size: 16px; min-width: 50px; }
            .action-btn, .preset-btn { width: 32px; font-size: 0.4rem; }
            .word-rotator { font-size: 0.4rem; max-width: 120px; }
            .brand .clock-panel { font-size: 0.6rem; padding: 1px 6px; }
            .country-tuner { font-size: 0.45rem; padding: 1px 4px; max-width: 60px; }
            .mute-header-btn { font-size: 0.45rem; padding: 1px 4px; }
        }
    </style>
</head>
<body>

<!-- Toast -->
<div class="toast" id="toast"></div>

<div id="radioApp" style="opacity:1;">
    <div class="radio-chassis">
        <div class="glass-header" onclick="location.href='/'">
            <div class="brand">
                ◢ AETHERWAVE 
                <span class="word-rotator" id="wordRotator">--</span>
                <span class="clock-panel" id="liveClock">--:--:--</span>
            </div>
            <div class="header-right">
                <select id="countrySelect" class="country-tuner" onclick="event.stopPropagation();">
                    <option value="China">🇨🇳 中国</option>
                    <option value="United States">🇺🇸 美国</option>
                    <option value="Japan">🇯🇵 日本</option>
                    <option value="United Kingdom">🇬🇧 英国</option>
                    <option value="Germany">🇩🇪 德国</option>
                    <option value="France">🇫🇷 法国</option>
                </select>
                <button id="globalMuteBtn" class="mute-header-btn" onclick="event.stopPropagation();">🔇 静音</button>
            </div>
        </div>
        <div id="layoutRoot"></div>
    </div>
</div>
<div id="eqModal" class="modal">
    <div class="modal-content">
        <h3>🎛️ 智能环绕音效库 · 点击多选叠加</h3>
        <div style="font-size:0.6rem;color:#888;margin:4px 0 8px;">最多叠加 3 个音效</div>
        <div id="presetList"></div>
        <div class="close-modal" id="closeModal">✖ 关闭</div>
    </div>
</div>

<script>
    (function(){
        let isPowered=true, currentIdx=-1;
        let stationsList=[];
        let presetUrls=new Array(9).fill("");
        let audioCtx=null, radioPlayer=new Audio(), analyser=null, masterGain=null, drcCompressor=null, stereoPanner=null, reverbNode=null, reverbDry=null, reverbWet=null;
        let eqFilters=[];
        let currentEffect="Original";
        let volumeRotation=-35;
        let fineOffset=0;
        let frameId=null;
        let isSurroundEnabled=false;
        let stackedEffects=[];
        let isMuted = false;
        let previousVolume = 0.85;
        let wordRotatorInterval = null;
        let visualActive = false;

        let panner3D = null;
        let surroundAnimationId = null;
        
        // ========== Toast ==========
        function showToast(msg) {
            const el = document.getElementById('toast');
            el.textContent = msg;
            el.classList.add('show');
            clearTimeout(el._timer);
            el._timer = setTimeout(() => el.classList.remove('show'), 1500);
        }
        
        // ========== 预设按钮点击计数器 ==========
        let presetClickCounts = {};
        let presetClickTimers = {};

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

        const EFFECT_PRESETS = { 
            "Original":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0,reverb:0,gain:0},
            "headset":{eq:[2,1,0,2,3,2,1,0,0,0],drc:false,stereo:0,reverb:0,gain:0},
            "headset2":{eq:[12,10,8,3,0,-2,-3,-2,0,0],drc:false,stereo:0,reverb:0,gain:0},
            "headset3":{eq:[8,6,4,-2,-4,-6,-4,-2,0,2],drc:false,stereo:0,reverb:0,gain:0},
            "speaker":{eq:[-12,-12,-6,-3,0,2,3,4,3,2],drc:false,stereo:0,reverb:0,gain:0},
            "voice_clean":{eq:[-6,-4,-2,-1,2,5,3,1,0,-1],drc:false,stereo:0,reverb:0,gain:5},
            "bass_enhance":{eq:[10,8,6,2,0,-1,-2,-1,0,0],drc:false,stereo:0,reverb:0,gain:0},
            "stereo_enhance":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0.8,reverb:0,gain:0},
            "360_all":{eq:[0,0,0,0,0,0,0,0,0,0],drc:false,stereo:0.5,reverb:0.25,gain:0},
            "hifi_live":{eq:[0,0,1,2,2,3,3,2,1,0],drc:false,stereo:0.2,reverb:0.3,gain:0},
            "vibrant_electronic":{eq:[4,3,2,1,0,0,2,4,5,4],drc:false,stereo:0.3,reverb:0.28,gain:10},
            "vinyl":{eq:[-8,-6,-4,-2,0,2,1,0,-2,-4],drc:false,stereo:0,reverb:0.15,gain:2},
            "rock":{eq:[8,6,4,2,0,1,2,4,6,8],drc:false,stereo:0,reverb:0,gain:0},
            "intelligent":{eq:[3,2,1,0,0,1,2,3,4,3],drc:true,stereo:0.15,reverb:0.1,gain:0},
            "🌊 三维海浪环绕":{eq:[1,1,1,0,0,1,2,3,3,2],drc:false,stereo:0.2,reverb:0.15,gain:0} 
        };
        const EFFECT_NAMES = Object.keys(EFFECT_PRESETS);
        const FREQ_BANDS = ["31Hz","62Hz","125Hz","250Hz","500Hz","1kHz","2kHz","4kHz","8kHz","14kHz"];

        function mergeEffects(effectsList) { 
            if(!effectsList.length) return EFFECT_PRESETS["Original"]; 
            let sumEq=new Array(10).fill(0), drcFlag=false, stereoSum=0, reverbMax=0, gainSum=0; 
            for(let name of effectsList){ 
                let p=EFFECT_PRESETS[name]; 
                if(!p) continue; 
                for(let i=0;i<10;i++) sumEq[i]+=p.eq[i]; 
                if(p.drc) drcFlag=true; 
                stereoSum+=p.stereo; 
                if(p.reverb>reverbMax) reverbMax=p.reverb; 
                gainSum+=p.gain; 
            } 
            let count=effectsList.length; 
            for(let i=0;i<10;i++) sumEq[i]=Math.min(20,Math.max(-20,sumEq[i])); 
            return { eq:sumEq, drc:drcFlag, stereo:stereoSum/count, reverb:reverbMax, gain:gainSum }; 
        }
        
        function applyMergedSurround(){ 
            if(!eqFilters.length) return; 
            let merged=mergeEffects(stackedEffects); 
            for(let i=0;i<10;i++) eqFilters[i].gain.value=merged.eq[i]; 
            if(stereoPanner) stereoPanner.pan.value=merged.stereo; 
            if(drcCompressor){ 
                if(merged.drc) { drcCompressor.threshold.value=-16.8; drcCompressor.ratio.value=3.15; } 
                else { drcCompressor.threshold.value=-100; drcCompressor.ratio.value=1; } 
            } 
            if(reverbWet && reverbDry){ 
                reverbWet.gain.value=merged.reverb*0.5; 
                reverbDry.gain.value=1-merged.reverb*0.3; 
            } 
            if(masterGain){ applyVolume(); } 
            renderBandsUIWithEq(merged.eq); 
            updateEqLabelSurround(); 
            refreshWordRotatorContent(); 
        }
        
        function renderBandsUIWithEq(eqVals){ 
            let container=document.getElementById("bandsGrid"); 
            if(!container) return; 
            container.innerHTML=""; 
            for(let i=0;i<FREQ_BANDS.length;i++){ 
                let val=eqVals[i]; 
                let bandDiv=document.createElement("div"); 
                bandDiv.className="band-item"; 
                bandDiv.innerHTML=`<div class="band-freq">${FREQ_BANDS[i]}</div><div class="band-gain">${val>0?'+'+val:val}</div>`; 
                container.appendChild(bandDiv); 
            } 
        }
        
        function updateEqLabelSurround(){ 
            let lab=document.getElementById("eqLabel"); 
            if(lab) lab.innerText=isSurroundEnabled?`环绕+${stackedEffects.length}`:currentEffect; 
        }
        
        function renderStackedChips(){ 
            let container = document.getElementById('stackedEffectsContainer'); 
            if(!container) return; 
            if(!isSurroundEnabled || stackedEffects.length===0){ 
                container.innerHTML=`<div class="stacked-title">🌀 智能环绕未激活</div>`; 
                return; 
            } 
            let html=`<div class="stacked-title">🔊 已叠加 (${stackedEffects.length}/3)</div><div class="stacked-chips">`; 
            stackedEffects.forEach(eff=>{ 
                html+=`<div class="stack-chip" data-effect="${eff}">${eff} <span class="remove-stack" data-effect="${eff}">✖</span></div>`; 
            }); 
            html+=`</div>`; 
            container.innerHTML=html; 
            document.querySelectorAll(".remove-stack").forEach(el=>{ 
                el.addEventListener("click",(e)=>{ 
                    e.stopPropagation(); 
                    let name=el.getAttribute("data-effect"); 
                    if(name){ 
                        let idx=stackedEffects.indexOf(name); 
                        if(idx!==-1) stackedEffects.splice(idx,1); 
                        if(stackedEffects.length===0) applyMergedSurround(); 
                        else applyMergedSurround(); 
                        renderStackedChips(); 
                        if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti(); 
                        refreshWordRotatorContent(); 
                    } 
                }); 
            }); 
        }
        
        function toggleSurroundMode(){
            isSurroundEnabled = !isSurroundEnabled;
            if(isSurroundEnabled){
                // 默认添加三维海浪环绕
                if(!stackedEffects.includes("🌊 三维海浪环绕")) {
                    stackedEffects.push("🌊 三维海浪环绕");
                }
                // 如果当前有效果且不是Original，也加上
                if(!stackedEffects.includes(currentEffect) && currentEffect!=="Original") {
                    stackedEffects.push(currentEffect);
                }
                applyMergedSurround();
                start3DSurround();
            } else {
                // 关闭环绕时，保留最后一个音效作为当前
                let lastSingle=stackedEffects.length>0?stackedEffects[stackedEffects.length-1]:currentEffect;
                // 如果是三维海浪环绕，换成Original
                if(lastSingle === "🌊 三维海浪环绕") lastSingle = "Original";
                currentEffect=lastSingle;
                applyEffectSingle();
                stackedEffects=[];
                stopSurround();
            }
            let toggleBtn=document.getElementById('surroundToggleBtn');
            if(toggleBtn) toggleBtn.classList.toggle('surround-active',isSurroundEnabled);
            let span=toggleBtn?.querySelector('span');
            if(span) span.innerText=isSurroundEnabled?'ON':'OFF';
            renderStackedChips();
            updateEqLabelSurround();
            if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti();
            refreshWordRotatorContent();
            showToast(isSurroundEnabled ? '🌊 环绕已开启 (三维海浪)' : '环绕已关闭');
        }

        function applyEffectSingle(){ 
            if(!eqFilters.length) return; 
            let preset=EFFECT_PRESETS[currentEffect]; 
            for(let i=0;i<10;i++) eqFilters[i].gain.value=preset.eq[i]; 
            if(stereoPanner) stereoPanner.pan.value=preset.stereo||0; 
            if(drcCompressor){ 
                if(preset.drc) { drcCompressor.threshold.value=-16.8; drcCompressor.ratio.value=3.15; } 
                else { drcCompressor.threshold.value=-100; drcCompressor.ratio.value=1; } 
            } 
            if(reverbWet && reverbDry){ 
                reverbWet.gain.value=(preset.reverb||0)*0.5; 
                reverbDry.gain.value=1-(preset.reverb||0)*0.3; 
            } 
            if(masterGain){ applyVolume(); } 
            renderBandsUIWithEq(preset.eq); 
            updateEqLabelSurround(); 
            refreshWordRotatorContent(); 
        }
        
        function setEffect(effectName){ 
            if(isSurroundEnabled){ 
                if(stackedEffects.includes(effectName)){ 
                    let idx=stackedEffects.indexOf(effectName); 
                    stackedEffects.splice(idx,1); 
                    if(stackedEffects.length===0) applyMergedSurround(); 
                    else applyMergedSurround(); 
                } else { 
                    if(stackedEffects.length >= 3) {
                        showToast('⚠️ 最多叠加 3 个音效');
                        return;
                    }
                    stackedEffects.push(effectName); 
                    applyMergedSurround(); 
                } 
                renderStackedChips(); 
                if(document.getElementById("eqModal").classList.contains("active")) renderEQModalMulti(); 
            } else { 
                if(currentEffect===effectName) return; 
                currentEffect=effectName; 
                applyEffectSingle(); 
                showToast(`音效: ${effectName}`); 
            } 
            refreshWordRotatorContent(); 
        }
        
        function renderEQModalMulti(){ 
            let listDiv=document.getElementById("presetList"); 
            if(!listDiv) return; 
            listDiv.innerHTML=""; 
            EFFECT_NAMES.forEach(name=>{ 
                let item=document.createElement("div"); 
                let isSelected=isSurroundEnabled?stackedEffects.includes(name):(currentEffect===name); 
                item.className=`modal-item ${isSelected?(isSurroundEnabled?"multi-selected":"selected"):""}`; 
                let preset=EFFECT_PRESETS[name]; 
                let badge=""; 
                if(preset.drc) badge='<span class="badge-icon">DRC</span>'; 
                else if(preset.reverb>0) badge='<span class="badge-icon">RVB</span>'; 
                else if(preset.stereo>0) badge='<span class="badge-icon">STEREO</span>'; 
                let full = isSurroundEnabled && stackedEffects.length >= 3 && !isSelected ? ' style="opacity:0.4;"' : '';
                let fullText = isSurroundEnabled && stackedEffects.length >= 3 && !isSelected ? ' <span style="font-size:0.4rem;color:#ff6633;">(已满)</span>' : '';
                item.innerHTML=`<span class="sound-icon">🎵</span><span>${name}</span>${badge}${fullText}`; 
                item.setAttribute('data-name', name); 
                item.onclick=()=>{ setEffect(name); renderEQModalMulti(); }; 
                listDiv.appendChild(item); 
            }); 
        }
        
        function showMsg(m){ 
            let st=document.getElementById("radioStatus"); 
            if(st){ 
                st.innerHTML=`📢 ${m}`; 
                setTimeout(()=>{ 
                    if(stationsList[currentIdx] && !radioPlayer.paused) 
                        st.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${stationsList[currentIdx]?.name?.substring(0,18)}`; 
                    else if(stationsList[currentIdx]) 
                        st.innerHTML=stationsList[currentIdx]?.name?.substring(0,20); 
                    else st.innerHTML="AETHERWAVE"; 
                },2000); 
            } 
        }
        
        function updateFreqDisplay(raw){ 
            let base=raw/10; 
            let final=base+fineOffset; 
            final=Math.min(108,Math.max(87,final)); 
            let spanTriple=document.getElementById("frequencyValue"); 
            if(spanTriple) spanTriple.innerText=final.toFixed(1); 
        }
        
        function prevStation(){ 
            if(!stationsList.length) return; 
            let newIdx=currentIdx-1; 
            if(newIdx<0) newIdx=stationsList.length-1; 
            selectStation(newIdx); 
        }
        
        function nextStation(){ 
            if(!stationsList.length) return; 
            let newIdx=currentIdx+1; 
            if(newIdx>=stationsList.length) newIdx=0; 
            selectStation(newIdx); 
        }
        
        function selectStation(idx){ 
            if(!stationsList[idx]) return; 
            currentIdx=idx; 
            let st=stationsList[idx]; 
            radioPlayer.pause(); 
            radioPlayer.src=''; 
            setTimeout(()=>{ 
                radioPlayer.src=st.url_resolved; 
                radioPlayer.load(); 
                radioPlayer.play().catch(err=>console.warn("播放失败",err)); 
            },50); 
            let pseudo=875+(idx%25)*7.2; 
            updateFreqDisplay(pseudo); 
            renderStationList(); 
            let statusSpan=document.getElementById("radioStatus"); 
            if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${st.name.substring(0,20)}`; 
            localStorage.setItem("aetherwave_last_station", st.url_resolved); 
            startQuoteRotation(st.name); 
            refreshWordRotatorContent(); 
        }
        
        function renderStationList(){ 
            let cont=document.getElementById("stationListArea"); 
            if(!cont) return; 
            cont.innerHTML=''; 
            stationsList.forEach((st,idx)=>{ 
                let div=document.createElement("div"); 
                div.className=`channel-item ${currentIdx===idx?'active':''}`; 
                div.innerHTML=`<span>${(87+idx*0.45).toFixed(1)} MHz • ${st.name.substring(0,28)}</span><span class="play-icon">▶</span>`; 
                div.onclick=()=>selectStation(idx); 
                cont.appendChild(div); 
            }); 
        }
        
        // ========== 预设按钮 - 单击播放(无提示), 双击保存, 三击清除 ==========
        function bindPresetButton(btn, idx) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (!presetClickCounts[idx]) presetClickCounts[idx] = 0;
                presetClickCounts[idx]++;
                
                let badge = btn.querySelector('.click-badge');
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'click-badge';
                    btn.appendChild(badge);
                }
                badge.textContent = presetClickCounts[idx];
                badge.classList.add('show');
                
                clearTimeout(presetClickTimers[idx]);
                presetClickTimers[idx] = setTimeout(() => {
                    const count = presetClickCounts[idx];
                    if (count === 1) {
                        // 单击：播放 - 无Toast提示
                        recallPreset(idx, false);
                        badge.classList.remove('show');
                    } else if (count === 2) {
                        // 双击：保存
                        saveCurrentPreset(idx);
                        badge.classList.remove('show');
                    } else if (count >= 3) {
                        // 三击：清除
                        clearPreset(idx);
                        badge.classList.remove('show');
                    }
                    presetClickCounts[idx] = 0;
                }, 500);
            });
            
            btn.addEventListener('dblclick', (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        }
        
        function recallPreset(i, showToastMsg=true){ 
            let url=presetUrls[i]; 
            if(!url) { 
                if(showToastMsg) showToast(`P${i+1} 无预设，双击保存`);
                return; 
            } 
            radioPlayer.pause(); 
            radioPlayer.src = url; 
            radioPlayer.load(); 
            radioPlayer.play().catch(err => console.warn("播放预设失败", err)); 
            let matchedIdx = stationsList.findIndex(s => s.url_resolved === url); 
            if(matchedIdx !== -1) { 
                currentIdx = matchedIdx; 
                renderStationList(); 
                let statusSpan = document.getElementById("radioStatus"); 
                if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | ${stationsList[matchedIdx].name.substring(0,20)}`; 
                startQuoteRotation(stationsList[matchedIdx].name); 
                let pseudo = 875 + (matchedIdx % 25) * 7.2; 
                updateFreqDisplay(pseudo); 
                localStorage.setItem("aetherwave_last_station", url); 
            } else { 
                currentIdx = -1; 
                renderStationList(); 
                let statusSpan = document.getElementById("radioStatus"); 
                if(statusSpan) statusSpan.innerHTML=`🎛️ ${isSurroundEnabled?'环绕':currentEffect} | 外部电台`; 
                startQuoteRotation(null); 
            } 
            refreshWordRotatorContent(); 
            // 单击不显示Toast，静默换台
        }
        
        function saveCurrentPreset(i){ 
            let currentUrl = radioPlayer.src; 
            if(!currentUrl || currentUrl === "") { 
                if(currentIdx !== -1 && stationsList[currentIdx]) { 
                    currentUrl = stationsList[currentIdx].url_resolved; 
                } else { 
                    showToast("请先选择或播放一个电台"); 
                    return; 
                } 
            } 
            if(presetUrls[i] === currentUrl) {
                showToast(`P${i+1} 已保存，无需重复`);
                return;
            }
            presetUrls[i] = currentUrl; 
            localStorage.setItem("aetherwave_presets", JSON.stringify(presetUrls)); 
            updatePresetUI(); 
            showToast(`✅ 已存入 P${i+1}`); 
        }
        
        function clearPreset(i){
            if(!presetUrls[i]) {
                showToast(`P${i+1} 已是空`);
                return;
            }
            presetUrls[i] = "";
            localStorage.setItem("aetherwave_presets", JSON.stringify(presetUrls));
            updatePresetUI();
            showToast(`🗑️ P${i+1} 已清除`);
        }
        
        function updatePresetUI(){ 
            document.querySelectorAll(".preset-btn").forEach((btn,i)=>{ 
                let url=presetUrls[i]; 
                let label=btn.querySelector(".preset-label"); 
                if(url && url !== "") { 
                    let station = stationsList.find(s => s.url_resolved === url); 
                    if(station) { 
                        label.innerText = station.name.slice(0,4); 
                        btn.classList.add("saved"); 
                    } else { 
                        label.innerText = "★"; 
                        btn.classList.add("saved"); 
                    } 
                } else { 
                    label.innerText = ""; 
                    btn.classList.remove("saved"); 
                } 
            }); 
        }
        
        function applyVolume(){ 
            if(!masterGain) return; 
            if(isMuted){ masterGain.gain.value = 0; } 
            else { 
                let norm = (volumeRotation + 135) / 180; 
                let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; 
                if(isSurroundEnabled){ 
                    let merged = mergeEffects(stackedEffects); 
                    vol = vol * Math.pow(10, merged.gain / 20); 
                } else { 
                    let preset = EFFECT_PRESETS[currentEffect]; 
                    vol = vol * Math.pow(10, (preset.gain || 0) / 20); 
                } 
                previousVolume = vol; 
                masterGain.gain.value = vol; 
            } 
        }
        
        function toggleMute(){ 
            isMuted = !isMuted; 
            if(isMuted){ 
                previousVolume = masterGain.gain.value; 
                masterGain.gain.value = 0; 
            } else { 
                masterGain.gain.value = previousVolume; 
            } 
            updateMuteUI(); 
            showToast(isMuted ? "🔇 已静音" : "🔊 已取消静音"); 
            refreshWordRotatorContent(); 
        }
        
        function updateMuteUI(){ 
            const headerBtn = document.getElementById('globalMuteBtn'); 
            if(headerBtn) headerBtn.innerHTML = isMuted ? "🎤 开启" : "🔇 静音"; 
        }
        
        function setVolumeFromKnob(deg){ 
            volumeRotation = deg; 
            if(!masterGain) return; 
            if(!isMuted){ 
                let norm = (volumeRotation + 135) / 180; 
                let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; 
                if(isSurroundEnabled){ 
                    let merged = mergeEffects(stackedEffects); 
                    vol = vol * Math.pow(10, merged.gain / 20); 
                } else { 
                    let preset = EFFECT_PRESETS[currentEffect]; 
                    vol = vol * Math.pow(10, (preset.gain || 0) / 20); 
                } 
                masterGain.gain.value = vol; 
                previousVolume = vol; 
            } else { 
                let norm = (volumeRotation + 135) / 180; 
                let vol = Math.min(1.2, Math.max(0, norm)) * 0.85; 
                previousVolume = vol; 
            } 
        }
        
        function startQuoteRotation(stationName=null){ 
            let qDiv=document.getElementById("rollingQuote"); 
            if(qDiv){ 
                let msg=stationName?`🎧 收听 ${stationName.substring(0,26)} 🎧`:"✨ AETHERWAVE · 三维海浪环绕 ✨"; 
                qDiv.innerText=msg; 
            } 
        }
        
        function refreshWordRotatorContent(){ 
            let el=document.getElementById("wordRotator"); 
            if(!el) return; 
            let stationName = (currentIdx !== -1 && stationsList[currentIdx]) ? stationsList[currentIdx].name.substring(0, 18) : "未选择"; 
            let effectName = isSurroundEnabled? (stackedEffects.length?stackedEffects.join('+'):"标准") : currentEffect; 
            let surroundStatus = isSurroundEnabled ? "🌐 ON" : "⬜ OFF"; 
            let hour = new Date().getHours(); 
            let themeIdx = 0; 
            let themeNames=["🌙 玄墨·夜阑","🌌 深靛·星沉","🌄 破晓·紫气","🌅 晨曦·鎏金","🍃 朝露·清欢","☀️ 曜日·煌煌","🌞 正午·炽白","🌇 午后·琥珀","🌤️ 夕照·熔岩","🌆 暮色·绛霞","🌠 夜澜·星河","🌚 子夜·霜天"]; 
            let hourMap=[0,2,4,6,8,10,12,14,16,18,20,22]; 
            for(let i=hourMap.length-1;i>=0;i--) if(hour>=hourMap[i]){ themeIdx=i; break; } 
            el.innerText = `📻 ${stationName} · 🎛️ ${effectName} · ${surroundStatus} · ${themeNames[themeIdx]}`; 
        }
        
        function startWordRotator(){ 
            if(wordRotatorInterval) clearInterval(wordRotatorInterval); 
            refreshWordRotatorContent(); 
            wordRotatorInterval = setInterval(refreshWordRotatorContent, 3000); 
        }
        
        function getSpectrumCardHTML(){ 
            return `<div class="spectrum-card"><div class="quote-header"><span class="time-slot-title" id="slotTitle">☀️ 白昼疗愈</span><span class="radio-status" id="radioStatus">AETHERWAVE</span></div><div class="viz-wrapper"><canvas id="waveCanvas"></canvas><canvas id="spectrumCanvas"></canvas><div class="crt-overlay"></div></div><div class="quote-scroll-area"><div class="rolling-quote" id="rollingQuote">✨ 点击EQ选择ByteAudio完整音效 ✨</div></div><div class="eq-bands-panel"><div class="bands-title"><span>🎛️ ByteAudio专业EQ（10段）</span><span>libbyteaudio</span></div><div class="bands-grid" id="bandsGrid"></div></div></div>`; 
        }
        
        function getStationListHTML(){ 
            return `<div class="channel-section"><div class="section-title">📡 全球频谱 · 实时电台</div><div class="station-list" id="stationListArea"></div></div>`; 
        }
        
        function getControlCardHTML(){ 
            return `<div class="control-card"><div class="section-title"><span>🎮 控制面板</span><span>智能环绕多选</span></div><div class="control-deck"><div class="triple-control-header"><div class="triple-actions"><div class="action-btn" id="eqToggleBtn">🎛️ 音效<br><span class="eq-label" id="eqLabel">Original</span></div></div><div class="triple-actions-right"><div class="action-btn" id="surroundToggleBtn">🌀 环绕<br><span style="font-size:0.45rem;">OFF</span></div></div></div><div class="triple-preset-area"><div class="preset-row" id="presetRowTriple1"></div><div class="preset-row" id="presetRowTriple2"></div></div><div class="freq-row"><div class="freq-arrow" id="freqStepLeft">◀</div><span class="freq-num" id="frequencyValue">99.5</span><span class="freq-unit">MHz</span><div class="freq-arrow" id="freqStepRight">▶</div></div><div id="stackedEffectsContainer" class="stacked-container"></div></div></div>`; 
        }
        
        function renderLayout(){ 
            layoutRoot.innerHTML = `<div class="triple-panel">${getStationListHTML()}${getSpectrumCardHTML()}${getControlCardHTML()}</div>`; 
            rebindAllEvents(); 
            setTimeout(()=>{
                initCanvasSize();
                if(!visualActive){
                    visualActive = true;
                    startVisuals();
                }
            }, 150);
        }
        
        function initCanvasSize(){
            let wc = document.getElementById('waveCanvas');
            let sc = document.getElementById('spectrumCanvas');
            if(!wc || !sc) return;
            let parent = wc.parentElement;
            if(!parent) return;
            let rect = parent.getBoundingClientRect();
            let w = rect.width || 700;
            let h = rect.height || 120;
            if(w > 0 && h > 0){
                wc.width = w;
                wc.height = h;
                sc.width = w;
                sc.height = h;
                wc.style.width = w + 'px';
                wc.style.height = h + 'px';
                sc.style.width = w + 'px';
                sc.style.height = h + 'px';
            }
        }
        
        function rebindAllEvents(){
            renderStationList();
            let eqBtn=document.getElementById('eqToggleBtn'); 
            if(eqBtn) eqBtn.onclick=()=>{ renderEQModalMulti(); document.getElementById('eqModal').classList.add('active'); };
            let surroundBtn=document.getElementById('surroundToggleBtn'); 
            if(surroundBtn) surroundBtn.onclick=()=>{ toggleSurroundMode(); };
            let leftArrow=document.getElementById('freqStepLeft'); 
            if(leftArrow) leftArrow.onclick=()=>{ if(stationsList.length) prevStation(); };
            let rightArrow=document.getElementById('freqStepRight'); 
            if(rightArrow) rightArrow.onclick=()=>{ if(stationsList.length) nextStation(); };
            let row1=document.getElementById('presetRowTriple1'); 
            let row2=document.getElementById('presetRowTriple2');
            if(row1 && row2){ 
                row1.innerHTML=''; 
                row2.innerHTML=''; 
                for(let i=0;i<6;i++){ 
                    let btn=document.createElement('button'); 
                    btn.className='preset-btn'; 
                    btn.innerHTML=`P${i+1}<span class="preset-label"></span><span class="click-badge"></span>`; 
                    bindPresetButton(btn, i); 
                    row1.appendChild(btn); 
                } 
                for(let i=6;i<9;i++){ 
                    let btn=document.createElement('button'); 
                    btn.className='preset-btn'; 
                    btn.innerHTML=`P${i+1}<span class="preset-label"></span><span class="click-badge"></span>`; 
                    bindPresetButton(btn, i); 
                    row2.appendChild(btn); 
                } 
                updatePresetUI(); 
            }
            let closeModalBtn = document.getElementById('closeModal'); 
            if(closeModalBtn) closeModalBtn.onclick = () => document.getElementById('eqModal').classList.remove('active');
            let eqModal = document.getElementById('eqModal'); 
            if(eqModal) eqModal.onclick = (e) => { if(e.target === eqModal) eqModal.classList.remove('active'); };
            if(isSurroundEnabled) applyMergedSurround(); 
            else applyEffectSingle();
            renderStackedChips();
            initCanvasSize();
        }
        
        async function fetchStations(country){ 
            try{ 
                let res=await fetch(`https://de1.api.radio-browser.info/json/stations/bycountry/${encodeURIComponent(country)}?limit=35&order=clickcount&reverse=true`); 
                let data=await res.json(); 
                stationsList=data.filter(s=>s.url_resolved && s.url_resolved.startsWith("http")).slice(0,35); 
                renderStationList(); 
                let last=localStorage.getItem("aetherwave_last_station"); 
                let idx=last?stationsList.findIndex(s=>s.url_resolved===last):-1; 
                if(idx!==-1) selectStation(idx); 
                else if(stationsList.length) selectStation(0); 
                updatePresetUI(); 
                refreshWordRotatorContent(); 
            } catch(e){ 
                let area=document.getElementById("stationListArea"); 
                if(area) area.innerHTML="<div style='padding:20px;'>📡 信号弱</div>"; 
            } 
        }
        
        function startVisuals(){ 
            function draw(){ 
                if(!isPowered){ 
                    frameId=requestAnimationFrame(draw); 
                    return; 
                } 
                let wc=document.getElementById("waveCanvas"), sc=document.getElementById("spectrumCanvas"); 
                if(!wc||!sc){ 
                    frameId=requestAnimationFrame(draw); 
                    return; 
                } 
                let w = wc.width;
                let h = wc.height;
                if(w <= 0 || h <= 0){
                    let parent = wc.parentElement;
                    if(parent){
                        let rect = parent.getBoundingClientRect();
                        w = rect.width || 700;
                        h = rect.height || 120;
                        if(w > 0 && h > 0){
                            wc.width = w;
                            wc.height = h;
                            sc.width = w;
                            sc.height = h;
                            wc.style.width = w + 'px';
                            wc.style.height = h + 'px';
                            sc.style.width = w + 'px';
                            sc.style.height = h + 'px';
                        }
                    }
                    if(w <= 0) w = 700;
                    if(h <= 0) h = 120;
                }
                let wctx=wc.getContext("2d"), sctx=sc.getContext("2d");
                if(!wctx || !sctx){
                    frameId=requestAnimationFrame(draw);
                    return;
                }
                try {
                    let timeData = new Uint8Array(analyser ? analyser.fftSize : 1024);
                    let freqData = new Uint8Array(analyser ? analyser.frequencyBinCount : 512);
                    if(analyser){
                        analyser.getByteTimeDomainData(timeData);
                        analyser.getByteFrequencyData(freqData);
                    } else {
                        for(let i=0;i<timeData.length;i++) timeData[i]=128;
                    }
                    wctx.fillStyle="#010103";
                    wctx.fillRect(0,0,w,h);
                    wctx.beginPath();
                    wctx.lineWidth=1.8;
                    wctx.strokeStyle="#8effaa";
                    let step=w/timeData.length, x=0;
                    for(let i=0;i<timeData.length;i+=2){
                        let v=timeData[i]/128.0;
                        let y=v*h/1.4+h/3.5;
                        if(i===0) wctx.moveTo(x,y);
                        else wctx.lineTo(x,y);
                        x+=step*2;
                    }
                    wctx.stroke();
                    if(analyser){
                        sctx.clearRect(0,0,w,h);
                        let bars=45, stepIdx=Math.floor(freqData.length/bars), barW=w/bars;
                        for(let i=0;i<bars;i++){
                            let avg=0;
                            for(let j=0;j<stepIdx;j++) avg+=freqData[i*stepIdx+j]||0;
                            avg/=stepIdx;
                            let barH=Math.min(h-4,(avg/220)*h*0.75);
                            if(barH<2) barH=1;
                            let grad=sctx.createLinearGradient(i*barW,h-barH,i*barW,h);
                            grad.addColorStop(0,"#88ffaa");
                            grad.addColorStop(1,"#ffaa66");
                            sctx.fillStyle=grad;
                            sctx.fillRect(i*barW,h-barH,barW-1,barH);
                        }
                    }
                } catch(e) {}
                frameId=requestAnimationFrame(draw); 
            } 
            frameId=requestAnimationFrame(draw); 
        }
        
        async function initAudioChain(){ 
            if(audioCtx) return; 
            audioCtx=new (window.AudioContext||window.webkitAudioContext)(); 
            await audioCtx.resume(); 
            radioPlayer.crossOrigin="anonymous"; 
            let source=audioCtx.createMediaElementSource(radioPlayer); 
            analyser=audioCtx.createAnalyser(); 
            analyser.fftSize=1024; 
            masterGain=audioCtx.createGain(); 
            masterGain.gain.value=0.85; 
            stereoPanner=audioCtx.createStereoPanner(); 
            drcCompressor=audioCtx.createDynamicsCompressor(); 
            drcCompressor.threshold.value=-100; 
            drcCompressor.ratio.value=1; 
            reverbDry=audioCtx.createGain(); 
            reverbWet=audioCtx.createGain(); 
            let sampleRate=audioCtx.sampleRate; 
            let length=sampleRate*1.2; 
            let impulse=audioCtx.createBuffer(2,length,sampleRate); 
            let left=impulse.getChannelData(0),right=impulse.getChannelData(1); 
            for(let i=0;i<length;i++){ 
                let n=i/length, decay=Math.exp(-n*4.5); 
                left[i]=(Math.random()-0.5)*decay*0.5; 
                right[i]=(Math.random()-0.5)*decay*0.5; 
            } 
            reverbNode=audioCtx.createConvolver(); 
            reverbNode.buffer=impulse; 
            reverbDry.gain.value=1; 
            reverbWet.gain.value=0; 
            let freqs=[31,62,125,250,500,1000,2000,4000,8000,14000]; 
            let prevNode=source; 
            eqFilters=[]; 
            for(let i=0;i<10;i++){ 
                let f=audioCtx.createBiquadFilter(); 
                f.type="peaking"; 
                f.frequency.value=freqs[i]; 
                f.Q.value=1; 
                f.gain.value=0; 
                prevNode.connect(f); 
                eqFilters.push(f); 
                prevNode=f; 
            } 
            prevNode.connect(stereoPanner); 
            stereoPanner.connect(drcCompressor); 
            drcCompressor.connect(reverbDry); 
            drcCompressor.connect(reverbNode); 
            reverbNode.connect(reverbWet); 
            reverbDry.connect(analyser); 
            reverbWet.connect(analyser); 
            analyser.connect(masterGain); 
            masterGain.connect(audioCtx.destination); 
            if(isSurroundEnabled) applyMergedSurround(); 
            else applyEffectSingle(); 
        }
        
        function startMainApp(){
            let pre=localStorage.getItem("aetherwave_presets"); 
            if(pre) try{ 
                let arr=JSON.parse(pre); 
                if(arr.length<9) arr=[...arr, ...new Array(9-arr.length).fill("")]; 
                presetUrls=arr; 
            }catch(e){}
            startQuoteRotation(); 
            let countrySelect = document.getElementById("countrySelect");
            if(countrySelect) {
                countrySelect.onchange = function() { fetchStations(this.value); };
                fetchStations(countrySelect.value);
            }
            updatePresetUI(); 
            renderLayout(); 
            setInterval(()=>{ 
                let now=new Date(); 
                document.getElementById("liveClock").innerText=now.toLocaleTimeString(); 
                let hour=now.getHours(); 
                let themeMap=[0,2,4,6,8,10,12,14,16,18,20,22]; 
                let idx=0; 
                for(let i=themeMap.length-1;i>=0;i--) if(hour>=themeMap[i]){ idx=i; break; } 
                let slotSpan=document.getElementById("slotTitle"); 
                if(slotSpan) slotSpan.innerHTML = ["🌙 玄墨·夜阑","🌌 深靛·星沉","🌄 破晓·紫气","🌅 晨曦·鎏金","🍃 朝露·清欢","☀️ 曜日·煌煌","🌞 正午·炽白","🌇 午后·琥珀","🌤️ 夕照·熔岩","🌆 暮色·绛霞","🌠 夜澜·星河","🌚 子夜·霜天"][idx]; 
            }, 1000); 
            startWordRotator(); 
            let headerMuteBtn = document.getElementById('globalMuteBtn'); 
            if(headerMuteBtn) headerMuteBtn.onclick = toggleMute; 
        }
        
        function globalAudioActivator(){ 
            if(audioCtx && audioCtx.state==='suspended') audioCtx.resume(); 
            if(radioPlayer.paused && radioPlayer.src) radioPlayer.play().catch(()=>{}); 
        }
        
        window.addEventListener('load',()=>{ 
            startMainApp(); 
            document.body.addEventListener('click',globalAudioActivator); 
            document.body.addEventListener('touchstart',globalAudioActivator); 
            initAudioChain().then(()=>{ 
                if(radioPlayer.src && radioPlayer.paused) radioPlayer.play().catch(()=>{}); 
                if(!visualActive){
                    visualActive = true;
                    startVisuals();
                }
            }); 
        });
        window.addEventListener('resize', function(){
            initCanvasSize();
        });
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
    print("  🎛️ P键: 单击播放(无提示) | 双击保存 | 三击清除")
    print("  🌊 环绕默认开启三维海浪, 最多叠加3个音效")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
