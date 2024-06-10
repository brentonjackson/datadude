import subprocess
import sys

DEFAULT_MAX_TOKENS = 1000

def call_token_validator(text, max_tokens=None):
    """
    Calls the token_validator.py script as a subprocess with the given text and optional max_tokens.
    """
    # Prepare the command to run token_validator.py
    command = ['python', 'ai_utils/token_validator.py']
    if max_tokens is not None:
        command.append(str(max_tokens))
    
    # Run the token_validator.py script as a subprocess
    result = subprocess.run(command, input=text, capture_output=True, text=True)
    
    # Check the return code to determine if validation was successful
    if result.returncode != 0:
        print(f"{result.stdout.strip()}")
        # exit(result.returncode)
    return result.returncode


if __name__ == "__main__":
    input_text = "This is sample text to test the token validator."
    max_tokens = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_TOKENS

    status_code = call_token_validator(input_text, max_tokens)
