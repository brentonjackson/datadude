from openai import OpenAI
from ai_utils.ai_base import AIHandler

class ChatCompletionsHandler(AIHandler):
    """
    This AI handler holds no state between messages.
    They effectively reset to zero.
    However, context is up to date on every message sent.
    The context is sent as a "system" message.
    """
    def __init__(self):
        self.client = OpenAI()

    def setup(self):
        # No setup required for Chat Completions API
        pass

    def get_response(self, context: str, input: str, init=False):
        messages = [
            {"role": "user", "content": f"{input}"},
        ]
        if init:
            messages = [
                {"role": "system", "content": f"You are DataDude, a filesystem assistant that knows everything about the specified directory. Using only the following context: {context}, answer the resulting queries. Answer queries briefly, in a sentence or less."},
                {"role": "user", "content": "Who are you?",},
                {"role": "assistant", "content": "I'm DataDude, your filesystem assistant bro!",},
                {"role": "system", "name": "example_user", "content": "What info do you have on my files?",},
                {"role": "system", "name": "example_assistant", "content": "I can tell you the name, full path, and the last modified/updated time of your files, based on the context you've given me.",},
                {"role": "system", "name":"example_user", "content": "When was the last updated file?"},
                {"role": "system", "name": "example_assistant", "content": "server.py, which was updated on 6/1/2024 at 6:18 PM."},
                {"role": "system", "name":"example_user", "content": "What is the path to server.py?"},
                {"role": "system", "name": "example_assistant", "content": "/Users/example_user/code/project/server.py"},
                {"role": "user", "content": f"{input}"}
            ]
        
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0 # from 0 to 2, where 0 is most deterministic and 2 most random.
        )
        return completion.choices[0].message.content
