from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import openai
import json
import base64
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
        
        #response_format = None

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
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    yield delta.reasoning_content
                elif hasattr(delta, 'content') and delta.content:
                    yield delta.content

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
    prompt = base64.b64decode(prompt).decode('utf-8')
    msg = data.get('msg')
    msg = base64.b64decode(msg).decode('utf-8')

    if model in model_list:
      return Response(stream_with_context(query(model, prompt, msg)))
    else:
        return jsonify({'error': '不支持的模型'}), 400

# 自定义错误处理


if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')