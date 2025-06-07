from flask import (Blueprint, request, jsonify, current_app, 
                   render_template, session, redirect, url_for, flash)
from ..api.handlers import parse_and_execute_command
from ..core import history_manager
from ..models.commands import COMMAND_GUIDE
from functools import wraps

api_bp = Blueprint('api', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('api.login'))
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/')
@login_required
def index():
    return render_template('index.html', command_guide=COMMAND_GUIDE)

@api_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('api.index'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password and password == current_app.config.get('CHATOPS_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('api.index'))
        else:
            flash('Password yang Anda masukkan salah.', 'error')
            return redirect(url_for('api.login'))
            
    return render_template('login.html')

@api_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Anda telah berhasil logout.', 'success')
    return redirect(url_for('api.login'))

@api_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    conv_list = history_manager.get_conversations_list()
    return jsonify(conv_list)

@api_bp.route('/conversation/<string:conv_id>', methods=['GET'])
@login_required
def get_conversation(conv_id):
    messages = history_manager.get_conversation_messages(conv_id)
    history_manager.set_last_active(conv_id)
    return jsonify(messages)

@api_bp.route('/conversation/<string:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation_route(conv_id):
    if history_manager.delete_conversation(conv_id):
        return jsonify({"status": "success", "message": "Percakapan dihapus."})
    else:
        return jsonify({"error": "Percakapan tidak ditemukan."}), 404

@api_bp.route('/command', methods=['POST'])
@login_required
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

        conversation_history = []
        if conv_id:
            conversation_history = history_manager.get_conversation_messages(conv_id)

        result = parse_and_execute_command(user_command_str, history=conversation_history)

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