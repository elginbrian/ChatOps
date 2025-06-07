import google.generativeai as genai
from flask import current_app
from app.models.commands import COMMAND_GUIDE
import json

docker_tool = genai.types.Tool(
    function_declarations=[
        genai.types.FunctionDeclaration(
            name="execute_docker_command",
            description="Executes a command to interact with the Docker environment, such as listing containers, viewing logs, or inspecting images. Use this to get real-time information about the system.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute, for example: 'list containers', 'docker ps', 'lihat log webku', 'inspect image nginx'."
                    }
                },
                "required": ["command"]
            }
        )
    ]
)

def _get_command_summary():
    return "\n".join([f"- `{cmd['example']}`: {cmd['description']}" for cmd in COMMAND_GUIDE])

def handle_gemini_request(user_prompt: str, history: list):
    from app.api.handlers import parse_and_execute_command

    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        return {"output": None, "error": "Error: GEMINI_API_KEY tidak diatur di server.", "output_type": "text"}

    genai.configure(api_key=api_key)

    system_prompt = f"""
    You are a helpful and intelligent Docker assistant integrated into a ChatOps application.
    Your primary role is to assist users in managing their Docker environment through conversation.

    You have two main capabilities:
    1.  **General Conversation**: You can only answer questions related to Docker, DevOps, and Cloud Infrastructure
    2.  **Docker Interaction**: You have a special tool to get real-time information from the Docker environment. When a user asks a question that requires knowledge of the current state of Docker (e.g., "is my database container running?", "why did my webserver crash?", "show me the nginx image details"), you MUST use the `execute_docker_command` tool.

    Here are some examples of commands you can execute with your tool:
    {_get_command_summary()}

    Based on the user's prompt, decide whether to answer directly or to use the `execute_docker_command` tool to gather information first before answering.
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=system_prompt,
        tools=[docker_tool]
    )
    
    gemini_history = []
    for item in history:
        gemini_history.append({"role": "user", "parts": [{"text": item['user_command']}]})
        bot_response_text = json.dumps(item.get('bot_response', {}).get('output'))
        gemini_history.append({"role": "model", "parts": [{"text": bot_response_text}]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_prompt)
    
    try:
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call.name == "execute_docker_command":
            command_to_run = function_call.args["command"]
            current_app.logger.info(f"Gemini wants to execute command: '{command_to_run}'")
            
            tool_response = parse_and_execute_command(command_to_run, is_gemini_call=True)
            
            final_response = chat.send_message(
                genai.types.Part.from_function_response(
                    name="execute_docker_command",
                    response={"result": tool_response}
                )
            )
            final_text = final_response.candidates[0].content.parts[0].text
            return {"output": final_text, "error": None, "output_type": "gemini_text"}

    except (ValueError, AttributeError, IndexError):
        final_text = response.candidates[0].content.parts[0].text
        return {"output": final_text, "error": None, "output_type": "gemini_text"}

    return {"output": None, "error": "Terjadi kesalahan saat berkomunikasi dengan Gemini.", "output_type": "text"}