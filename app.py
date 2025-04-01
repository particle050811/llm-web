from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import openai
import json
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour"],  # 默认限制：每小时 300 次
    storage_uri="memory://",
)
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    print("Rate limit exceeded handler called")
    return jsonify(
        error=f"请求频率过高，已超出限制：{e.description}，请稍后重试。"
    ), 429
# 加载配置文件
with open('../llm-web.json', 'r', encoding='utf-8') as file:
    cg = json.load(file)

# 将模型列表转换为列表形式
model_list = list(cg.keys())

def query(model, prompt, msg):
    try:
        md = cg[model]
        
        # 判断是否需要 JSON 输出
        if 'json' in prompt:
            response_format = {'type': 'json_object'}
        else:
            response_format = None
        
        if "R1" in md:
            response_format = None

        client = openai.OpenAI(api_key=md['api_key'], base_url=md['base_url'])
        response = client.chat.completions.create(
            model=md['model'],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": msg}
            ],
            stream=True,
            response_format=response_format
        )

        # 生成器函数，用于流式返回
        def generate():
            for chunk in response:
                delta = chunk.choices[0].delta
                # 将delta对象转换为JSON字符串并返回
                yield json.dumps(delta.model_dump()) + '\n'

        return generate()

    except openai.OpenAIError as e:
        print(f"OpenAI API 错误: {e}")
        return jsonify({"error": "AI模型API调用失败"}), 500

    except Exception as e:
        print(f"未知错误: {e}")
        return jsonify({"error": "发生未知错误"}), 500

@app.route('/fetchModels', methods=['GET'])
def get_model_list():
    # 返回模型列表，确保是可序列化的对象
    reply=jsonify(model_list)
    print(reply)
    return reply

@app.route('/query_stream', methods=['POST'])
@limiter.limit("300 per hour") # 实际使用时可以改成 300 per hour
def query_llm_stream():
    data = request.get_json()
    model = data.get('model')
    prompt = data.get('prompt')
    msg = data.get('msg')

    if model in model_list:
        return Response(stream_with_context(query(model, prompt, msg)))
    else:
        return jsonify({'error': '不支持的模型'}), 400

# 自定义错误处理


# OSS配置
endpoint = "https://oss-cn-beijing.aliyuncs.com"
region = "cn-beijing"
bucket_name = "llm-web-mp3"

# 从环境变量获取OSS凭证
try:
    # 强制使用 V2 签名
    print("强制使用 V2 签名...")
    creds = EnvironmentVariableCredentialsProvider().get_credentials()
    if not creds or not creds.access_key_id or not creds.access_key_secret:
        raise ValueError("无法从环境变量获取 OSS_ACCESS_KEY_ID 或 OSS_ACCESS_KEY_SECRET")
    auth_v2 = oss2.Auth(creds.access_key_id, creds.access_key_secret)
    bucket = oss2.Bucket(auth_v2, endpoint, bucket_name)
    try:
        bucket.get_bucket_info()
        print("OSS V2凭证验证成功")
    except Exception as e:
        print(f"OSS V2凭证验证失败: {str(e)}")
        bucket = None

except Exception as e:
    print(f"OSS初始化失败: {str(e)}")
    print("请检查环境变量配置: OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET")
    bucket = None

@app.route('/api/generate-audio-url', methods=['GET'])
def generate_audio_url():
    if not bucket:
        return jsonify({"error": "OSS服务未正确初始化"}), 500
        
    try:
        # 生成唯一的对象名
        import time
        content_type = request.args.get('contentType', 'audio/mpeg')  # 默认为 audio/mpeg
        import random
        
        # 根据 content_type 推断文件扩展名
        extension = '.mp3'  # 默认值
        if '/' in content_type:
            mime_suffix = content_type.split('/')[-1]
            if mime_suffix == 'wav': extension = '.wav'
            elif mime_suffix == 'ogg': extension = '.ogg'
            elif mime_suffix == 'aac': extension = '.aac'
        
        object_name = f"audio/{int(time.time())}-{random.randint(1000,9999)}{extension}"
        
        # 生成预签名URL，包含 Content-Type 头部
        headers = {'Content-Type': content_type}
        url = bucket.sign_url('PUT', object_name, 300, headers=headers, slash_safe=True)
        
        return jsonify({
            "url": url,
            "object_name": object_name
        }), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"生成签名URL时出错: {e}")
        return jsonify({"error": f"生成签名URL失败: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')