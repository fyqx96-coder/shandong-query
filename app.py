#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string, send_file
import requests
import os
import time
import random
import threading
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import base64
import io

app = Flask(__name__)

# 下载配置
DOWNLOAD_CONFIG = {
    'max_workers': 4,
    'chunk_size': 1024 * 256,
    'timeout': 30,
    'retry_count': 3
}

# 下载任务存储
download_tasks = {}

# 歌词库
JAY_LYRICS = [
    "从前从前有个人爱你很久，但偏偏风渐渐把距离吹得好远。——《晴天》",
    "我想就这样牵着你的手不放开，爱能不能够永远单纯没有悲哀。——《简单爱》",
    "最美的不是下雨天，是曾与你躲过雨的屋檐。——《不能说的秘密》",
    "我给你的爱写在西元前，深埋在美索不达米亚平原。——《爱在西元前》",
    "雨纷纷，旧故里草木深。我听闻，你始终一个人。——《烟花易冷》",
    "天青色等烟雨，而我在等你。——《青花瓷》",
    "我一路向北，离开有你的季节。——《一路向北》",
    "你说你有点难追，想让我知难而退。——《告白气球》",
]

# 歌曲榜单
MUSIC_CHARTS = [
    {"id": "hot", "name": "🔥 热歌榜", "description": "QQ音乐热门歌曲排行榜"},
    {"id": "new", "name": "🎵 新歌榜", "description": "最新发行的歌曲榜单"},
    {"id": "pop", "name": "🌟 流行榜", "description": "当前流行音乐榜单"},
]

# 榜单歌曲数据
CHART_SONGS = {
    "hot": [
        {"song": "孤勇者", "singer": "陈奕迅", "album": "《英雄联盟:双城之战》", "mid": "001"},
        {"song": "晴天", "singer": "周杰伦", "album": "叶惠美", "mid": "002"},
        {"song": "起风了", "singer": "买辣椒也用券", "album": "起风了", "mid": "003"},
        {"song": "光年之外", "singer": "G.E.M.邓紫棋", "album": "光年之外", "mid": "004"},
        {"song": "少年", "singer": "梦然", "album": "少年", "mid": "005"},
        {"song": "星辰大海", "singer": "黄霄雲", "album": "星辰大海", "mid": "006"},
        {"song": "错位时空", "singer": "艾辰", "album": "错位时空", "mid": "007"},
        {"song": "四季予你", "singer": "程响", "album": "四季予你", "mid": "008"},
        {"song": "云与海", "singer": "阿YueYue", "album": "云与海", "mid": "009"},
        {"song": "踏山河", "singer": "是七叔呢", "album": "踏山河", "mid": "010"}
    ],
    "new": [
        {"song": "最伟大的作品", "singer": "周杰伦", "album": "最伟大的作品", "mid": "011"},
        {"song": "还在流浪", "singer": "周杰伦", "album": "最伟大的作品", "mid": "012"},
        {"song": "粉色海洋", "singer": "周杰伦", "album": "最伟大的作品", "mid": "013"},
        {"song": "红颜如霜", "singer": "周杰伦", "album": "最伟大的作品", "mid": "014"}
    ],
    "pop": [
        {"song": "向云端", "singer": "小霞", "album": "向云端", "mid": "015"},
        {"song": "笼", "singer": "张碧晨", "album": "消失的她", "mid": "016"},
        {"song": "爱人错过", "singer": "告五人", "album": "爱人错过", "mid": "017"}
    ]
}

def get_random_lyric():
    return random.choice(JAY_LYRICS)

def search_music(keyword):
    """搜索音乐"""
    try:
        url = f"https://api.vkeys.cn/v2/music/tencent?word={keyword}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['code'] != 200 or not data['data']:
            return []
        
        results = []
        seen = set()
        for song in data['data']:
            key = (song['song'], song['singer'])
            if key not in seen:
                seen.add(key)
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
    """获取歌曲下载链接"""
    try:
        url = f"https://api.vkeys.cn/v2/music/tencent?mid={mid}&quality=8"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data['code'] == 200 and data.get('data'):
            return data['data'].get('url')
        return None
    except Exception as e:
        print(f"获取下载链接失败: {e}")
        return None

