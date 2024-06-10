import os
import json
import sys
from datetime import datetime
import gzip
import base64


DEFAULT_FOLDER_PATH = os.getcwd()

def read_dudeignore(dudeignore_location=DEFAULT_FOLDER_PATH):
    """
    Reads the .dudeignore file and returns a list of files and directories to omit.
    Also ignores anything in a .gitigore, which should be in the same location.
    """
    dudeignore_path = os.path.join(dudeignore_location, '.dudeignore')
    gitignore_path = os.path.join(dudeignore_location, '.gitignore')
    if not os.path.exists(dudeignore_path):
        # use my .dudeignore instead
        return [".dudeignore", ".git"]
    with open(dudeignore_path, 'r') as file:
        lines = file.readlines()
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            git_lines = file.readlines()
        for line in git_lines:
            lines.append(line)
    # Strip lines, ignore empty lines and comments
    omit_paths = [line.strip().rstrip('/') for line in lines if line.strip() and not line.startswith("#")]
    omit_paths.append(".dudeignore")
    omit_paths.append(".git")
    return omit_paths

def get_directory_structure(rootdir=DEFAULT_FOLDER_PATH, omit_paths=None):
    """
    Recursively collects information about files and directories, omitting specified subdirectories and files.
    Will not omit a directory listed in .dudeignore if that directory is the rootdir.
    """
    if omit_paths is None:
        omit_paths = []

    file_info_list = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        # Omit specified subdirectories
        dirnames[:] = [d for d in dirnames if d not in omit_paths]
        # Omit specified files
        filenames[:] = [f for f in filenames if f not in omit_paths]

        for file in filenames:
            file_path = os.path.join(dirpath, file)
            file_info = {
                "name": file,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "lastModified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            }
            if file.endswith(('.md', '.py', '.sh', '.js', '.jsx')):
                # Read and compress the file content
                with open(file_path, 'r') as f:
                    file_content = f.read()
                    # compressed_content = gzip.compress(file_content)
                    # base64_encoded_content = base64.b64encode(compressed_content).decode('utf-8')
                    
                    # # Ensure proper base64 padding
                    # missing_padding = len(base64_encoded_content) % 4
                    # if missing_padding != 0:
                    #     base64_encoded_content += '=' * (4 - missing_padding)
                    
                    file_info['content'] = file_content

            file_info_list.append(file_info)
    return file_info_list
   

if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FOLDER_PATH
    dudeignore_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_FOLDER_PATH

    try:
        omit_paths = read_dudeignore(dudeignore_path)
        files = get_directory_structure(folder_path, omit_paths)

        # Output the directory structure as a JSON string
        files_json = json.dumps(files, indent=2)
        print(files_json)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
