from ai_utils.chat_completions_handler import ChatCompletionsHandler
from ai_utils.assistants_handler import AssistantsHandler

def get_ai_handler(ai_type, sessionID, context: object):
    if ai_type == "chat_completions":
        return ChatCompletionsHandler()
    elif ai_type == "assistants":
        return AssistantsHandler(sessionID=sessionID, context=context)
    else:
        raise ValueError(f"Unknown AI type: {ai_type}")
