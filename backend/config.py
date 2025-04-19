# backend/config.py
import os
import json

# 获取当前脚本文件所在的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'ai.json')

cg = {}
model_list = []

try:
    with open(config_path, 'r', encoding='utf-8') as file:
        cg = json.load(file)
    # 将模型列表转换为列表形式 (过滤掉没有 api_key 或 base_url 的配置)
    model_list = [k for k, v in cg.items() if v.get('api_key') and v.get('base_url')]
    print(f"加载的可用模型: {model_list}")
except FileNotFoundError:
    print(f"警告: 配置文件 {config_path} 未找到。")
except json.JSONDecodeError:
    print(f"警告: 配置文件 {config_path} 格式错误。")
except Exception as e:
    print(f"加载配置文件时发生未知错误: {e}")

def get_config():
    """返回加载的配置字典"""
    return cg

def get_model_list():
    """返回可用的模型列表"""
    return model_list

def get_model_config(model_name):
    """根据模型名称获取配置"""
    return cg.get(model_name)

def get_script_dir():
    """返回脚本所在目录"""
    return script_dir

def get_gemini_config(model_name):
    model_cnt_path = os.path.join(script_dir, f'{model_name}_cnt.txt')
    api_path = os.path.join(script_dir, f'api.txt')

    if not os.path.exists(model_cnt_path):
        cnt = 0
    else:
        with open(model_cnt_path, 'rb') as f:
            cnt = int(f.read())
    with open(model_cnt_path, 'wb') as f:
        f.write(str(cnt + 1).encode())
    with open(api_path, 'r') as f:
        api_list = f.read().split('\n')
    return {
        "model": model_name,
        "api_key": api_list[cnt % len(api_list)],
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/"
    }
    pass