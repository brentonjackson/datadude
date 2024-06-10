import subprocess
import json

def get_directory_structure_json(root_dir=None):
    """
    Calls the directory_scanner.py script as a subprocess and returns the directory structure object.
    """
    # Prepare the command to run directory_scanner.py
    command = ['python', 'directory_utils/directory_scanner.py']
    if root_dir is not None:
        command.append(str(root_dir))

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
        return json.loads(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

if __name__ == "__main__":
    directory_json = get_directory_structure_json()
    if directory_json:
        print(json.dumps(directory_json, indent=2))
