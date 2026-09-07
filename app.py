#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string, send_file, Response, stream_with_context
import requests
import os
import time
import random
import threading
import json
import re
from datetime import datetime

app = Flask(__name__)

# ==================== 配置 ====================
DOWNLOAD_DIR = "最酷音乐"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

favorites_file = "favorites.json"
if os.path.exists(favorites_file):
    with open(favorites_file, 'r', encoding='utf-8') as f:
        FAVORITES = json.load(f)
else:
    FAVORITES = []

download_tasks = {}
song_url_cache = {}

# ==================== 预置推荐歌单 ====================
PRESET_SONGS = [
    {"song": "离别开出花", "singer": "就是南方凯", "mid": "preset_001"},
    {"song": "白鸽乌鸦相爱的戏码", "singer": "潘成", "mid": "preset_002"},
    {"song": "土坡上的狗尾草", "singer": "卢润泽", "mid": "preset_003"},
    {"song": "春庭雪", "singer": "等什么君", "mid": "preset_004"},
    {"song": "放纵L", "singer": "怪阿姨", "mid": "preset_005"},
    {"song": "落", "singer": "唐伯虎Annie", "mid": "preset_006"},
    {"song": "有风无风皆自由", "singer": "王一佳", "mid": "preset_007"},
    {"song": "青丝", "singer": "等什么君", "mid": "preset_008"},
    {"song": "苹果香", "singer": "狼戈", "mid": "preset_009"},
    {"song": "异客", "singer": "杨坤", "mid": "preset_010"},
    {"song": "若月亮没来", "singer": "王宇宙Leto", "mid": "preset_011"},
    {"song": "桃花诺", "singer": "G.E.M.邓紫棋", "mid": "preset_012"},
    {"song": "会开花的云", "singer": "姚晓棠", "mid": "preset_013"},
    {"song": "化风行万里", "singer": "大欢", "mid": "preset_014"},
    {"song": "列车开往春天", "singer": "抠抠", "mid": "preset_015"},
    {"song": "难却", "singer": "平生不晚", "mid": "preset_016"},
    {"song": "风经过需飘过", "singer": "王优秀", "mid": "preset_017"},
    {"song": "转身即心痛", "singer": "吉他的天空", "mid": "preset_018"},
    {"song": "520只为你着迷", "singer": "七叔叶泽浩", "mid": "preset_019"},
    {"song": "唯一", "singer": "告五人", "mid": "preset_020"},
    {"song": "壁上观", "singer": "等什么君", "mid": "preset_021"},
    {"song": "归途的光", "singer": "黄文文", "mid": "preset_022"},
    {"song": "陪我过个冬", "singer": "秋原依", "mid": "preset_023"},
    {"song": "阿嬷", "singer": "周林枫", "mid": "preset_024"},
    {"song": "人间半途", "singer": "刘阳阳", "mid": "preset_025"},
    {"song": "青花", "singer": "周传雄", "mid": "preset_026"},
    {"song": "牵丝戏", "singer": "银临", "mid": "preset_027"},
    {"song": "我期待的不是雪", "singer": "张妙格", "mid": "preset_028"},
    {"song": "越来越不懂", "singer": "蔡健雅", "mid": "preset_029"},
    {"song": "谁", "singer": "廖俊涛", "mid": "preset_030"},
    {"song": "外卖又凉一半", "singer": "星野", "mid": "preset_031"},
    {"song": "满眼是你又怎样", "singer": "贺敬轩", "mid": "preset_032"},
    {"song": "绝口不提你", "singer": "陈雅森", "mid": "preset_033"},
    {"song": "大海 粤语版", "singer": "张明敏", "mid": "preset_034"},
]

LYRICS = [
    "从前从前有个人爱你很久，但偏偏风渐渐把距离吹得好远。——《晴天》",
    "最美的不是下雨天，是曾与你躲过雨的屋檐。——《不能说的秘密》",
    "天青色等烟雨，而我在等你。——《青花瓷》",
    "我一路向北，离开有你的季节。——《一路向北》",
    "你说你有点难追，想让我知难而退。——《告白气球》",
]

def get_random_lyric():
    return random.choice(LYRICS)

def search_music(keyword):
    try:
        results = []
        keyword_lower = keyword.lower()
        for song in PRESET_SONGS:
            if keyword_lower in song['song'].lower() or keyword_lower in song['singer'].lower():
                results.append(song.copy())
        if results:
            return results
        url = f"https://api.vkeys.cn/v2/music/tencent?word={keyword}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['code'] != 200 or not data['data']:
            return []
        for song in data['data']:
            results.append({
                'song': song['song'],
                'singer': song['singer'],
                'album': song.get('album', '未知'),
                'mid': song.get('mid', ''),
                'time': song.get('time', '未知')
            })
        return results
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def get_song_url(mid):
    if mid in song_url_cache:
        return song_url_cache[mid]
    try:
        if mid.startswith('preset_'):
            url = f"https://example.com/music/{mid}.mp3"
            song_url_cache[mid] = url
            return url
        url = f"https://api.vkeys.cn/v2/music/tencent?mid={mid}&quality=8"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['code'] == 200 and data.get('data'):
            song_url = data['data'].get('url')
            if song_url:
                song_url_cache[mid] = song_url
                return song_url
        return None
    except Exception as e:
        print(f"获取下载链接失败: {e}")
        return None

