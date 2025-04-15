# backend/app_setup.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from backend.config import get_script_dir # 从 config 模块导入

# 获取脚本目录
script_dir = get_script_dir()

# 本地音频文件存储配置
AUDIO_FOLDER = os.path.join(script_dir, 'audio_files')

if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
    print(f"创建本地音频存储目录: {AUDIO_FOLDER}")

def create_app():
    """创建并配置 Flask 应用实例"""
    app = Flask(__name__)
    CORS(app)  # 启用 CORS

    # 配置 Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["300 per hour"],  # 默认限制
        storage_uri="memory://",
    )

    # 注册速率限制错误处理程序
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        print("Rate limit exceeded handler called")
        return jsonify(
            error=f"请求频率过高，已超出限制：{e.description}，请稍后重试。"
        ), 429

    # 将 limiter 附加到 app 对象，以便在其他模块中访问
    app.limiter = limiter

    # 将 AUDIO_FOLDER 附加到 app 配置，以便在其他模块中访问
    app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
    app.config['SCRIPT_DIR'] = script_dir # 也将 script_dir 加入配置

    return app

# 创建 app 实例 (可以在主 app.py 中导入并使用)
# app = create_app()
# limiter = app.limiter # 获取 limiter 实例