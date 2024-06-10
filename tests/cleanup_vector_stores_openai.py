import sys
import os

# Path to the external code
external_code_path = os.path.join(os.getcwd(), '..')
print(external_code_path)

# Add the external code directory to sys.path
if external_code_path not in sys.path:
    sys.path.append(external_code_path)

# Now you can import the external module
from ai_utils.assistants_handler import AssistantsHandler


assistant: AssistantsHandler = AssistantsHandler("", "")
assistant.delete_vectore_stores()