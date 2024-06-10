import base64
import gzip
import json
import os

filename = "../tmp/4929b078-c2e0-5e22-b96d-0dec404f76f7_context.json"

# Read the JSON file
with open(filename, 'r') as file:
    filecontent = file.read()
    file_info = json.loads(filecontent)

# Extract the first file's base64 encoded content
first_filename = file_info["files"][0]["name"]
first_file_content = file_info["files"][0]["content"]  # Updated to match correct JSON structure if it doesn't contain 'files'
print(len(first_file_content))
# Decode the base64 content
decoded_content = base64.b64decode(first_file_content)

# Decompress the gzip content
decompressed_content = gzip.decompress(decoded_content)
# print(decompressed_content)


# Ensure the tmp directory exists
if not os.path.exists("tmp"):
    os.makedirs("tmp")

# Write the decompressed content to a file
output_path = "tmp/"  + first_filename
with open(output_path, 'wb') as output_file:
    output_file.write(decompressed_content)

print(f"Decompressed content written to {output_path}")
