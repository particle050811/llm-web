# backend/app.py
import os
from backend.app_setup import create_app
from backend.routes import register_routes

# 创建 Flask 应用实例
app = create_app()

# 注册路由
register_routes(app)

# === 环境变量验证和代理设置 ===
# 在这里根据 APP_ENV 环境变量设置代理
proxy_url = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')

if os.environ.get('APP_ENV') == 'local' and not proxy_url:
    # 如果是本地环境且未通过环境变量设置代理，则使用默认本地代理
    proxy_url = 'http://127.0.0.1:7890' # 可以从配置读取或使用其他默认值
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    print(f"本地环境，已设置默认代理: {proxy_url}")
elif proxy_url:
    print(f"已通过环境变量设置代理: {proxy_url}")
else:
    print("未设置代理")
# === 环境验证和代理设置结束 ===


if __name__ == '__main__':
    # 注意：debug=True 在生产环境中应设为 False
    # host='::' 监听 IPv6 和 IPv4
    app.run(host='::', port=5000, debug=False)
