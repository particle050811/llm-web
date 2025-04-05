from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import openai
import json
import os # Added for local file operations
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
import requests

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

# 本地音频文件存储配置
AUDIO_FOLDER = 'audio_files'
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
    print(f"创建本地音频存储目录: {AUDIO_FOLDER}")

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

def query(model_name, prompt, msg):
    try:
        md = cg[model_name]
        
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
    model_name = data.get('model')
    prompt = data.get('prompt')
    msg = data.get('msg')

    if model_name in model_list:
        return Response(stream_with_context(query(model_name, prompt, msg)))
    else:
        return jsonify({'error': '不支持的模型'}), 400

# 自定义错误处理


# --- OSS 相关代码已移除 ---

@app.route('/api/generate-audio-url', methods=['GET'])
def generate_audio_url():
    # 不再需要检查 OSS 服务
    try:
        content_type = request.args.get('contentType', 'audio/mpeg')
        file_hash = request.args.get('fileHash')

        if not file_hash:
            return jsonify({"error": "缺少文件哈希参数"}), 400

        # 根据 content_type 推断文件扩展名 (逻辑保留)
        extension = '.mp3'
        if '/' in content_type:
            mime_suffix = content_type.split('/')[-1]
            if mime_suffix == 'wav': extension = '.wav'
            elif mime_suffix == 'ogg': extension = '.ogg'
            elif mime_suffix == 'aac': extension = '.aac'
            # 可以根据需要添加更多格式

        # 构建本地文件名 (不包含 audio/ 前缀，直接存放在 AUDIO_FOLDER 下)
        object_name = f"{file_hash}{extension}"
        local_path = os.path.join(AUDIO_FOLDER, object_name)

        # 检查本地文件是否存在
        if os.path.exists(local_path):
            print(f"本地文件已存在: {local_path}")
            return jsonify({
                "status": "exists",
                "object_name": object_name # 返回文件名供后续使用
            }), 200
        else:
            print(f"本地文件不存在，准备上传: {object_name}")
            # 不再返回 URL，只返回状态和 object_name
            return jsonify({
                "status": "new",
                "object_name": object_name # 返回文件名供上传接口使用
            }), 200
    except Exception as e:
        print(f"检查本地音频文件状态时出错: {e}")
        return jsonify({"error": f"检查文件状态失败: {str(e)}"}), 500
    


# 新增：处理文件上传的接口
@app.route('/api/upload-audio', methods=['POST'])
@limiter.limit("120 per hour") # 上传接口限流可以适当放宽
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "缺少文件部分"}), 400
    file = request.files['file']
    object_name = request.form.get('object_name') # 从表单获取 object_name

    if not object_name:
         return jsonify({"error": "缺少 object_name 参数"}), 400

    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    try:
        local_path = os.path.join(AUDIO_FOLDER, object_name)
        file.save(local_path)
        print(f"文件已保存到本地: {local_path}")
        return jsonify({"message": "文件上传成功", "object_name": object_name}), 200
    except Exception as e:
        print(f"保存上传文件时出错: {e}")
        return jsonify({"error": f"保存文件失败: {str(e)}"}), 500


# 新增：封装 AI 处理逻辑的内部函数
def _process_audio_with_ai(model_config, audio_data_base64, audio_format, audio_prompt_text):
    client = openai.OpenAI(api_key=model_config['api_key'], base_url=model_config['base_url'])
    response = client.chat.completions.create(
        model=model_config['model'],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_data_base64,
                            "format": audio_format
                        }
                    },
                    {"type": "text", "text": audio_prompt_text}
                ]
            }
        ],
        modalities=["text"],
        stream=True
    )
    print("转录 API 调用完成。")

    # 提取结果 (处理流式响应)
    print(f"识别结果: ")
    def generate():
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
                print(delta, end='', flush=True)

    return generate()

import os

@app.route('/api/transcribe-audio', methods=['POST'])
@limiter.limit("60 per hour") # 对识别接口单独限流
def transcribe_audio_openai_compatible():
    # 不再需要检查 OSS 服务
    data = request.get_json()
    object_name = data.get('object_name') # 这个 object_name 现在是本地文件名
    model_name = data.get('model')

    if not object_name:
        return jsonify({"error": "缺少 object_name 参数"}), 400

    try:
        # 从本地文件系统读取文件内容
        local_path = os.path.join(AUDIO_FOLDER, object_name)
        if not os.path.exists(local_path):
             return jsonify({"error": f"本地文件不存在: {object_name}"}), 404

        try:
            with open(local_path, 'rb') as f:
                file_content = f.read()
            # 从 object_name 推断文件格式
            file_format = object_name.split('.')[-1] if '.' in object_name else "mp3"
            md = cg[model_name] # 获取模型配置
        except Exception as e:
            print(f"读取本地文件时出错 ({local_path}): {e}")
            return jsonify({"error": f"读取本地文件失败: {str(e)}"}), 500

        # 读取 audio prompt
        try:
            with open('audio_prompt.txt', 'r', encoding='utf-8') as file:
                audio_prompt = file.read()
        except FileNotFoundError:
            print("警告: audio_prompt.txt 未找到，将使用空提示。")
            audio_prompt = ""
        except Exception as e:
             print(f"读取 audio_prompt.txt 时出错: {e}")
             return jsonify({"error": f"读取音频提示失败: {str(e)}"}), 500

        # Base64 编码
        import base64
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        base64_audio = base64.b64encode(file_content).decode('utf-8')

        # === 环境变量验证和代理设置 ===
        print(f"当前环境变量APP_ENV: {os.environ.get('APP_ENV')}")
        if os.environ.get('APP_ENV') == 'local':
            proxy_url = 'http://127.0.0.1:7890' # 或者从配置读取
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            print(f"本地环境，已设置代理: {proxy_url}")
        else:
            print("非本地环境，跳过代理设置")
        # === 环境验证和代理设置结束 ===

        # 调用新的内部函数处理 AI 逻辑
        generator = _process_audio_with_ai(md, base64_audio, file_format, audio_prompt)
        return Response(stream_with_context(generator))

    except requests.exceptions.RequestException as e:
        print(f"下载音频文件时出错 ({object_name}): {e}")
        return jsonify({"error": f"无法下载音频文件: {e}"}), 500
    except openai.APIConnectionError as e:
        # 获取模型配置以在错误消息中使用
        md_for_error = cg.get(model_name, {}) # 安全获取，避免KeyError
        print(f"无法连接到 gemini API ({md_for_error.get('model', model_name)}): {e}")
        return jsonify({"error": f"无法连接到 API: {e}"}), 503
    except openai.RateLimitError as e:
        md_for_error = cg.get(model_name, {}) # 安全获取
        print(f"gemini API 请求频率受限 ({md_for_error.get('model', model_name)}): {e}，考虑换用更廉价的模型。")
        return jsonify({"error": f"API 请求频率过高: {e}"}), 429
    except openai.APIStatusError as e:
        md_for_error = cg.get(model_name, {}) # 安全获取
        print(f"gemini API 返回错误状态 ({md_for_error.get('model', model_name)}): {e.status_code} - {e.response}")
        return jsonify({"error": f"API 返回错误: {e.status_code} {e.message}"}), e.status_code
    except Exception as e:
        print(f"处理音频识别时发生未知错误 ({object_name}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"处理音频识别失败: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(host='::', port=5000, debug=False)  # 关键改动！监听所有 IPv4/IPv6 接口
