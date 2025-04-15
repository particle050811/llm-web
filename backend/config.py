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