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
from urllib.parse import quote

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

song_url_cache = {}
download_tasks = {}

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
    {"song": "花火", "singer": "梁咏琪", "mid": "preset_035"},
]

LYRICS = [
    "从前从前有个人爱你很久，但偏偏风渐渐把距离吹得好远。——《晴天》",
    "最美的不是下雨天，是曾与你躲过雨的屋檐。——《不能说的秘密》",
    "天青色等烟雨，而我在等你。——《青花瓷》",
    "我一路向北，离开有你的季节。——《一路向北》",
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
            return None
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

def get_downloaded_songs():
    songs = []
    if os.path.exists(DOWNLOAD_DIR):
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith('.mp3'):
                name = f.replace('.mp3', '')
                parts = name.split(' - ', 1)
                if len(parts) == 2:
                    songs.append({'song': parts[1], 'singer': parts[0], 'file': f, 'mid': 'local_' + f})
                else:
                    songs.append({'song': name, 'singer': '未知', 'file': f, 'mid': 'local_' + f})
    return songs

def proxy_stream(url, as_attachment=False, filename=None):
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        headers = {
            'Content-Type': 'audio/mpeg',
            'Content-Length': response.headers.get('content-length', ''),
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=86400',
            'Access-Control-Allow-Origin': '*',
        }
        if as_attachment and filename:
            headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(stream_with_context(generate()), status=response.status_code, headers=headers)
    except Exception as e:
        print(f"流式代理失败: {e}")
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

# ==================== HTML 模板（整合播放逻辑） ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>🎵 最酷音乐下歌精灵 v2.1</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;font-family:'Segoe UI',-apple-system,sans-serif}
        :root{--primary:#f7971e;--primary2:#ffd200;--bg1:#1a1a2e;--bg2:#16213e;--bg3:#0f3460;--card:rgba(255,255,255,0.06);--text:#e0e0e0;--text2:#888}
        body{background:linear-gradient(135deg,var(--bg1),var(--bg2),var(--bg3));min-height:100vh;padding:10px;color:var(--text);padding-bottom:180px}
        .container{max-width:800px;margin:0 auto}
        
        .header{text-align:center;padding:14px 0 8px;cursor:pointer}
        .header h1{font-size:26px;background:linear-gradient(135deg,var(--primary),var(--primary2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:inline-block;white-space:nowrap}
        .header .sub{color:var(--text2);font-size:12px;margin-top:2px}
        .header .version{display:inline-block;background:rgba(255,215,0,0.12);color:#ffd700;padding:1px 10px;border-radius:10px;font-size:10px;margin-top:2px}
        .header .lyric{color:#ffd700;font-size:11px;margin-top:4px;opacity:0.4;font-style:italic}
        
        .music-icon-pulse{display:inline-block;font-size:26px;margin-right:4px;animation:colorPulse 2s ease-in-out infinite, iconPulse 1.2s ease-in-out infinite;vertical-align:middle}
        @keyframes colorPulse{
            0%{color:#ff6b6b;text-shadow:0 0 10px rgba(255,107,107,0.5)}
            20%{color:#ffd93d;text-shadow:0 0 15px rgba(255,217,61,0.6)}
            40%{color:#6bcb77;text-shadow:0 0 15px rgba(107,203,119,0.6)}
            60%{color:#4d96ff;text-shadow:0 0 15px rgba(77,150,255,0.6)}
            80%{color:#9b59b6;text-shadow:0 0 15px rgba(155,89,182,0.6)}
            100%{color:#ff6b6b;text-shadow:0 0 10px rgba(255,107,107,0.5)}
        }
        @keyframes iconPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.12)}}
        
        .search-box{background:var(--card);border-radius:14px;padding:12px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.05)}
        .search-row{display:flex;gap:6px;flex-wrap:wrap}
        .search-row input{flex:1;min-width:80px;padding:10px 14px;border:none;border-radius:10px;font-size:14px;background:rgba(255,255,255,0.08);color:#fff;outline:none}
        .search-row input:focus{background:rgba(255,255,255,0.13)}
        .search-row input::placeholder{color:#555}
        .search-row button{padding:10px 12px;border:none;border-radius:10px;font-size:12px;font-weight:600;cursor:pointer;transition:0.2s}
        .search-row button:active{transform:scale(0.95)}
        .btn-search{background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e}
        .btn-singer{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
        .btn-fav{background:linear-gradient(135deg,#e74c3c,#c0392b);color:#fff}
        .btn-downloaded{background:linear-gradient(135deg,#17a2b8,#0d6efd);color:#fff}
        
        .quick-tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
        .quick-tags button{padding:4px 10px;border:none;border-radius:12px;font-size:10px;cursor:pointer;background:rgba(255,255,255,0.05);color:#aaa;transition:0.2s}
        .quick-tags button:active{background:rgba(255,215,0,0.15);color:#ffd700}
        
        .tabs{display:flex;gap:3px;margin-bottom:10px;background:var(--card);border-radius:10px;padding:3px;border:1px solid rgba(255,255,255,0.04)}
        .tabs button{flex:1;padding:8px;border:none;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;transition:0.2s;background:transparent;color:#666}
        .tabs button.active{background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e}
        .tabs button:active{transform:scale(0.95)}
        
        .song-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
        .song-card{background:var(--card);border-radius:12px;padding:14px 12px;text-align:center;border:1px solid rgba(255,255,255,0.04);transition:all 0.25s;cursor:pointer;position:relative;min-height:95px;display:flex;flex-direction:column;justify-content:center;align-items:center}
        .song-card:active{transform:scale(0.96);background:rgba(255,255,255,0.08)}
        .song-card.playing{background:rgba(255,215,0,0.12);border-color:rgba(255,215,0,0.25)}
        .song-card .card-icon{font-size:24px;margin-bottom:3px;opacity:0.5}
        .song-card.playing .card-icon{animation:pulse 1.5s ease-in-out infinite;opacity:1}
        @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
        .song-card .card-name{font-size:13px;font-weight:600;color:#fff;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
        .song-card .card-singer{font-size:11px;color:var(--text2);margin-top:2px}
        .song-card .card-actions{display:flex;gap:5px;margin-top:6px;flex-wrap:wrap;justify-content:center}
        .song-card .card-actions button{padding:3px 10px;border:none;border-radius:6px;font-size:10px;cursor:pointer;transition:0.2s}
        .song-card .card-actions button:active{transform:scale(0.9)}
        .card-btn-download{background:#28a745;color:#fff}
        .card-btn-fav{background:#e74c3c;color:#fff;font-size:13px;padding:3px 7px;border-radius:6px;border:none;cursor:pointer}
        .card-btn-fav.active{background:#555}
        .card-badge{position:absolute;top:4px;right:4px;font-size:8px;background:rgba(255,215,0,0.15);color:#ffd700;padding:1px 6px;border-radius:6px}
        .card-badge.local{background:rgba(23,162,184,0.2);color:#17a2b8}
        
        .player{position:fixed;bottom:0;left:0;right:0;background:rgba(20,20,40,0.96);backdrop-filter:blur(16px);padding:10px 14px;border-top:1px solid rgba(255,255,255,0.05);z-index:100}
        .player .top-row{display:flex;align-items:center;gap:8px}
        .player .top-row .info{flex:1;min-width:0}
        .player .top-row .info .name{font-size:13px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .player .top-row .info .singer{font-size:10px;color:var(--text2)}
        .player .top-row .btn-play-pause{padding:6px 10px;border:none;border-radius:50%;font-size:16px;cursor:pointer;background:linear-gradient(135deg,var(--primary),var(--primary2));color:#1a1a2e;width:34px;height:34px;display:flex;align-items:center;justify-content:center}
        .player .top-row .btn-play-pause:active{transform:scale(0.9)}
        .player .top-row .btn-close{background:transparent;color:#666;border:none;font-size:14px;cursor:pointer;padding:3px 5px}
        .player .bottom-row{display:flex;align-items:center;gap:5px;margin-top:3px}
        .player .bottom-row .btn-mode{background:rgba(255,255,255,0.05);color:#888;border:none;border-radius:4px;padding:2px 6px;font-size:9px;cursor:pointer}
        .player .bottom-row .btn-mode.active{background:rgba(255,215,0,0.12);color:#ffd700}
        .player .progress-bar{flex:1;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;cursor:pointer;position:relative}
        .player .progress-bar .progress-inner{height:100%;background:linear-gradient(90deg,var(--primary),var(--primary2));border-radius:2px;width:0%}
        .player .time-display{font-size:9px;color:#555;min-width:60px;text-align:right}
        .player audio{display:none}
        
        .toast{position:fixed;top:15px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.85);color:#fff;padding:8px 20px;border-radius:10px;font-size:13px;z-index:999;opacity:0;transition:opacity 0.3s;pointer-events:none;max-width:90%}
        .toast.show{opacity:1}
        
        .empty{text-align:center;padding:30px;color:#555;font-size:13px}
        
        @media(max-width:480px){
            .song-grid{grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}
            .song-card{padding:10px 8px;min-height:80px}
            .song-card .card-name{font-size:12px}
            .search-row input{min-width:60px;font-size:12px;padding:8px 10px}
            .search-row button{padding:8px 10px;font-size:11px}
            .header h1{font-size:20px}
            .player{padding:8px 10px}
            .player .top-row .btn-play-pause{width:30px;height:30px;font-size:14px}
        }
    </style>
</head>
<body>
<div class="toast" id="toast"></div>

<div class="container">
    <div class="header" onclick="goHome()">
        <h1>
            <span class="music-icon-pulse">🎵</span>
            最酷音乐下歌精灵
            <span class="version">v2.1</span>
        </h1>
        <div class="sub">🎧 点击卡片立即播放 · 直接下载</div>
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
    
    <div id="songGrid" class="song-grid"></div>
</div>

<!-- 播放器 -->
<div class="player" id="player" style="display:none">
    <div class="top-row">
        <button class="btn-close" onclick="closePlayer()">✕</button>
        <div class="info">
            <div class="name" id="playerName">歌曲名</div>
            <div class="singer" id="playerSinger">歌手</div>
        </div>
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
let favorites = [];
let currentPlayIndex = -1;
let playMode = 'order';
let isPlaying = false;
let audioElement = null;

// ==================== Toast ====================
function showToast(msg) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), 2500);
}

function goHome() { window.location.href = '/'; }

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    loadRecommend();
    loadQuickTags();
    loadFavoritesFromStorage();
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

// ==================== 渲染卡片 ====================
function renderSongs(songs, showFavoriteBtn=true, isLocal=false) {
    const container = document.getElementById('songGrid');
    if (!songs || songs.length === 0) {
        container.innerHTML = '<div class="empty">🎵 暂无歌曲</div>';
        return;
    }
    currentSongs = songs;
    
    container.innerHTML = songs.map((song, idx) => {
        const fav = isFavorite(song);
        const isCurrent = (idx === currentPlayIndex && audioElement && audioElement.src);
        const badge = isCurrent ? '<div class="card-badge">▶ 播放中</div>' : (isLocal ? '<div class="card-badge local">📂 本地</div>' : '');
        return `
        <div class="song-card ${isCurrent ? 'playing' : ''}" id="card-${idx}" onclick="playSong(${idx})">
            ${badge}
            <div class="card-icon">${isCurrent ? '🎵' : '🎶'}</div>
            <div class="card-name">${song.song}</div>
            <div class="card-singer">${song.singer}</div>
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
    renderSongs(presetSongs);
}

function searchMusic() {
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) return;
    fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            if (data.code === 200 && data.data.length > 0) {
                renderSongs(data.data);
                switchTab('search');
            } else {
                document.getElementById('songGrid').innerHTML = `<div class="empty">😅 没有找到 "${keyword}"</div>`;
            }
        })
        .catch(() => { document.getElementById('songGrid').innerHTML = '<div class="empty">❌ 网络错误</div>'; });
}

function quickSearch(k) { document.getElementById('keyword').value = k; searchMusic(); }
function searchBySinger() { const s = prompt('请输入歌手名称：'); if(s && s.trim()) { document.getElementById('keyword').value=s; searchMusic(); } }

// ==================== 已下载 ====================
function showDownloaded() {
    fetch('/api/downloaded')
        .then(res => res.json())
        .then(data => {
            if (data.code === 200 && data.data.length > 0) {
                renderSongs(data.data, false, true);
                switchTab('downloaded');
            } else {
                document.getElementById('songGrid').innerHTML = '<div class="empty">📂 还没有下载歌曲</div>';
                switchTab('downloaded');
            }
        })
        .catch(() => { document.getElementById('songGrid').innerHTML = '<div class="empty">❌ 加载失败</div>'; });
}

// ==================== 收藏 ====================
function toggleFavorite(idx) {
    const song = currentSongs[idx];
    if (!song) return;
    const index = favorites.findIndex(s => s.song === song.song && s.singer === song.singer);
    if (index > -1) favorites.splice(index, 1);
    else favorites.push({song: song.song, singer: song.singer});
    saveFavorites();
    showToast(index > -1 ? '已取消收藏' : '❤️ 已收藏');
    if (currentTab === 'favorites') showFavorites();
    else renderSongs(currentSongs);
}

function showFavorites() {
    if (favorites.length === 0) {
        document.getElementById('songGrid').innerHTML = '<div class="empty">💔 还没有收藏歌曲</div>';
        switchTab('favorites');
        return;
    }
    renderSongs(favorites, false);
    switchTab('favorites');
}

// ==================== 播放 ====================
function playSong(idx) {
    if (idx < 0 || idx >= currentSongs.length) return;
    const song = currentSongs[idx];
    if (!song) return;
    
    currentPlayIndex = idx;
    
    document.getElementById('playerName').textContent = song.song;
    document.getElementById('playerSinger').textContent = song.singer;
    
    document.querySelectorAll('.song-card').forEach(el => el.classList.remove('playing'));
    const el = document.getElementById(`card-${idx}`);
    if (el) el.classList.add('playing');
    
    let playUrl = '';
    if (song.mid && song.mid.startsWith('local_')) {
        playUrl = `/api/local/${encodeURIComponent(song.file)}`;
    } else {
        playUrl = `/api/stream/${encodeURIComponent(song.mid || '')}`;
    }
    
    if (!audioElement) {
        audioElement = new Audio();
        setupAudioEvents();
    }
    
    audioElement.src = playUrl;
    audioElement.load();
    audioElement.play();
    isPlaying = true;
    document.getElementById('player').style.display = 'block';
    document.getElementById('playPauseBtn').textContent = '⏸️';
    showToast(`▶️ 正在播放: ${song.song}`);
}

function togglePlay() {
    if (!audioElement) return;
    if (audioElement.paused) {
        audioElement.play();
        isPlaying = true;
        document.getElementById('playPauseBtn').textContent = '⏸️';
    } else {
        audioElement.pause();
        isPlaying = false;
        document.getElementById('playPauseBtn').textContent = '▶️';
    }
}

function closePlayer() {
    document.getElementById('player').style.display = 'none';
    if (audioElement) { audioElement.pause(); audioElement.src = ''; }
    isPlaying = false;
}

function seekTo(e) {
    const bar = document.getElementById('progressBarPlayer');
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    if (audioElement && audioElement.duration) {
        audioElement.currentTime = pct * audioElement.duration;
    }
}

function toggleMode() {
    const modes = ['order', 'single', 'random'];
    const labels = ['🔁 列表', '🔂 单曲', '🎲 随机'];
    const idx = modes.indexOf(playMode);
    playMode = modes[(idx + 1) % 3];
    document.getElementById('modeBtn').textContent = labels[modes.indexOf(playMode)];
    showToast('播放模式: ' + labels[modes.indexOf(playMode)]);
}

function getNextIndex() {
    if (!currentSongs.length) return -1;
    if (playMode === 'single') return currentPlayIndex;
    if (playMode === 'random') {
        let newIndex;
        do { newIndex = Math.floor(Math.random() * currentSongs.length); } 
        while (currentSongs.length > 1 && newIndex === currentPlayIndex);
        return newIndex;
    }
    let next = currentPlayIndex + 1;
    if (next >= currentSongs.length) next = 0;
    return next;
}

function setupAudioEvents() {
    if (!audioElement) return;
    
    audioElement.ontimeupdate = function() {
        if (audioElement.duration) {
            document.getElementById('progressInner').style.width = (audioElement.currentTime / audioElement.duration * 100) + '%';
            document.getElementById('currentTime').textContent = formatTime(audioElement.currentTime);
            document.getElementById('totalTime').textContent = formatTime(audioElement.duration);
        }
    };
    
    audioElement.onended = function() {
        if (playMode === 'single') {
            audioElement.currentTime = 0;
            audioElement.play();
        } else {
            const nextIdx = getNextIndex();
            if (nextIdx !== currentPlayIndex) playSong(nextIdx);
        }
    };
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
    
    let downloadUrl = '';
    if (song.mid && song.mid.startsWith('local_')) {
        downloadUrl = `/api/local/${encodeURIComponent(song.file)}?download=true`;
    } else {
        downloadUrl = `/api/download/direct/${encodeURIComponent(song.mid || '')}?name=${encodeURIComponent(song.song + ' - ' + song.singer)}`;
    }
    
    window.open(downloadUrl, '_blank');
    showToast(`⬇️ 正在下载: ${song.song}`);
    setTimeout(() => showToast(`✅ 下载完成: ${song.song}`), 5000);
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
    response = proxy_stream(song_url)
    if response:
        return response
    return jsonify({'code': 404, 'message': '播放失败'}), 404

@app.route('/api/download/direct/<mid>')
def download_direct(mid):
    song_name = request.args.get('name', 'music')
    song_url = get_song_url(mid)
    if not song_url:
        return jsonify({'code': 404, 'message': '无法获取下载链接'}), 404
    if mid.startswith('preset_'):
        return jsonify({'code': 404, 'message': '预设歌曲暂无下载源'}), 404
    filename = f"{song_name}.mp3"
    response = proxy_stream(song_url, as_attachment=True, filename=filename)
    if response:
        return response
    return jsonify({'code': 404, 'message': '下载失败'}), 404

@app.route('/api/local/<path:filename>')
def play_local(filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'code': 404, 'message': '文件不存在'}), 404
    if request.args.get('download'):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return send_file(filepath, mimetype='audio/mpeg')

@app.route('/api/downloaded')
def get_downloaded():
    songs = get_downloaded_songs()
    return jsonify({'code': 200, 'data': songs})

@app.route('/api/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'code': 400, 'message': '请输入关键词'})
    results = search_music(keyword)
    return jsonify({'code': 200, 'data': results})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                  lyric=get_random_lyric(),
                                  preset_songs=PRESET_SONGS)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print("  🎵 最酷音乐下歌精灵 v2.1")
    print("="*60)
    print(f"  🌐 访问地址: http://localhost:{port}")
    print("  🎧 点击卡片立即播放 · 直接下载")
    print("  📂 已下载歌曲列表")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
