# backend/routes.py
from flask import request, jsonify, Response, stream_with_context, current_app
from backend.config import get_model_list as config_get_model_list # 重命名以避免冲突
from backend.llm_service import query_llm
from backend.database_service import save_report_data
from backend.audio_service import (
    check_audio_file_status,
    save_uploaded_audio,
    transcribe_audio,
    analyze_report_info
)

def register_routes(app):
    """在 Flask 应用实例上注册路由"""

    limiter = app.limiter # 从 app 对象获取 limiter
    AUDIO_FOLDER = app.config['AUDIO_FOLDER']
    SCRIPT_DIR = app.config['SCRIPT_DIR']

    @app.route('/fetchModels', methods=['GET'])
    def get_model_list_route():
        """获取可用模型列表的路由"""
        model_list = config_get_model_list()
        print(f"返回模型列表: {model_list}")
        return jsonify(model_list)

    @app.route('/query_stream', methods=['POST'])
    @limiter.limit("300 per hour")
    def query_llm_stream_route():
        """处理流式 LLM 查询的路由"""
        data = request.get_json()
        model_name = data.get('model')
        prompt = data.get('prompt')
        msg = data.get('msg')

        available_models = config_get_model_list()
        if model_name not in available_models:
            return jsonify({'error': f'不支持的模型: {model_name}'}), 400

        result = query_llm(model_name, prompt, msg)

        if isinstance(result, tuple): # 如果返回的是错误元组
            error_msg, status_code = result
            return jsonify(error_msg), status_code
        else: # 否则返回流式响应
            return Response(stream_with_context(result))

    @app.route('/api/generate-audio-url', methods=['GET'])
    # @limiter.limit("...") # 可以根据需要添加限流
    def generate_audio_url_route():
        """检查音频文件状态的路由 (原 generate-audio-url)"""
        content_type = request.args.get('contentType', 'audio/mpeg')
        file_hash = request.args.get('fileHash')
        result, status_code = check_audio_file_status(AUDIO_FOLDER, content_type, file_hash)
        return jsonify(result), status_code

    @app.route('/api/upload-audio', methods=['POST'])
    @limiter.limit("120 per hour")
    def upload_audio_route():
        """处理音频文件上传的路由"""
        if 'file' not in request.files:
            return jsonify({"error": "缺少文件部分"}), 400
        file = request.files['file']
        object_name = request.form.get('object_name')

        result, status_code = save_uploaded_audio(AUDIO_FOLDER, file, object_name)
        return jsonify(result), status_code

    @app.route('/api/transcribe-audio', methods=['POST'])
    @limiter.limit("60 per hour")
    def transcribe_audio_route():
        """处理音频转录请求的路由"""
        data = request.get_json()
        object_name = data.get('object_name')
        model_name = data.get('model')

        # transcribe_audio 现在直接返回 Flask Response 或 (jsonify(...), status_code)
        return transcribe_audio(AUDIO_FOLDER, SCRIPT_DIR, object_name, model_name)


    @app.route('/api/analyze-report', methods=['POST'])
    @limiter.limit("60 per hour")
    def analyze_report_route():
        """处理举报信息分析请求的路由"""
        data = request.get_json()
        object_name = data.get('object_name')
        transcription_text = data.get('transcription_text')

        # analyze_report_info 现在直接返回 Flask Response (jsonify)
        return analyze_report_info(SCRIPT_DIR, object_name, transcription_text)

    @app.route('/api/submit-final-report', methods=['POST'])
    @limiter.limit("60 per hour")
    def submit_final_report_route():
        """处理最终举报信息提交的路由""" 
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须为JSON格式"}), 400
        
        success, message = save_report_data(data)
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"error": message}), 400