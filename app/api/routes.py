from flask import Blueprint, request, jsonify, current_app
from ..api.handlers import parse_and_execute_command
from ..core import history_manager

api_bp = Blueprint('api', __name__)

@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    conv_list = history_manager.get_conversations_list()
    return jsonify(conv_list)

@api_bp.route('/conversation/<string:conv_id>', methods=['GET'])
def get_conversation(conv_id):
    messages = history_manager.get_conversation_messages(conv_id)
    history_manager.set_last_active(conv_id)
    return jsonify(messages)

@api_bp.route('/conversation/<string:conv_id>', methods=['DELETE'])
def delete_conversation_route(conv_id):
    if history_manager.delete_conversation(conv_id):
        return jsonify({"status": "success", "message": "Percakapan dihapus."})
    else:
        return jsonify({"error": "Percakapan tidak ditemukan."}), 404

@api_bp.route('/command', methods=['POST'])
def handle_command_route():
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': "Permintaan buruk: field 'command' dibutuhkan."}), 400

        user_command_str = data.get('command', '').strip()
        conv_id = data.get('conversation_id')

        if not user_command_str:
            return jsonify({'error': "Perintah tidak boleh kosong."}), 400

        current_app.logger.info(f"Menerima perintah: '{user_command_str}' untuk conv_id: {conv_id}")

        result = parse_and_execute_command(user_command_str)

        if conv_id:
            history_manager.add_message_to_conversation(conv_id, user_command_str, result)
            history_manager.set_last_active(conv_id)
            return jsonify(result)
        else:
            new_conv_id = history_manager.create_new_conversation(user_command_str, result)
            history_manager.set_last_active(new_conv_id)
            response_data = {**result, "conversation_id": new_conv_id}
            return jsonify(response_data)

    except Exception as e:
        current_app.logger.exception(f"Error internal server saat memproses perintah dari {request.remote_addr}:")
        error_msg = str(e) if current_app.config['DEBUG_MODE'] else "Terjadi kesalahan internal pada server."
        return jsonify({'error': error_msg, 'output_type': 'text'}), 500