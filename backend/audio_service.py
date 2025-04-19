# backend/audio_service.py
import os
import time
import base64
import json
import openai
import requests
import httpx # 导入 httpx 用于代理
from flask import jsonify, Response, stream_with_context
from backend.config import get_model_config, get_script_dir, get_gemini_config # 导入配置

# --- 音频文件处理逻辑 ---

def check_audio_file_status(audio_folder, content_type, file_hash):
    """检查本地音频文件是否存在"""
    if not file_hash:
        return {"error": "缺少文件哈希参数"}, 400

    # 根据 content_type 推断文件扩展名
    extension = '.mp3'
    if '/' in content_type:
        mime_suffix = content_type.split('/')[-1]
        if mime_suffix == 'wav': extension = '.wav'
        elif mime_suffix == 'ogg': extension = '.ogg'
        elif mime_suffix == 'aac': extension = '.aac'
        # 可以根据需要添加更多格式

    object_name = f"{file_hash}{extension}"
    local_path = os.path.join(audio_folder, object_name)

    try:
        if os.path.exists(local_path):
            print(f"本地文件已存在: {local_path}")
            return {
                "status": "exists",
                "object_name": object_name # 返回文件名供后续使用
            }, 200
        else:
            print(f"本地文件不存在，准备上传: {object_name}")
            return {
                "status": "new",
                "object_name": object_name # 返回文件名供上传接口使用
            }, 200
    except Exception as e:
        print(f"检查本地音频文件状态时出错: {e}")
        return {"error": f"检查文件状态失败: {str(e)}"}, 500

def save_uploaded_audio(audio_folder, file, object_name):
    """保存上传的音频文件到本地"""
    if not file:
        return {"error": "缺少文件部分"}, 400
    if not object_name:
         return {"error": "缺少 object_name 参数"}, 400
    if file.filename == '':
        return {"error": "未选择文件"}, 400

    try:
        local_path = os.path.join(audio_folder, object_name)
        file.save(local_path)
        print(f"文件已保存到本地: {local_path}")
        return {"message": "文件上传成功", "object_name": object_name}, 200
    except Exception as e:
        print(f"保存上传文件时出错: {e}")
        return {"error": f"保存文件失败: {str(e)}"}, 500

# --- AI 音频处理逻辑 ---

