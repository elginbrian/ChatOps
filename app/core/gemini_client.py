import google.generativeai as genai
from flask import current_app
from app.models.commands import COMMAND_GUIDE
from app.api.handlers import ACTION_HANDLERS, INSPECT_ACTION_MAP
import json
import re

def _create_dynamic_tools_from_guide():
    function_declarations = []
    
    param_pattern = re.compile(r'\(\?P<(\w+)>')

    for cmd_def in COMMAND_GUIDE:
        function_name = cmd_def["id"]
        description = cmd_def["description"]
        
        params = param_pattern.findall(cmd_def["pattern"])
        
        properties = {}
        for param in params:
            properties[param] = {"type": "string", "description": f"Parameter untuk {param}"}

        func = genai.types.FunctionDeclaration(
            name=function_name,
            description=description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": params, 
            }
        )
        function_declarations.append(func)
        
    return genai.types.Tool(function_declarations=function_declarations)

def _get_command_summary():
    return "\n".join([f"- `{cmd['example']}`: {cmd['description']}" for cmd in COMMAND_GUIDE])

def handle_gemini_request(user_prompt: str, history: list):
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        return {"output": None, "error": "Error: GEMINI_API_KEY tidak diatur di server.", "output_type": "text"}

    genai.configure(api_key=api_key)

    system_prompt = f"""
    You are a helpful and intelligent Docker assistant integrated into a ChatOps application.
    Your primary role is to assist users in managing their Docker environment through conversation.
    You have two main capabilities:
    1.  **General Conversation**: You can only answer questions related to Docker, DevOps, and Cloud Infrastructure.
    2.  **Docker Interaction**: You have a set of special tools to get real-time information from the Docker environment. When a user asks a question that requires knowledge of the current state of Docker (e.g., "is my database container running?", "why did my webserver crash?", "show me the nginx image details"), you MUST use one of your available tools.
    
    Here is a summary of available tools:
    {_get_command_summary()}

    Analyze the user's prompt and decide whether to answer directly or to use one of the available functions.
    """

    safety_settings = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }
    
    docker_tool = _create_dynamic_tools_from_guide()

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        tools=[docker_tool],
        safety_settings=safety_settings
    )
    
    gemini_history = []
    for item in history:
        gemini_history.append({"role": "user", "parts": [{"text": item['user_command']}]})
        bot_response_text = json.dumps(item.get('bot_response', {}).get('output'))
        gemini_history.append({"role": "model", "parts": [{"text": bot_response_text}]})

    chat = model.start_chat(history=gemini_history)
    
    try:
        response = chat.send_message(user_prompt)
        current_app.logger.info(f"Gemini Raw Response: {response}")

        if not response.candidates:
            feedback = response.prompt_feedback
            error_message = f"Gemini request was blocked. Reason: {feedback.block_reason}."
            current_app.logger.error(error_message)
            return {"output": None, "error": error_message, "output_type": "text"}

        part = response.candidates[0].content.parts[0]

        if hasattr(part, 'function_call') and part.function_call:
            function_call = part.function_call
            command_id = function_call.name
            params = dict(function_call.args)
            
            current_app.logger.info(f"Gemini calling function '{command_id}' with params: {params}")

            cmd_def = next((cmd for cmd in COMMAND_GUIDE if cmd["id"] == command_id), None)
            
            if not cmd_def:
                return {"output": None, "error": f"Error: Gemini mencoba memanggil fungsi tidak dikenal: '{command_id}'", "output_type": "text"}

            action = cmd_def["action"]
            
            if action == "inspect_object":
                object_type = params.get("object_type")
                resolved_action = INSPECT_ACTION_MAP.get(object_type)
                if not resolved_action:
                    return {"output": None, "error": f"Error: Tipe objek '{object_type}' tidak dikenal untuk inspect.", "output_type": "text"}
                action = resolved_action

            if action in ACTION_HANDLERS:
                if "params_map" in cmd_def:
                    params.update(cmd_def["params_map"])
                
                output_data, error_str = ACTION_HANDLERS[action](params)

                output_type = "text"
                if action in ["list_containers", "list_images", "view_stats", "view_logs", "list_volumes", "list_networks"]:
                    output_type = "table"
                elif "inspect" in action:
                    output_type = "inspect"
                else: 
                    output_type = "action_receipt"

                tool_response = {"output": output_data, "error": error_str, "output_type": output_type}
                
                final_response = chat.send_message(
                    genai.types.Part.from_function_response(
                        name=command_id,
                        response={"result": tool_response}
                    )
                )
                final_text = final_response.candidates[0].content.parts[0].text
                return {"output": final_text, "error": None, "output_type": "gemini_text"}
            else:
                 return {"output": None, "error": f"Error: Aksi '{action}' belum terdefinisi di backend.", "output_type": "text"}
        
        elif hasattr(part, 'text') and part.text:
            return {"output": part.text, "error": None, "output_type": "gemini_text"}
        
        else:
            return {"output": None, "error": "Gemini returned an empty or unexpected response.", "output_type": "text"}

    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred with Gemini API: {e}", exc_info=True)
        return {"output": None, "error": f"An unexpected error occurred with the Gemini API. Check logs for details.", "output_type": "text"}