def download_song_task(task_id, song):
    """后台下载任务"""
    try:
        download_tasks[task_id] = {'status': 'downloading', 'progress': 0, 'song': song['song']}
        
        song_url = get_song_url(song['mid'])
        if not song_url:
            download_tasks[task_id] = {'status': 'failed', 'error': '无法获取下载链接'}
            return
        
        # 创建下载目录
        download_dir = "醉酷音乐"
        os.makedirs(download_dir, exist_ok=True)
        
        safe_singer = re.sub(r'[<>:"/\\|?*]', '_', song['singer'])
        safe_song = re.sub(r'[<>:"/\\|?*]', '_', song['song'])
        file_name = f"{safe_singer} - {safe_song}.mp3"
        save_path = os.path.join(download_dir, file_name)
        
        # 下载文件
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

# ==================== HTML 模板 ====================

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 音乐下歌精灵</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
        body{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);min-height:100vh;padding:20px;color:#e0e0e0}
        .container{max-width:1200px;margin:0 auto}
        .header{text-align:center;padding:30px 0}
        .header h1{font-size:42px;background:linear-gradient(135deg,#f7971e,#ffd200);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none}
        .header .sub{color:#888;font-size:16px;margin-top:8px}
        .header .lyric{color:#ffd700;font-size:14px;margin-top:10px;font-style:italic;opacity:0.7}
        
        .search-box{background:rgba(255,255,255,0.05);border-radius:16px;padding:25px;margin-bottom:25px;border:1px solid rgba(255,255,255,0.08)}
        .search-box input{width:70%;padding:14px 20px;border:none;border-radius:10px;font-size:16px;background:rgba(255,255,255,0.1);color:#fff;outline:none;transition:0.3s}
        .search-box input:focus{background:rgba(255,255,255,0.15);box-shadow:0 0 20px rgba(255,215,0,0.1)}
        .search-box input::placeholder{color:#666}
        .search-box button{padding:14px 30px;border:none;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer;transition:0.3s;margin-left:10px}
        .btn-search{background:linear-gradient(135deg,#f7971e,#ffd200);color:#1a1a2e}
        .btn-search:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(247,151,30,0.3)}
        .btn-singer{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
        .btn-singer:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(102,126,234,0.3)}
        
        .quick-buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:15px}
        .quick-buttons button{padding:8px 18px;border:none;border-radius:20px;font-size:13px;cursor:pointer;background:rgba(255,255,255,0.08);color:#aaa;transition:0.3s}
        .quick-buttons button:hover{background:rgba(255,215,0,0.2);color:#ffd700}
        
        .charts-section{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px;margin-bottom:25px}
        .chart-card{background:rgba(255,255,255,0.05);border-radius:12px;padding:18px;text-align:center;cursor:pointer;transition:0.3s;border:1px solid rgba(255,255,255,0.06)}
        .chart-card:hover{transform:translateY(-4px);background:rgba(255,255,255,0.08);border-color:rgba(255,215,0,0.3)}
        .chart-card .name{font-size:16px;font-weight:bold;color:#fff}
        .chart-card .desc{font-size:12px;color:#666;margin-top:4px}
        
        .results{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-top:20px}
        .song-card{background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;display:flex;flex-direction:column;border-left:3px solid #ffd700;transition:0.3s}
        .song-card:hover{background:rgba(255,255,255,0.08)}
        .song-card .song-name{font-size:16px;font-weight:bold;color:#fff}
        .song-card .singer{font-size:14px;color:#888;margin-top:4px}
        .song-card .album{font-size:12px;color:#555}
        .song-card .actions{margin-top:12px;display:flex;gap:8px}
        .song-card .actions button{padding:6px 16px;border:none;border-radius:8px;font-size:12px;cursor:pointer;transition:0.3s}
        .btn-download{background:#28a745;color:#fff}
        .btn-download:hover{background:#218838;transform:scale(1.05)}
        .btn-play{background:#007bff;color:#fff}
        .btn-play:hover{background:#0056b3;transform:scale(1.05)}
        
        .download-status{background:rgba(255,255,255,0.05);border-radius:12px;padding:20px;margin-top:20px;border:1px solid rgba(255,215,0,0.1)}
        .download-status .bar{width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;margin-top:10px}
        .download-status .bar-inner{height:100%;background:linear-gradient(90deg,#f7971e,#ffd200);transition:width 0.5s;border-radius:3px}
        .download-status .info{display:flex;justify-content:space-between;font-size:14px;color:#888}
        
        .status-badge{display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:bold}
        .status-downloading{background:#ffc107;color:#1a1a2e}
        .status-completed{background:#28a745;color:#fff}
        .status-failed{background:#dc3545;color:#fff}
        
        .loading{display:none;text-align:center;padding:20px}
        .loading .spinner{width:40px;height:40px;border:4px solid rgba(255,255,255,0.1);border-top:4px solid #ffd700;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto}
        @keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
        
        @media(max-width:768px){
            .search-box input{width:100%;margin-bottom:10px}
            .search-box button{width:100%;margin-left:0}
            .quick-buttons{justify-content:center}
            .results{grid-template-columns:1fr}
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🎵 音乐下歌精灵</h1>
        <div class="sub">🎧 免费下载全网歌曲 · 网页版</div>
        <div class="lyric">✨ "{{ lyric }}"</div>
    </div>
    
    <div class="search-box">
        <form id="searchForm" onsubmit="searchMusic(event)">
            <input type="text" id="keyword" placeholder="输入歌曲名或歌手名..." required>
            <button type="submit" class="btn-search">🔍 搜索</button>
            <button type="button" class="btn-singer" onclick="searchBySinger()">🎤 歌手搜索</button>
        </form>
        <div class="quick-buttons">
            <button onclick="quickSearch('周杰伦')">周杰伦</button>
            <button onclick="quickSearch('林俊杰')">林俊杰</button>
            <button onclick="quickSearch('陈奕迅')">陈奕迅</button>
            <button onclick="quickSearch('邓紫棋')">邓紫棋</button>
            <button onclick="quickSearch('薛之谦')">薛之谦</button>
            <button onclick="quickSearch('热歌')">🔥 热歌</button>
            <button onclick="loadChart('hot')">📊 榜单</button>
        </div>
    </div>
    
    <div class="charts-section" id="chartsSection"></div>
    
    <div id="loading" class="loading"><div class="spinner"></div><p style="color:#888;margin-top:10px">搜索中...</p></div>
    
    <div id="results" class="results"></div>
    
    <div id="downloadStatus" class="download-status" style="display:none">
        <div class="info"><span id="downloadInfo">准备下载...</span><span id="downloadProgress">0%</span></div>
        <div class="bar"><div class="bar-inner" id="progressBar" style="width:0%"></div></div>
        <div style="margin-top:10px;font-size:13px;color:#888" id="downloadDetail"></div>
    </div>
</div>

<script>
let currentResults = [];
let downloadTaskId = null;
let statusCheckInterval = null;

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function renderResults(results) {
    const container = document.getElementById('results');
    if (!results || results.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:40px;color:#666">🎵 没有找到相关歌曲</div>';
        return;
    }
    
    container.innerHTML = results.map((song, idx) => `
        <div class="song-card">
            <div class="song-name">${song.song}</div>
            <div class="singer">🎤 ${song.singer}</div>
            <div class="album">💿 ${song.album || '未知'}</div>
            <div class="actions">
                <button class="btn-download" onclick="downloadSong(${idx})">⬇️ 下载</button>
            </div>
        </div>
    `).join('');
    currentResults = results;
}

function searchMusic(e) {
    e.preventDefault();
    const keyword = document.getElementById('keyword').value.trim();
    if (!keyword) return;
    doSearch(keyword);
}

function quickSearch(keyword) {
    document.getElementById('keyword').value = keyword;
    doSearch(keyword);
}

function searchBySinger() {
    const singer = prompt('请输入歌手名称：');
    if (singer && singer.trim()) {
        document.getElementById('keyword').value = singer;
        doSearch(singer);
    }
}

function doSearch(keyword) {
    showLoading(true);
    document.getElementById('results').innerHTML = '';
    
    fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            showLoading(false);
            if (data.code === 200) {
                renderResults(data.data);
            } else {
                document.getElementById('results').innerHTML = `<div style="text-align:center;padding:40px;color:#666">${data.message || '搜索失败'}</div>`;
            }
        })
        .catch(() => {
            showLoading(false);
            document.getElementById('results').innerHTML = '<div style="text-align:center;padding:40px;color:#dc3545">❌ 网络错误，请重试</div>';
        });
}

function downloadSong(idx) {
    const song = currentResults[idx];
    if (!song) return;
    
    document.getElementById('downloadStatus').style.display = 'block';
    document.getElementById('downloadInfo').textContent = `⬇️ 正在下载: ${song.song} - ${song.singer}`;
    document.getElementById('downloadProgress').textContent = '0%';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('downloadDetail').textContent = '⏳ 准备下载...';
    
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
        }
    })
    .catch(() => {
        document.getElementById('downloadDetail').textContent = '❌ 下载请求失败';
    });
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
                        📁 文件已保存: ${data.file}
                        <br>
                        <a href="/api/download/file/${downloadTaskId}" target="_blank" style="color:#ffd700;">🎧 点击播放</a>
                    `;
                } else if (data.status === 'downloading') {
                    document.getElementById('downloadProgress').textContent = data.progress + '%';
                    document.getElementById('progressBar').style.width = data.progress + '%';
                    document.getElementById('downloadDetail').textContent = `⏳ 下载中... ${data.progress}%`;
                } else if (data.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    document.getElementById('downloadInfo').textContent = '❌ 下载失败';
                    document.getElementById('downloadDetail').textContent = '错误: ' + (data.error || '未知错误');
                }
            })
            .catch(() => {});
    }, 1000);
}

function loadChart(chartId) {
    showLoading(true);
    fetch(`/api/chart/${chartId}`)
        .then(res => res.json())
        .then(data => {
            showLoading(false);
            if (data.code === 200) {
                renderResults(data.data);
                document.getElementById('keyword').value = '📊 ' + data.name;
            }
        })
        .catch(() => {
            showLoading(false);
        });
}

// 加载榜单按钮
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/charts')
        .then(res => res.json())
        .then(data => {
            const section = document.getElementById('chartsSection');
            if (data.code === 200) {
                section.innerHTML = data.data.map(chart => `
                    <div class="chart-card" onclick="loadChart('${chart.id}')">
                        <div class="name">${chart.name}</div>
                        <div class="desc">${chart.description}</div>
                    </div>
                `).join('');
            }
        });
});
</script>
</body>
</html>
'''

# ==================== Flask 路由 ====================

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, lyric=get_random_lyric())

@app.route('/api/search')
def search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'code': 400, 'message': '请输入关键词'})
    
    results = search_music(keyword)
    return jsonify({'code': 200, 'data': results})

@app.route('/api/charts')
def get_charts():
    return jsonify({'code': 200, 'data': MUSIC_CHARTS})

@app.route('/api/chart/<chart_id>')
def get_chart(chart_id):
    songs = CHART_SONGS.get(chart_id, [])
    chart_name = next((c['name'] for c in MUSIC_CHARTS if c['id'] == chart_id), '榜单')
    return jsonify({'code': 200, 'data': songs, 'name': chart_name})

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
    # 创建下载目录
    os.makedirs('醉酷音乐', exist_ok=True)
    print(f"\n{'='*60}")
    print("  🎵 音乐下歌精灵 网页版启动成功!")
    print("="*60)
    print(f"  🌐 访问地址: http://localhost:{port}")
    print("  🎧 搜索歌曲、查看榜单、一键下载")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
