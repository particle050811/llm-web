from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json
import base64

app = Flask(__name__)
CORS(app)  # 启用 CORS，允许跨域请求

# 加载配置文件
with open('../llm-web.json', 'r', encoding='utf-8') as file:
    cg = json.load(file)

# 将模型列表转换为列表形式
model_list = list(cg.keys())

def query(model, prompt, msg):
    try:
        md = cg[model]
        client = openai.OpenAI(api_key=md['api_key'], base_url=md['base_url'])
        response = client.chat.completions.create(
            model=md['model'],
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": msg}
            ],
            response_format={'type': 'json_object'}
        )
        reply = response.choices[0].message.content
        print(reply)
        return reply

    except openai.OpenAIError as e:
        print(f"OpenAI API 错误: {e}")
        return {"error": "AI模型API调用失败"}

    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return {"error": "响应格式错误"}

    except Exception as e:
        print(f"未知错误: {e}")
        return {"error": "发生未知错误"}

@app.route('/fetchModels', methods=['GET'])
def get_model_list():
    # 返回模型列表，确保是可序列化的对象
    reply=jsonify(model_list)
    print(reply)
    return reply

@app.route('/query', methods=['POST'])
def query_llm():
    data = request.get_json()
    model = data.get('model')
    prompt = data.get('prompt')
    prompt = base64.b64decode(prompt).decode('utf-8')
    msg = data.get('msg')
    msg = base64.b64decode(msg).decode('utf-8')

    if model in model_list:
        check_result = query(model, prompt, msg)
        return jsonify(check_result)
    else:
        return jsonify({'error': '不支持的模型'}), 400

if __name__ == '__main__':
    app.run(debug=True)