def download_song_task(task_id, song):
    try:
        download_tasks[task_id] = {'status': 'downloading', 'progress': 0, 'song': song['song']}
        song_url = get_song_url(song['mid'])
        if not song_url:
            download_tasks[task_id] = {'status': 'failed', 'error': '无法获取下载链接'}
            return
        safe_singer = re.sub(r'[<>:"/\\|?*]', '_', song['singer'])
        safe_song = re.sub(r'[<>:"/\\|?*]', '_', song['song'])
        file_name = f"{safe_singer} - {safe_song}.mp3"
        save_path = os.path.join(DOWNLOAD_DIR, file_name)
        response = requests.get(song_url, stream=True, timeout=30)
        total_size = int(response.headers.get('content-length', 0))
        with open(save_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        download_tasks[task_id]['progress'] = progress
        download_tasks[task_id] = {
            'status': 'completed',
            'progress': 100,
            'file': file_name,
            'path': save_path
        }
    except Exception as e:
        download_tasks[task_id] = {'status': 'failed', 'error': str(e)}

def proxy_stream(url):
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(
            stream_with_context(generate()),
            status=response.status_code,
            headers={
                'Content-Type': 'audio/mpeg',
                'Content-Length': response.headers.get('content-length', ''),
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=86400',
                'Access-Control-Allow-Origin': '*',
            }
        )
    except Exception as e:
        print(f"流式播放失败: {e}")
        return None

# ==================== 获取已下载歌曲列表 ====================
def get_downloaded_songs():
    songs = []
    if os.path.exists(DOWNLOAD_DIR):
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith('.mp3'):
                # 解析文件名 歌手 - 歌曲.mp3
                name = f.replace('.mp3', '')
                parts = name.split(' - ', 1)
                if len(parts) == 2:
                    songs.append({'song': parts[1], 'singer': parts[0], 'file': f})
                else:
                    songs.append({'song': name, 'singer': '未知', 'file': f})
    return songs

# ==================== HTML 模板 ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎵 最酷音乐下歌精灵 v2.1</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',-apple-system,sans-serif}
        :root{--primary:#f7971e;--primary2:#ffd200;--bg1:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--card:rgba(255,255,255,0.06);--text:#e0e0e0;--text2:#888}
        body{background:linear-gradient(135deg,var(--bg1),var(--bg2),var(--bg3));min-height:100vh;padding:12px;color:var(--text);padding-bottom:160px}
        .container{max-width:800px;margin:0 auto}
        
        .header{text-align:center;padding:18px 0 10px;cursor:pointer}
        .header h1{font-size:30px;background:linear-gradient(135deg,var(--primary),var(--primary2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:inline-block;white-space:nowrap}
        .header .sub{color:var(--text2);font-size:13px;margin-top:4px}
        .header .version{display:inline-block;background:rgba(255,215,0,0.12);color:#ffd700;padding:2px 12px;border-radius:12px;font-size:11px;margin-top:3px}
        .header .lyric{color:#ffd700;font-size:12px;margin-top:6px;opacity:0.5;font-style:italic}
        
        .music-icon-pulse{display:inline-block;font-size:30px;margin-right:6px;animation:colorPulse 2s ease-in-out infinite, iconPulse 1.2s ease-in-out infinite;vertical-align:middle}
        @keyframes colorPulse{
            0%{color:#ff6b6b;text-shadow:0 0 10px rgba(255,107,107,0.5)}
            20%{color:#ffd93d;text-shadow:0 0 15px rgba(255,217,61,0.6)}
            40%{color:#6bcb77;text-shadow:0 0 15px rgba(107,203,119,0.6)}
            60%{color:#4d96ff;text-shadow:0 0 15px rgba(77,150,255,0.6)}
            80%{color:#9b59b6;text-shadow:0 0 15px rgba(155,89,182,0.6)}
            100%{color:#ff6b6b;text-shadow:0 0 10px rgba(255,107,107,0.5)}
        }
        @keyframes iconPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}
        .song-card.playing .card-icon{animation:colorPulse 1.8s ease-in-out infinite, iconPulse 1s ease-in-out infinite !important;opacity:1 !important}
        
        .search-box{background:var(--card);border-radius:14px;padding:14px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.05)}
        .search-row{display:flex;gap:8px;flex-wrap:wrap}
        .search-row input{flex:1;min-width:100px;padding:11px 14px;border:none;border-radius:10px;font-size:14px;background:rgba(255,255,255,0.08);color:#fff;outline:none}
        .search-row input:focus{background:rgba(255,255,255,0.13);box-shadow:0 0 20px rgba(255,215,0,0.06)}
        .search-row input::placeholder{color:#555}
        .search-row button{padding:11px 14px;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;transition:0.2s}
        .search-row button:active{transform:scale(0.95)}
        .btn-search{background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e}
        .btn-singer{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
        .btn-fav{background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff}
        .btn-downloaded{background:linear-gradient(135deg,#17a2b8,#0d6efd);color:#fff}
        
        .quick-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
        .quick-tags button{padding:4px 12px;border:none;border-radius:14px;font-size:11px;cursor:pointer;background:rgba(255,255,255,0.05);color:#aaa;transition:0.2s}
        .quick-tags button:active{background:rgba(255,215,0,0.15);color:#ffd700;transform:scale(0.95)}
        
        .tabs{display:flex;gap:4px;margin-bottom:12px;background:var(--card);border-radius:12px;padding:4px;border:1px solid rgba(255,255,255,0.04)}
        .tabs button{flex:1;padding:9px;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:0.2s;background:transparent;color:#666}
        .tabs button.active{background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e}
        .tabs button:active{transform:scale(0.95)}
        
        .song-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
        .song-card{background:var(--card);border-radius:14px;padding:16px 14px;text-align:center;border:1px solid rgba(255,255,255,0.04);transition:all 0.25s;cursor:pointer;position:relative;min-height:105px;display:flex;flex-direction:column;justify-content:center;align-items:center}
        .song-card:active{transform:scale(0.96);background:rgba(255,255,255,0.08)}
        .song-card.playing{background:rgba(255,215,0,0.12);border-color:rgba(255,215,0,0.25);box-shadow:0 0 30px rgba(255,215,0,0.05)}
        .song-card .card-icon{font-size:28px;margin-bottom:4px;opacity:0.5;transition:all 0.3s}
        .song-card .card-name{font-size:14px;font-weight:600;color:#fff;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
        .song-card .card-singer{font-size:12px;color:var(--text2);margin-top:3px;cursor:pointer}
        .song-card .card-singer:active{color:#ffd700}
        .song-card .card-actions{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;justify-content:center}
        .song-card .card-actions button{padding:4px 12px;border:none;border-radius:8px;font-size:11px;cursor:pointer;transition:0.2s}
        .song-card .card-actions button:active{transform:scale(0.9)}
        .card-btn-download{background:#28a745;color:#fff}
        .card-btn-fav{background:#e74c3c;color:#fff;font-size:14px;padding:4px 8px;border-radius:8px;border:none;cursor:pointer}
        .card-btn-fav.active{background:#555}
        .card-badge{position:absolute;top:6px;right:6px;font-size:9px;background:rgba(255,215,0,0.15);color:#ffd700;padding:1px 8px;border-radius:8px}
        .card-badge.local{background:rgba(23,162,184,0.2);color:#17a2b8}
        
        .download-status{background:var(--card);border-radius:12px;padding:14px;margin-top:12px;border:1px solid rgba(255,215,0,0.08);display:none}
        .download-status .bar{width:100%;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;margin-top:6px}
        .download-status .bar-inner{height:100%;background:linear-gradient(90deg,var(--primary),var(--primary2));transition:width 0.3s;border-radius:2px}
        .download-status .info{display:flex;justify-content:space-between;font-size:12px;color:var(--text2)}
        
        .player{position:fixed;bottom:0;left:0;right:0;background:rgba(20,20,40,0.96);backdrop-filter:blur(16px);padding:10px 14px;border-top:1px solid rgba(255,255,255,0.05);z-index:100}
        .player .top-row{display:flex;align-items:center;gap:10px}
        .player .top-row .info{flex:1;min-width:0}
        .player .top-row .info .name{font-size:14px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .player .top-row .info .singer{font-size:11px;color:var(--text2)}
        .player .top-row .btn-play-pause{padding:6px 12px;border:none;border-radius:50%;font-size:18px;cursor:pointer;background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e;width:38px;height:38px;display:flex;align-items:center;justify-content:center}
        .player .top-row .btn-play-pause:active{transform:scale(0.9)}
        .player .top-row .btn-close{background:transparent;color:#666;border:none;font-size:16px;cursor:pointer;padding:4px 6px}
        .player .top-row .btn-volume{background:transparent;color:#888;border:none;font-size:18px;cursor:pointer;padding:4px 6px}
        .player .bottom-row{display:flex;align-items:center;gap:6px;margin-top:4px}
        .player .bottom-row .btn-mode{background:rgba(255,255,255,0.05);color:#888;border:none;border-radius:5px;padding:3px 8px;font-size:10px;cursor:pointer;white-space:nowrap}
        .player .bottom-row .btn-mode.active{background:rgba(255,215,0,0.12);color:#ffd700}
        .player .progress-bar{flex:1;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;cursor:pointer;position:relative}
        .player .progress-bar .progress-inner{height:100%;background:linear-gradient(90deg,var(--primary),var(--primary2));border-radius:2px;width:0%}
        .player .time-display{font-size:10px;color:#555;min-width:70px;text-align:right}
        .player audio{display:none}
        
        .volume-popup{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:rgba(20,20,40,0.95);backdrop-filter:blur(12px);padding:18px 24px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);z-index:101;display:none;min-width:180px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.5)}
        .volume-popup.show{display:block;animation:fadeUp 0.25s ease}
        @keyframes fadeUp{from{opacity:0;transform:translateX(-50%) translateY(10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
        .volume-popup .vol-icon{font-size:28px;margin-bottom:8px}
        .volume-popup .vol-label{font-size:12px;color:#888;margin-bottom:6px}
        .volume-popup input[type=range]{width:100%;height:4px;-webkit-appearance:none;background:linear-gradient(90deg,var(--primary),var(--primary2));border-radius:2px;outline:none}
        .volume-popup input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:#ffd700;cursor:pointer;box-shadow:0 0 10px rgba(255,215,0,0.3)}
        .volume-popup .vol-value{font-size:14px;color:#fff;margin-top:6px}
        
        .loading{display:none;text-align:center;padding:30px}
        .loading .spinner{width:32px;height:32px;border:3px solid rgba(255,255,255,0.06);border-top:3px solid #ffd700;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto}
        @keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
        
        .empty{text-align:center;padding:40px;color:#555;font-size:14px}
        .footer-text{text-align:center;padding:14px 0 6px;color:#444;font-size:11px;border-top:1px solid rgba(255,255,255,0.03);margin-top:12px}
        
        .toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.8);color:#fff;padding:10px 24px;border-radius:10px;font-size:14px;z-index:999;opacity:0;transition:opacity 0.3s;pointer-events:none}
        .toast.show{opacity:1}
        
        .waiting-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:200;display:none;justify-content:center;align-items:center;flex-direction:column}
        .waiting-overlay.show{display:flex}
        .waiting-overlay .spinner-big{width:60px;height:60px;border:4px solid rgba(255,255,255,0.1);border-top:4px solid #ffd700;border-radius:50%;animation:spin 1s linear infinite}
        .waiting-overlay .waiting-text{color:#fff;font-size:18px;margin-top:20px;animation:pulseText 1s ease-in-out infinite}
        @keyframes pulseText{0%,100%{opacity:1}50%{opacity:0.5}}
        .waiting-overlay .waiting-time{color:#ffd700;font-size:14px;margin-top:8px}
        
        @media(max-width:480px){
            .song-grid{grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px}
            .song-card{padding:12px 10px;min-height:90px}
            .song-card .card-name{font-size:13px}
            .search-row input{min-width:70px;font-size:13px;padding:9px 12px}
            .search-row button{padding:9px 10px;font-size:11px}
            .header h1{font-size:22px;white-space:nowrap}
            .player{padding:8px 12px}
            .player .top-row .btn-play-pause{width:34px;height:34px;font-size:16px}
            .volume-popup{min-width:140px;padding:14px 18px;bottom:80px}
            .music-icon-pulse{font-size:24px}
        }
        @media(max-width:360px){.song-grid{grid-template-columns:repeat(2,1fr)}}
        @media(max-width:380px){.header h1{font-size:18px;white-space:nowrap}}
    </style>
</head>
<body>
<div class="toast" id="toast"></div>

<!-- 等待遮罩 -->
<div class="waiting-overlay" id="waitingOverlay">
    <div class="spinner-big"></div>
    <div class="waiting-text">⏳ 正在加载歌曲...</div>
    <div class="waiting-time" id="waitingTime">等待 0 秒</div>
</div>

<div class="volume-popup" id="volumePopup">
    <div class="vol-icon" id="volIcon">🔊</div>
    <div class="vol-label">音量</div>
    <input type="range" id="volumeSlider" min="0" max="1" step="0.05" value="0.8">
    <div class="vol-value" id="volValue">80%</div>
</div>

<div class="container">
    <div class="header" onclick="goHome()">
        <h1>
            <span class="music-icon-pulse">🎵</span>
            最酷音乐下歌精灵
            <span class="version">v2.1</span>
        </h1>
        <div class="sub">🎧 点击卡片立即播放 · 边下边播</div>
        <div class="lyric">✨ "{{ lyric }}"</div>
    </div>
    
    <div class="search-box">
        <div class="search-row">
            <input type="text" id="keyword" placeholder="搜索歌曲或歌手..." onkeydown="if(event.key==='Enter') searchMusic()">
            <button class="btn-search" onclick="searchMusic()">🔍</button>
            <button class="btn-singer" onclick="searchBySinger()">🎤</button>
            <button class="btn-fav" onclick="showFavorites()">❤️</button>
            <button class="btn-downloaded" onclick="showDownloaded()">📂</button>
        </div>
        <div class="quick-tags" id="quickTags"></div>
    </div>
    
    <div class="tabs">
        <button class="active" onclick="switchTab('recommend')">🔥 推荐</button>
        <button onclick="switchTab('search')">📋 搜索结果</button>
        <button onclick="switchTab('favorites')">❤️ 收藏</button>
        <button onclick="switchTab('downloaded')">📂 已下载</button>
    </div>
    
    <div id="loading" class="loading"><div class="spinner"></div><p style="color:#888;margin-top:6px;font-size:13px">加载中...</p></div>
    
    <div id="songGrid" class="song-grid"></div>
    
    <div id="downloadStatus" class="download-status">
        <div class="info"><span id="downloadInfo">准备下载...</span><span id="downloadProgress">0%</span></div>
        <div class="bar"><div class="bar-inner" id="progressBar" style="width:0%"></div></div>
        <div style="margin-top:4px;font-size:11px;color:#666" id="downloadDetail"></div>
    </div>
    
    <div class="footer-text">🎵 最酷音乐下歌精灵 v2.1 · 点击卡片立即播放</div>
</div>

<!-- ===== 播放器 ===== -->
<div class="player" id="player" style="display:none">
    <div class="top-row">
        <button class="btn-close" onclick="closePlayer()">✕</button>
        <div class="info">
            <div class="name" id="playerName">歌曲名</div>
            <div class="singer" id="playerSinger">歌手</div>
        </div>
        <button class="btn-volume" id="volumeBtn" onclick="toggleVolume(event)">🔊</button>
        <button class="btn-play-pause" id="playPauseBtn" onclick="togglePlay()">▶️</button>
    </div>
    <div class="bottom-row">
        <button class="btn-mode active" id="modeBtn" onclick="toggleMode()">🔁 列表</button>
        <div class="progress-bar" id="progressBarPlayer" onclick="seekTo(event)">
            <div class="progress-inner" id="progressInner"></div>
        </div>
        <div class="time-display">
            <span id="currentTime">00:00</span>/<span id="totalTime">00:00</span>
        </div>
    </div>
    <audio id="audioPlayer"></audio>
</div>

<script>
// ==================== 预设数据 ====================
const presetSongs = {{ preset_songs|tojson }};

// ==================== 状态 ====================
let currentSongs = [];
let currentTab = 'recommend';
let downloadTaskId = null;
let statusCheckInterval = null;
let favorites = [];
let currentPlayIndex = -1;
let playMode = 'all';
let isPlaying = false;
let shuffledIndices = [];
let shuffleIndex = 0;
let volumeTimeout = null;
let waitingTimer = null;
let waitingSeconds = 0;

// ==================== Toast ====================
function showToast(msg) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), 2500);
}

// ==================== 跳转主页 ====================
function goHome() {
    window.location.href = '/';
}

// ==================== 音量控制 ====================
function toggleVolume(e) {
    e.stopPropagation();
    const popup = document.getElementById('volumePopup');
    if (popup.classList.contains('show')) {
        popup.classList.remove('show');
        clearTimeout(volumeTimeout);
    } else {
        popup.classList.add('show');
        clearTimeout(volumeTimeout);
        volumeTimeout = setTimeout(() => popup.classList.remove('show'), 4000);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById('volumeSlider');
    const valDisplay = document.getElementById('volValue');
    const icon = document.getElementById('volIcon');
    const audio = document.getElementById('audioPlayer');
    
    slider.addEventListener('input', function() {
        const val = parseFloat(this.value);
        const pct = Math.round(val * 100);
        valDisplay.textContent = pct + '%';
        audio.volume = val;
        icon.textContent = val > 0.5 ? '🔊' : val > 0.1 ? '🔉' : '🔇';
        clearTimeout(volumeTimeout);
        volumeTimeout = setTimeout(() => {
            document.getElementById('volumePopup').classList.remove('show');
        }, 4000);
    });
});

document.addEventListener('click', function(e) {
    const popup = document.getElementById('volumePopup');
    const btn = document.getElementById('volumeBtn');
    if (!popup.contains(e.target) && !btn.contains(e.target)) {
        popup.classList.remove('show');
        clearTimeout(volumeTimeout);
    }
});

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadRecommend();
    loadQuickTags();
    loadFavoritesFromStorage();
    loadPlayerState();
});

function loadQuickTags() {
    const tags = ['周杰伦','林俊杰','陈奕迅','邓紫棋','热歌'];
    const container = document.getElementById('quickTags');
    container.innerHTML = tags.map(t => `<button onclick="quickSearch('${t}')">${t}</button>`).join('');
}

function loadFavoritesFromStorage() {
    try { const stored = localStorage.getItem('music_favorites'); if (stored) favorites = JSON.parse(stored); } catch(e) {}
}

function saveFavorites() {
    try { localStorage.setItem('music_favorites', JSON.stringify(favorites)); } catch(e) {}
}

function isFavorite(song) {
    return favorites.some(s => s.song === song.song && s.singer === song.singer);
}

function savePlayerState() {
    const audio = document.getElementById('audioPlayer');
    try {
        localStorage.setItem('player_state', JSON.stringify({
            currentTime: audio.currentTime || 0,
            playing: isPlaying,
            song: currentPlayIndex >= 0 && currentPlayIndex < currentSongs.length ? currentSongs[currentPlayIndex] : null,
            index: currentPlayIndex,
            mode: playMode
        }));
    } catch(e) {}
}

function loadPlayerState() {
    try {
        const state = JSON.parse(localStorage.getItem('player_state'));
        if (state && state.song) {
            const idx = currentSongs.findIndex(s => s.song === state.song.song && s.singer === state.song.singer);
            if (idx >= 0) {
                currentPlayIndex = idx;
                playMode = state.mode || 'all';
                updateModeButton();
                playSong(idx, state.currentTime || 0);
            }
        }
    } catch(e) {}
}

// ==================== 渲染卡片 ====================
function renderSongs(songs, showFavoriteBtn=true, isLocal=false) {
    const container = document.getElementById('songGrid');
    if (!songs || songs.length === 0) {
        container.innerHTML = '<div class="empty">🎵 暂无歌曲</div>';
        return;
    }
    currentSongs = songs;
    shuffledIndices = [];
    shuffleIndex = 0;
    
    container.innerHTML = songs.map((song, idx) => {
        const fav = isFavorite(song);
        const isCurrent = (idx === currentPlayIndex);
        const localBadge = isLocal ? '<div class="card-badge local">📂 本地</div>' : '';
        const badge = isCurrent ? '<div class="card-badge">▶ 播放中</div>' : localBadge;
        return `
        <div class="song-card ${isCurrent ? 'playing' : ''}" id="card-${idx}" onclick="playSong(${idx})">
            ${badge}
            <div class="card-icon">${isCurrent ? '🎵' : '🎶'}</div>
            <div class="card-name">${song.song}</div>
            <div class="card-singer" onclick="event.stopPropagation();searchSinger('${song.singer}')">${song.singer}</div>
            <div class="card-actions" onclick="event.stopPropagation();">
                <button class="card-btn-download" onclick="downloadSong(${idx})">⬇️ 下载</button>
                ${showFavoriteBtn ? `
                    <button class="card-btn-fav ${fav ? 'active' : ''}" onclick="toggleFavorite(${idx})">
                        ${fav ? '❤️' : '🤍'}
                    </button>
                ` : ''}
            </div>
        </div>
    `}).join('');
}

// ==================== Tab 切换 ====================
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    const map = {'recommend':0,'search':1,'favorites':2,'downloaded':3};
    const btns = document.querySelectorAll('.tabs button');
    if (map[tab] !== undefined) btns[map[tab]].classList.add('active');
    if (tab === 'recommend') loadRecommend();
    else if (tab === 'favorites') showFavorites();
    else if (tab === 'downloaded') showDownloaded();
}

function loadRecommend() {
    showLoading(true);
    setTimeout(() => { renderSongs(presetSongs); showLoading(false); }, 300);
}

function searchMusic() {
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) return;
    showLoading(true);
    document.getElementById('songGrid').innerHTML = '';
    fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            showLoading(false);
            if (data.code === 200 && data.data.length > 0) {
                renderSongs(data.data);
                switchTab('search');
            } else {
                document.getElementById('songGrid').innerHTML = `<div class="empty">😅 没有找到 "${keyword}"</div>`;
            }
        })
        .catch(() => { showLoading(false); document.getElementById('songGrid').innerHTML = '<div class="empty">❌ 网络错误</div>'; });
}

function quickSearch(k) { document.getElementById('keyword').value = k; searchMusic(); }
function searchBySinger() { const s = prompt('请输入歌手名称：'); if(s && s.trim()) { document.getElementById('keyword').value=s; searchMusic(); } }
function searchSinger(s) { document.getElementById('keyword').value=s; searchMusic(); }

// ==================== 已下载 ====================
function showDownloaded() {
    showLoading(true);
    fetch('/api/downloaded')
        .then(res => res.json())
        .then(data => {
            showLoading(false);
            if (data.code === 200 && data.data.length > 0) {
                renderSongs(data.data, false, true);
                switchTab('downloaded');
            } else {
                document.getElementById('songGrid').innerHTML = '<div class="empty">📂 还没有下载歌曲</div>';
                switchTab('downloaded');
            }
        })
        .catch(() => {
            showLoading(false);
            document.getElementById('songGrid').innerHTML = '<div class="empty">❌ 加载失败</div>';
        });
}

// ==================== 收藏 ====================
function toggleFavorite(idx) {
    const song = currentSongs[idx];
    if (!song) return;
    const index = favorites.findIndex(s => s.song === song.song && s.singer === song.singer);
    if (index > -1) favorites.splice(index, 1);
    else favorites.push({song: song.song, singer: song.singer, mid: song.mid || ''});
    saveFavorites();
    showToast(index > -1 ? '已取消收藏' : '❤️ 已收藏');
    if (currentTab === 'favorites') showFavorites();
    else renderSongs(currentSongs);
}

function showFavorites() {
    if (favorites.length === 0) {
        document.getElementById('songGrid').innerHTML = '<div class="empty">💔 还没有收藏歌曲<br><span style="font-size:12px;color:#555">点击 🤍 收藏</span></div>';
        switchTab('favorites');
        return;
    }
    renderSongs(favorites, false);
    switchTab('favorites');
}

// ==================== 等待遮罩 ====================
function showWaiting(show) {
    const overlay = document.getElementById('waitingOverlay');
    if (show) {
        overlay.classList.add('show');
        waitingSeconds = 0;
        document.getElementById('waitingTime').textContent = '等待 0 秒';
        clearInterval(waitingTimer);
        waitingTimer = setInterval(() => {
            waitingSeconds++;
            document.getElementById('waitingTime').textContent = '等待 ' + waitingSeconds + ' 秒';
            if (waitingSeconds >= 6) {
                clearInterval(waitingTimer);
            }
        }, 1000);
    } else {
        overlay.classList.remove('show');
        clearInterval(waitingTimer);
    }
}

// ==================== 播放（点击卡片立即播放） ====================
function playSong(idx, seekTime) {
    if (idx < 0 || idx >= currentSongs.length) return;
    const song = currentSongs[idx];
    if (!song) return;
    
    // 显示等待遮罩
    showWaiting(true);
    
    currentPlayIndex = idx;
    const player = document.getElementById('player');
    const audio = document.getElementById('audioPlayer');
    document.getElementById('playerName').textContent = song.song;
    document.getElementById('playerSinger').textContent = song.singer;
    
    document.querySelectorAll('.song-card').forEach(el => el.classList.remove('playing'));
    const el = document.getElementById(`card-${idx}`);
    if (el) el.classList.add('playing');
    
    const playUrl = `/api/stream/${encodeURIComponent(song.mid || '')}`;
    audio.src = playUrl;
    audio.load();
    
    // 6秒后自动播放或等待加载完成
    let loaded = false;
    audio.oncanplay = function() {
        if (!loaded) {
            loaded = true;
            showWaiting(false);
            audio.play();
            isPlaying = true;
            player.style.display = 'block';
            document.getElementById('playPauseBtn').textContent = '⏸️';
            setupAudioEvents();
            savePlayerState();
            showToast(`▶️ 正在播放: ${song.song}`);
        }
    };
    
    // 6秒超时强制播放
    setTimeout(() => {
        showWaiting(false);
        if (!loaded) {
            audio.play().catch(() => {});
            isPlaying = true;
            player.style.display = 'block';
            document.getElementById('playPauseBtn').textContent = '⏸️';
            setupAudioEvents();
            savePlayerState();
            showToast(`▶️ 正在播放: ${song.song}`);
        }
    }, 6000);
    
    // 错误处理
    audio.onerror = function() {
        showWaiting(false);
        showToast('❌ 播放失败，请重试');
        isPlaying = false;
        document.getElementById('playPauseBtn').textContent = '▶️';
    };
}

function togglePlay() {
    const audio = document.getElementById('audioPlayer');
    if (audio.paused) {
        audio.play();
        isPlaying = true;
        document.getElementById('playPauseBtn').textContent = '⏸️';
    } else {
        audio.pause();
        isPlaying = false;
        document.getElementById('playPauseBtn').textContent = '▶️';
    }
    savePlayerState();
}

function closePlayer() {
    document.getElementById('player').style.display = 'none';
    const audio = document.getElementById('audioPlayer');
    audio.pause();
    audio.src = '';
    isPlaying = false;
    savePlayerState();
}

function seekTo(e) {
    const bar = document.getElementById('progressBarPlayer');
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const audio = document.getElementById('audioPlayer');
    if (audio.duration) {
        audio.currentTime = pct * audio.duration;
    }
}

// ===== 播放模式 =====
function toggleMode() {
    const modes = ['all', 'single', 'loop', 'random'];
    const labels = ['🔁 列表', '🔂 单曲', '🔁 循环', '🎲 随机'];
    const idx = modes.indexOf(playMode);
    playMode = modes[(idx + 1) % 4];
    updateModeButton();
    savePlayerState();
    if (playMode === 'random') generateShuffleList();
    showToast('播放模式: ' + labels[modes.indexOf(playMode)]);
}

function updateModeButton() {
    const btn = document.getElementById('modeBtn');
    const labels = {'all':'🔁 列表', 'single':'🔂 单曲', 'loop':'🔁 循环', 'random':'🎲 随机'};
    btn.textContent = labels[playMode] || '🔁 列表';
}

function generateShuffleList() {
    shuffledIndices = Array.from({length: currentSongs.length}, (_, i) => i);
    for (let i = shuffledIndices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledIndices[i], shuffledIndices[j]] = [shuffledIndices[j], shuffledIndices[i]];
    }
    shuffleIndex = 0;
    if (currentPlayIndex >= 0) {
        const pos = shuffledIndices.indexOf(currentPlayIndex);
        if (pos >= 0) shuffleIndex = pos;
    }
}

function getNextSongIndex() {
    if (playMode === 'random') {
        if (shuffledIndices.length === 0) generateShuffleList();
        const idx = shuffledIndices[shuffleIndex];
        shuffleIndex = (shuffleIndex + 1) % shuffledIndices.length;
        return idx;
    }
    return (currentPlayIndex + 1) % currentSongs.length;
}

function setupAudioEvents() {
    const audio = document.getElementById('audioPlayer');
    const progress = document.getElementById('progressInner');
    const currentTimeEl = document.getElementById('currentTime');
    const totalTimeEl = document.getElementById('totalTime');
    
    audio.ontimeupdate = function() {
        if (audio.duration) {
            progress.style.width = (audio.currentTime / audio.duration * 100) + '%';
            currentTimeEl.textContent = formatTime(audio.currentTime);
            totalTimeEl.textContent = formatTime(audio.duration);
        }
        savePlayerState();
    };
    
    audio.onended = function() {
        if (playMode === 'single') {
            audio.currentTime = 0;
            audio.play();
        } else if (playMode === 'loop' || playMode === 'all' || playMode === 'random') {
            const nextIdx = getNextSongIndex();
            playSong(nextIdx);
        } else {
            isPlaying = false;
            document.getElementById('playPauseBtn').textContent = '▶️';
            savePlayerState();
        }
    };
    
    audio.onplay = function() { isPlaying = true; document.getElementById('playPauseBtn').textContent = '⏸️'; };
    audio.onpause = function() { isPlaying = false; document.getElementById('playPauseBtn').textContent = '▶️'; };
}

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
}

// ==================== 下载 ====================
function downloadSong(idx) {
    const song = currentSongs[idx];
    if (!song) return;
    const status = document.getElementById('downloadStatus');
    status.style.display = 'block';
    document.getElementById('downloadInfo').textContent = `⬇️ ${song.song} - ${song.singer}`;
    document.getElementById('downloadProgress').textContent = '0%';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('downloadDetail').textContent = '⏳ 准备下载...';
    showToast(`⏳ 开始下载: ${song.song}`);
    
    fetch('/api/download', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(song)
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            downloadTaskId = data.task_id;
            startStatusCheck();
        } else {
            document.getElementById('downloadDetail').textContent = '❌ ' + data.message;
            showToast('❌ 下载失败: ' + data.message);
        }
    })
    .catch(() => { document.getElementById('downloadDetail').textContent = '❌ 下载请求失败'; showToast('❌ 下载请求失败'); });
}

function startStatusCheck() {
    if (statusCheckInterval) clearInterval(statusCheckInterval);
    statusCheckInterval = setInterval(() => {
        fetch(`/api/download/status/${downloadTaskId}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(statusCheckInterval);
                    document.getElementById('downloadInfo').textContent = '✅ 下载完成!';
                    document.getElementById('downloadProgress').textContent = '100%';
                    document.getElementById('progressBar').style.width = '100%';
                    document.getElementById('downloadDetail').innerHTML = `
                        📁 已保存: ${data.file}
                        <br>
                        <a href="/api/download/file/${downloadTaskId}" style="color:#ffd700;" download>🎧 点击下载文件</a>
                    `;
                    showToast('✅ 下载完成: ' + data.file);
                } else if (data.status === 'downloading') {
                    document.getElementById('downloadProgress').textContent = data.progress + '%';
                    document.getElementById('progressBar').style.width = data.progress + '%';
                    document.getElementById('downloadDetail').textContent = `⏳ 下载中... ${data.progress}%`;
                } else if (data.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    document.getElementById('downloadInfo').textContent = '❌ 下载失败';
                    document.getElementById('downloadDetail').textContent = '错误: ' + (data.error || '未知错误');
                    showToast('❌ 下载失败');
                }
            })
            .catch(() => {});
    }, 1000);
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}
</script>
</body>
</html>
'''

# ==================== 路由 ====================

@app.route('/api/stream/<mid>')
def stream_music(mid):
    song_url = get_song_url(mid)
    if not song_url:
        return jsonify({'code': 404, 'message': '无法获取播放链接'}), 404
    if song_url.startswith('https://example.com/'):
        return jsonify({'code': 404, 'message': '预置歌曲请先下载到服务器'}), 404
    response = proxy_stream(song_url)
    if response:
        return response
    return jsonify({'code': 404, 'message': '播放失败'}), 404

@app.route('/api/downloaded')
def get_downloaded():
    songs = get_downloaded_songs()
    return jsonify({'code': 200, 'data': songs})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                  lyric=get_random_lyric(),
                                  preset_songs=PRESET_SONGS)

@app.route('/api/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'code': 400, 'message': '请输入关键词'})
    results = search_music(keyword)
    return jsonify({'code': 200, 'data': results})

@app.route('/api/download', methods=['POST'])
def start_download():
    song = request.json
    if not song or not song.get('mid'):
        return jsonify({'code': 400, 'message': '无效的歌曲信息'})
    task_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
    thread = threading.Thread(target=download_song_task, args=(task_id, song))
    thread.daemon = True
    thread.start()
    return jsonify({'code': 200, 'task_id': task_id})

@app.route('/api/download/status/<task_id>')
def download_status(task_id):
    if task_id not in download_tasks:
        return jsonify({'status': 'not_found'})
    return jsonify(download_tasks[task_id])

@app.route('/api/download/file/<task_id>')
def download_file(task_id):
    if task_id not in download_tasks:
        return jsonify({'error': '任务不存在'}), 404
    task = download_tasks[task_id]
    if task.get('status') != 'completed':
        return jsonify({'error': '文件未准备好'}), 404
    path = task.get('path')
    if not path or not os.path.exists(path):
        return jsonify({'error': '文件不存在'}), 404
    return send_file(path, as_attachment=True, download_name=task.get('file', 'music.mp3'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print("  🎵 最酷音乐下歌精灵 v2.1")
    print("="*60)
    print(f"  🌐 访问地址: http://localhost:{port}")
    print("  🎧 点击卡片立即播放 · 6秒等待")
    print("  📂 已下载歌曲列表")
    print("  🏠 点击标题返回主页")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
