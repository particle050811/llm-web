# backend/app.py
import os
from backend.app_setup import create_app
from backend.routes import register_routes

# 创建 Flask 应用实例
app = create_app()

# 注册路由
register_routes(app)

# === 环境变量验证和代理设置 (移到这里或启动脚本更合适) ===
# 可以在这里根据需要设置代理，或者在运行脚本中设置环境变量
# 例如:
# if os.environ.get('APP_ENV') == 'local':
#     proxy_url = 'http://127.0.0.1:7890' # 或者从配置读取
#     os.environ['HTTP_PROXY'] = proxy_url
#     os.environ['HTTPS_PROXY'] = proxy_url
#     print(f"本地环境，已设置代理: {proxy_url}")
# else:
#     print("非本地环境，跳过代理设置")
# === 环境验证和代理设置结束 ===


if __name__ == '__main__':
    # 注意：debug=True 在生产环境中应设为 False
    # host='::' 监听 IPv6 和 IPv4
    app.run(host='::', port=5000, debug=False)
