# backend/llm_service.py
import openai
import json
from backend.config import get_model_config # 从 config 模块导入模型配置获取函数

def query_llm(model_name, prompt, msg):
    """
    使用给定的提示和消息查询指定的 LLM 模型。

    Args:
        model_name (str): 要查询的模型名称。
        prompt (str): 系统提示。
        msg (str): 用户消息。

    Returns:
        generator or tuple: 成功时返回一个流式生成器，
                           失败时返回一个包含错误信息的元组 (dict, status_code)。
    """
    try:
        md = get_model_config(model_name)
        if not md:
            print(f"错误: 未找到模型 '{model_name}' 的配置。")
            return {"error": f"模型配置未找到: {model_name}"}, 400 # 返回错误字典和状态码

        # 判断是否需要 JSON 输出
        # 默认根据 prompt 判断
        response_format = {'type': 'json_object'} if 'json' in prompt else None
        # 如果模型配置中显式禁用 json_format，则覆盖默认设置
        if md.get('json_format') is False:
            response_format = None

        client = openai.OpenAI(api_key=md['api_key'], base_url=md['base_url'])
        response = client.chat.completions.create(
            model=md['model'],
            messages=[
                {"role": "user", "content": prompt},
                {"role": "user", "content": msg}
            ],
            stream=True,
            response_format=response_format
        )

        # 生成器函数，用于流式返回
        def generate():
            try:
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta: # 确保 delta 不为 None
                        # 将 delta 对象转换为 JSON 字符串并返回
                        yield json.dumps(delta.model_dump()) + '\n'
            except Exception as e:
                print(f"流式生成过程中出错: {e}")
                # 在流中产生错误信息
                yield json.dumps({"error": "流式生成过程中出错"}) + '\n'

        return generate() # 返回生成器

    except openai.OpenAIError as e:
        print(f"OpenAI API 错误: {e}")
        return {"error": "AI模型API调用失败"}, 500 # 返回错误字典和状态码
    except KeyError as e:
        print(f"配置错误: 模型 '{model_name}' 配置中缺少键 {e}")
        return {"error": f"模型 '{model_name}' 配置不完整"}, 500 # 返回错误字典和状态码
    except Exception as e:
        print(f"查询 LLM 时发生未知错误: {e}")
        return {"error": "查询 LLM 时发生未知错误"}, 500 # 返回错误字典和状态码