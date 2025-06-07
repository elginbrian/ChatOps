import google.generativeai as genai
from flask import current_app
from app.models.commands import COMMAND_GUIDE
from google.generativeai.protos import Part, FunctionResponse
import json
import re

def _create_dynamic_tools_from_guide():
    function_declarations = []
    
    param_pattern = re.compile(r'\(\?P<(\w+)>')

    for cmd_def in COMMAND_GUIDE:
        function_name = cmd_def["id"]
        description = cmd_def["description"]
        
        params = param_pattern.findall(cmd_def["pattern"])
        
        required_params = cmd_def.get("required_params", params)

        properties = {}
        for param in params:
            properties[param] = {"type": "string", "description": f"Parameter untuk {param}"}

        func = genai.types.FunctionDeclaration(
            name=function_name,
            description=description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required_params,
            }
        )
        function_declarations.append(func)
        
    return genai.types.Tool(function_declarations=function_declarations)

def _get_command_summary():
    return "\n".join([f"- `{cmd['example']}`: {cmd['description']}" for cmd in COMMAND_GUIDE])

def summarize_docker_status(status_data: dict):
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        return None, "Error: GEMINI_API_KEY tidak diatur di server."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    prompt = f"""
    Anda adalah asisten Docker. Berdasarkan data JSON berikut, buatlah sebuah ringkasan status yang singkat, jelas, dan ramah untuk pengguna.

    Data Status:
    {json.dumps(status_data, indent=2)}

    Contoh output yang baik: "Saat ini, Anda memiliki {status_data.get('total_containers', 0)} kontainer, dimana {status_data.get('running_containers', 0)} sedang berjalan. Selain itu, terdapat {status_data.get('total_images', 0)} image dan {status_data.get('total_volumes', 0)} volume di sistem Anda."
    Jawab dalam Bahasa Indonesia.
    """
    try:
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        current_app.logger.error(f"Error saat meringkas status Docker: {e}", exc_info=True)
        return None, "Gagal saat membuat ringkasan status dari AI."

def handle_gemini_request(user_prompt: str, history: list):
    from app.api.handlers import ACTION_HANDLERS, INSPECT_ACTION_MAP

    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        return {"output": None, "error": "Error: GEMINI_API_KEY tidak diatur di server.", "output_type": "text"}

    genai.configure(api_key=api_key)

    system_prompt = f"""
    You are a helpful and intelligent Docker assistant. Your primary role is to assist users in managing their Docker environment.
    When a user asks a question that requires real-time information (e.g., "is my database container running?", "show me the details of nginx and redis containers"), you MUST use your available tools.
    You can call multiple tools in parallel in a single turn.

    IMPORTANT: If you need to present data in a tabular format, you MUST ONLY output a single, valid JSON object following this EXACT structure:
    {{
      "type": "table",
      "data": {{
        "headers": ["Header 1", "Header 2", ...],
        "rows": [
          ["Row 1 Cell 1", "Row 1 Cell 2", ...],
          ["Row 2 Cell 1", "Row 2 Cell 2", ...]
        ]
      }}
    }}
    Do not add any text or explanation outside of this JSON object.

    IMPORTANT: If the user asks for "help", "bantuan", or "command list", you MUST NOT list the commands yourself. Instead, reply with the text: "Tentu, Anda dapat melihat semua daftar perintah yang tersedia dengan menekan tombol 'Panduan Perintah' di sidebar."
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        tools=[_create_dynamic_tools_from_guide()]
    )
    
    gemini_history = []
    for item in history:
        gemini_history.append({"role": "user", "parts": [{"text": item['user_command']}]})
        bot_response_text = json.dumps(item.get('bot_response', {}).get('output'))
        gemini_history.append({"role": "model", "parts": [{"text": bot_response_text}]})

    chat = model.start_chat(history=gemini_history)
    
    try:
        response = chat.send_message(user_prompt)
        
        while response.candidates[0].content.parts[0].function_call:
            function_calls = response.candidates[0].content.parts
            tool_responses = []

            for call in function_calls:
                function_call = call.function_call
                command_id = function_call.name
                params = dict(function_call.args)
                
                current_app.logger.info(f"Gemini calling function '{command_id}' with params: {params}")

                cmd_def = next((cmd for cmd in COMMAND_GUIDE if cmd["id"] == command_id), None)
                
                if not cmd_def:
                    func_response = FunctionResponse(name=command_id, response={"status": "error", "message": f"Fungsi '{command_id}' tidak ditemukan."})
                    tool_responses.append(Part(function_response=func_response))
                    continue

                action = cmd_def.get("action")
                if action == "inspect_object":
                    object_type = params.get("object_type")
                    action = INSPECT_ACTION_MAP.get(object_type)
                
                if action in ACTION_HANDLERS:
                    if "params_map" in cmd_def:
                        params.update(cmd_def["params_map"])
                    
                    output_data, error_str = ACTION_HANDLERS[action](params)
                    
                    serialized_output = json.dumps(output_data)

                    func_response = FunctionResponse(
                        name=command_id, 
                        response={"data": serialized_output, "error": error_str}
                    )
                    tool_responses.append(Part(function_response=func_response))
                else:
                    func_response = FunctionResponse(name=command_id, response={"status": "error", "message": f"Aksi untuk '{command_id}' tidak terdefinisi."})
                    tool_responses.append(Part(function_response=func_response))
                
            response = chat.send_message(tool_responses)
        
        final_text = response.candidates[0].content.parts[0].text
        
        json_match = re.search(r'\{.*\}', final_text, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(0)
            try:
                json_data = json.loads(json_string)
                if isinstance(json_data, dict) and json_data.get("type") == "table":
                    current_app.logger.info("Gemini generated a table, extracted from text.")
                    return {"output": json_data.get("data"), "error": None, "output_type": "gemini_table"}
            except json.JSONDecodeError:
                pass
        
        return {"output": final_text, "error": None, "output_type": "gemini_text"}

    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred with Gemini API: {e}", exc_info=True)
        try:
            current_app.logger.error(f"Last Gemini Response before error: {response}")
        except NameError:
            pass
        return {"output": None, "error": f"An unexpected error occurred with the Gemini API. Check server logs for details.", "output_type": "text"}