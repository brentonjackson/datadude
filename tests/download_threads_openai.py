import sys
import os

# Path to the external code
external_code_path = os.path.join(os.getcwd(), '..')

# Add the external code directory to sys.path
if external_code_path not in sys.path:
    sys.path.append(external_code_path)

# Now you can import the external module
from ai_utils.assistants_handler import AssistantsHandler


assistant: AssistantsHandler = AssistantsHandler("", "")
messages = assistant.get_thread_messages("thread_Z0js5ZWYBrGSh4C2Q5EMrVeb")
for message in messages:
    print(message, "\n")