def _process_audio_with_ai(model_config, audio_data_base64, audio_format, audio_prompt_text):
    """内部函数：使用 AI 模型处理音频数据"""
    try:
        client = openai.OpenAI(
            api_key=model_config['api_key'],
            base_url=model_config['base_url']
        )
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
            modalities=["text"], # 明确指定模态
            stream=True
        )
        print("转录 API 调用完成。")

        # 生成器函数，用于流式返回
        def generate():
            try:
                print(f"识别结果: ")
                for chunk in response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                        print(delta, end='', flush=True) # 实时打印到控制台
                print("\n--- 识别结束 ---") # 标记流结束
            except Exception as e:
                print(f"\n音频流处理中发生错误: {e}")
                yield f"Error in stream: {e}" # 在流中返回错误信息

        return generate() # 返回生成器

    except openai.APIConnectionError as e:
        print(f"无法连接到 API ({model_config.get('model', '未知模型')}): {e}")
        raise ConnectionError(f"无法连接到 API: {e}") # 抛出特定异常
    except openai.RateLimitError as e:
        print(f"API 请求频率受限 ({model_config.get('model', '未知模型')}): {e}")
        raise ValueError(f"API 请求频率过高: {e}") # 抛出特定异常
    except openai.APIStatusError as e:
        print(f"API 返回错误状态 ({model_config.get('model', '未知模型')}): {e.status_code} - {e.response}")
        raise RuntimeError(f"API 返回错误: {e.status_code} {e.message}") # 抛出特定异常
    except Exception as e:
        print(f"调用 AI 处理音频时发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"AI 处理音频失败: {str(e)}") # 抛出通用异常


def transcribe_audio(audio_folder, script_dir, object_name, model_name):
    """处理音频转录请求"""
    if not object_name:
        return jsonify({"error": "缺少 object_name 参数"}), 400

    local_path = os.path.join(audio_folder, object_name)
    file_content = None

    # 尝试读取本地文件，增加重试逻辑
    for attempt in range(3):
        try:
            if not os.path.exists(local_path):
                print(f"尝试 {attempt + 1}/3: 文件 {local_path} 尚不存在，等待...")
                time.sleep(0.2 * (attempt + 1))
                continue
            with open(local_path, 'rb') as f:
                file_content = f.read()
                print(f"文件 {local_path} 读取成功。")
                break
        except PermissionError as e:
            print(f"尝试 {attempt + 1}/3: 读取文件 {local_path} 时遇到权限错误: {e}，等待...")
            time.sleep(0.2 * (attempt + 1))
        except Exception as e:
            print(f"尝试 {attempt + 1}/3: 读取本地文件时发生意外错误 ({local_path}): {e}")
            time.sleep(0.2 * (attempt + 1))

    if file_content is None:
        print(f"尝试多次后仍无法读取文件: {local_path}")
        return jsonify({"error": f"无法读取本地文件: {object_name} (尝试3次后失败)"}), 500

    try:
        # 推断格式和获取模型配置
        file_format = object_name.split('.')[-1].lower() if '.' in object_name else "mp3"
        md = get_gemini_config(model_name)
        if not md:
             return jsonify({"error": f"无效的模型名称: {model_name}"}), 400

        # 读取 audio prompt
        audio_prompt_path = os.path.join(script_dir, 'audio_prompt.txt')
        try:
            with open(audio_prompt_path, 'r', encoding='utf-8') as file:
                audio_prompt = file.read()
        except FileNotFoundError:
            print(f"警告: {audio_prompt_path} 未找到，将使用空提示。")
            audio_prompt = ""
        except Exception as e:
             print(f"读取 audio_prompt.txt 时出错: {e}")
             return jsonify({"error": f"读取音频提示失败: {str(e)}"}), 500

        # Base64 编码
        base64_audio = base64.b64encode(file_content).decode('utf-8')

        # 调用内部函数处理 AI 逻辑
        generator = _process_audio_with_ai(md, base64_audio, file_format, audio_prompt)
        # 直接返回 Response 对象，包含流式生成器
        return Response(stream_with_context(generator))

    except (ConnectionError, ValueError, RuntimeError) as e: # 捕获内部函数抛出的特定异常
        # 这些是 AI 调用相关的错误
        status_code = 503 if isinstance(e, ConnectionError) else \
                      429 if isinstance(e, ValueError) else 500
        return jsonify({"error": str(e)}), status_code
    except KeyError:
         return jsonify({"error": f"无效的模型名称: {model_name}"}), 400
    except Exception as e:
        print(f"处理音频识别时发生未知错误 ({object_name}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"处理音频识别失败: {str(e)}"}), 500


# --- 举报信息分析逻辑 ---

def analyze_report_info(script_dir, object_name, transcription_text):
    """分析举报信息"""
    if not object_name:
        return jsonify({"error": "缺少 object_name 参数"}), 400
    if not transcription_text:
        return jsonify({"error": "缺少 transcription_text 参数"}), 400

    # 选择默认模型 (可以考虑从配置读取)
    model_name = "gemini-2.5-flash-preview-04-17"
    md = get_gemini_config(model_name)

    if not md:
        return jsonify({"error": f"模型配置未找到: {model_name}"}), 500

    try:
        # 从文件读取提示词模板
        report_prompt_path = os.path.join(script_dir, 'report_prompt.txt')
        with open(report_prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 格式化提示词
        prompt = prompt_template.format(
            transcription_text=transcription_text,
            object_name=object_name
        )

        client = openai.OpenAI(
            api_key=md['api_key'],
            base_url=md['base_url']
        )
        response = client.chat.completions.create(
            model=md['model'],
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=False # 分析接口不需要流式
        )

        content = response.choices[0].message.content

        # 解析JSON
        try:
            # 预处理，去除markdown代码块标记
            content = content.strip()
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip().rstrip()
                if content.endswith("```"):
                    content = content[:-3].strip()
            result = json.loads(content)
        except json.JSONDecodeError:
            print(f"模型响应内容 (非JSON): {content}")
            return jsonify({"error": "模型未返回有效JSON", "raw_response": content}), 500

        # 确保所有字段存在
        for key in ["school", "method", "phone", "time"]:
            result.setdefault(key, "") # 使用 setdefault 更简洁

        return jsonify(result) # 返回 JSON 响应

    except FileNotFoundError:
        print(f"错误: 举报提示文件 {report_prompt_path} 未找到。")
        return jsonify({"error": "举报提示文件未找到"}), 500
    except openai.OpenAIError as e:
        print(f"分析举报信息时 OpenAI API 错误: {e}")
        return jsonify({"error": "AI模型API调用失败"}), 500
    except Exception as e:
        print(f"分析举报信息时出错: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"分析举报信息失败: {str(e)}"}), 500

def get_audio_file(audio_folder, object_name):
    """获取音频文件内容
    
    Args:
        audio_folder: 音频文件存储目录
        object_name: 音频文件名
        
    Returns:
        tuple: (audio_data, content_type, status_code) 或 (None, None, status_code) 如果失败
    """
    if not object_name:
        print("错误: 缺少object_name参数")
        return None, None, 400
        
    local_path = os.path.join(audio_folder, object_name)
    
    try:
        if not os.path.exists(local_path):
            print(f"错误: 文件不存在 - {local_path}")
            return None, None, 404
            
        with open(local_path, 'rb') as f:
            audio_data = f.read()
            
        extension = os.path.splitext(object_name)[1].lower()
        content_type = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac'
        }.get(extension, 'application/octet-stream')
        
        print(f"成功获取音频文件: {object_name} (类型: {content_type})")
        return audio_data, content_type, 200
        
    except PermissionError as e:
        print(f"权限错误: {e}")
        return None, None, 403
    except Exception as e:
        print(f"获取音频文件时出错: {e}")
        return None, None, 500