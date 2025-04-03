from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import openai
import json
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
import requests
import io # 用于将 bytes 包装成文件对象
import mimetypes # 仍然需要推断文件名以帮助API

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
try:
    with open('../llm-web.json', 'r', encoding='utf-8') as file:
        cg = json.load(file)
except FileNotFoundError:
    print("警告: ../llm-web.json 配置文件未找到。")
    cg = {}
except json.JSONDecodeError:
    print("警告: ../llm-web.json 配置文件格式错误。")
    cg = {}

# 将模型列表转换为列表形式 (过滤掉没有 api_key 或 base_url 的配置)
model_list = [k for k, v in cg.items() if v.get('api_key') and v.get('base_url')]
print(f"加载的可用模型: {model_list}")

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
        content_type = request.args.get('contentType', 'audio/mpeg')  # 默认为 audio/mpeg
        file_hash = request.args.get('fileHash')
        
        if not file_hash:
            return jsonify({"error": "缺少文件哈希参数"}), 400
            
        # 根据 content_type 推断文件扩展名
        extension = '.mp3'  # 默认值
        if '/' in content_type:
            mime_suffix = content_type.split('/')[-1]
            if mime_suffix == 'wav': extension = '.wav'
            elif mime_suffix == 'ogg': extension = '.ogg'
            elif mime_suffix == 'aac': extension = '.aac'
        
        object_name = f"audio/{file_hash}{extension}"

        # 检查文件是否已存在
        if bucket.object_exists(object_name):
            return jsonify({
                "status": "exists",
                "object_name": object_name
            }), 200, {'Content-Type': 'application/json'}
        else:
            # 生成预签名URL，包含 Content-Type 头部
            headers = {'Content-Type': content_type}
            url = bucket.sign_url('PUT', object_name, 300, headers=headers, slash_safe=True)
            
            return jsonify({
                "status": "new",
                "url": url,
                "object_name": object_name
            }), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        print(f"生成签名URL时出错: {e}")
        return jsonify({"error": f"生成签名URL失败: {str(e)}"}), 500
    


@app.route('/api/transcribe-audio', methods=['POST'])
@limiter.limit("60 per hour") # 对识别接口单独限流
def transcribe_audio_openai_compatible():
    if not bucket:
        return jsonify({"error": "OSS 服务未正确初始化"}), 500

    data = request.get_json()
    object_name = data.get('object_name')
    model = data.get('model')

    if not object_name:
        return jsonify({"error": "缺少 object_name 参数"}), 400

    try:
        # 从OSS下载文件内容
        try:
            result = bucket.get_object(object_name)
            file_content = result.read()
            file_name = object_name.split('/')[-1] if '/' in object_name else object_name
            file_format = file_name.split('.')[-1] if '.' in file_name else "mp3"
            
            md = cg[model]
        except oss2.exceptions.NoSuchKey:
            return jsonify({"error": f"OSS文件不存在: {object_name}"}), 404
        except Exception as e:
            print(f"下载OSS文件时出错: {e}")
            return jsonify({"error": f"下载OSS文件失败: {str(e)}"}), 500
        client = openai.OpenAI(api_key=md['api_key'], base_url=md['base_url'])
        with open('audio_prompt.txt', 'r',encoding='utf-8') as file:
            audio_prompt=file.read()
        
        import base64
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        base64_audio = base64.b64encode(file_content).decode('utf-8')
        
        response = client.chat.completions.create(
            model=md['model'],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": base64_audio,
                                "format": file_format
                            }
                        },
                        {"type": "text", "text": audio_prompt}
                    ]
                }
            ],
            modalities=["text"],
            stream=True,
            stream_options={"include_usage": True}
        )
        print("转录 API 调用完成。")

        # 提取结果 (处理流式响应)
        print(f"识别结果: ")
        def generate():
            for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end='', flush=True)
                    yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={'Cache-Control': 'no-cache'}
        )

    except requests.exceptions.RequestException as e:
        print(f"下载音频文件时出错 ({object_name}): {e}")
        return jsonify({"error": f"无法下载音频文件: {e}"}), 500
    except openai.APIConnectionError as e:
        print(f"无法连接到 gemini API ({md['model']}): {e}")
        return jsonify({"error": f"无法连接到 API: {e}"}), 503
    except openai.RateLimitError as e:
        print(f"gemini API 请求频率受限 ({md['model']}): {e}，考虑换用更廉价的模型。")
        return jsonify({"error": f"API 请求频率过高: {e}"}), 429
    except openai.APIStatusError as e:
        print(f"gemini API 返回错误状态 ({md['model']}): {e.status_code} - {e.response}")
        return jsonify({"error": f"API 返回错误: {e.status_code} {e.message}"}), e.status_code
    except Exception as e:
        print(f"处理音频识别时发生未知错误 ({object_name}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"处理音频识别失败: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000) # 保持端口指定
