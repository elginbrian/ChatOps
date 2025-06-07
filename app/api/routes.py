from flask import Blueprint, request, jsonify, current_app
from .handlers import parse_and_execute_command

api_bp = Blueprint('api', __name__)

@api_bp.route('/command', methods=['POST'])
def handle_command_route():
    try:
        data = request.get_json()
        if not data or 'command' not in data or not isinstance(data['command'], str):
            current_app.logger.warning(f"Permintaan buruk dari {request.remote_addr}")
            return jsonify({'error': "Permintaan buruk: Field 'command' (string) dibutuhkan.", 'output': ''}), 400
        
        user_command_str = data.get('command', '').strip()
        current_app.logger.info(f"Menerima perintah dari {request.remote_addr}: '{user_command_str}'")

        result = parse_and_execute_command(user_command_str)

        response_data = {
            'output': result.get('output'),
            'error': result.get('error'),
            'output_type': result.get('output_type', 'text'),
            'received_command': user_command_str
        }
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.exception(f"Error internal server saat memproses /api/command dari {request.remote_addr}:")
        internal_error_msg = "Terjadi kesalahan internal pada server." if not current_app.config['DEBUG_MODE'] else str(e)
        return jsonify({'error': internal_error_msg, 'output': ''}), 500