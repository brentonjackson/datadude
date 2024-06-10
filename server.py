from flask import Flask, request, jsonify
import uuid
import os
from ai_utils.ai_factory import get_ai_handler
from ai_utils.ai_base import AIHandler  # The base class to define type hints
from datetime import datetime

# Create an instance of AIHandler based on the desired type
# For example, use "chat_completions" or "assistants"
DEFAULT_AI_HANDLER = "assistants"
ai_handlers = {} # store ai handlers for each thread


"""
messagePool:
{
    <sessionID>: {
        folder: "",
        threads: {
            <threadID>: 
            {
                messages: [],
                startTime: "",
                endTime: "",
            },
        },
        files: [],
        gitinfo: {},
    },
    <sessionID>: {
        folder: "",
        threads: {
            <threadID>:
            {
                messages: [],
                startTime: "",
                endTime: "",
            }
        },
        files: [],
        gitinfo: {},
    }
}
Data structures to hold messages
Each sessionID has its own in-memory message thread in the pool that it uses
The message pool is structured as key-value pairs w/ key being session ID
The value is an object itself which has all the info about the session,
most importantly the list of threads which contain messages:
List of messages e.g. [{user: "asdfasdf"}, {system: "adsfasdf"},...]
but also some other things about the session, such as the context:
context: { folder: "", files: [{ filename: "", modified: "", size: "", ...}], gitinfo: {} }
It makes sense to keep the contexts common under the sessionID since the sessionID
represents the folder itself.
Also, the threadID is not the same as the thread_id used by the AI system.
"""
messagePool = {}

app = Flask(__name__)

########## Helper Functions ###########
def create_context_text(context):
    """
    Summarizes the context to keep it concise
    """
    files_summary = "\n".join([f"{file['name']} ({file['path']}, {file['size']} bytes)" for file in context['files']])
    # git_info_summary = "\n".join([f"{key}: {value}" for key, value in context['git_info'].items()])

    return f"Files:\n{files_summary}\n"
    # \nGit Info:\n{git_info_summary}"

def validate_sessionID(sessionID: str):
    """
    Returns False if given sessionID is invalid. Returns True if valid.
    """
    if not messagePool.get(sessionID):
        return False
    return True

def validate_threadID(sessionID: str, threadID: str):
    """
    Returns False if given threadID not part of session. Returns True if valid.
    """
    if len(messagePool[sessionID]["threads"]) == 0:
        return False
    # iterate through messagePool threads to see if the given threadID exists
    if not messagePool[sessionID]["threads"].get(threadID):
        return False
    return True
    
#######################################

########## API Endpoints ###########
@app.route('/')
def home():
    return "DataDude Server is running"

@app.route('/session', methods=['POST'])
def start_session():
    """
    Returns two UUIDs representing the session ID and thread ID, not caring if the session
    was started already or not.
    """
    data = request.get_json()    

    if "path" not in data:
        return jsonify({'error': 'No path in the request'}), 400
    path = data.get("path")
    if not path or not os.path.isdir(path):
        return jsonify({'error': 'Invalid folder path'}), 400
    
    
    sessionID = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
    # create new thread, which is completely independent of the AI handler's threads
    # they may have the same data, or not depending on the handler used.
    # for example, chat completions API doesn't use threads.
    threadID = str(uuid.uuid4()) # completely random uuid
    # Store the AI handler for this thread
    ai_type = data.get("ai_type", DEFAULT_AI_HANDLER)

    
    # If path already in message pool, just create a new thread
    if messagePool.get(sessionID):
        messagePool[sessionID]["threads"][threadID] = {
            "startTime": datetime.now().isoformat(),
            "endTime": "",
            "messages": [],
            "ai_type": ai_type
        }
    else:
    # If this is a new session completely, add all of the info to the message pool
        messagePool[sessionID] = {
            "folder": os.path.basename(path),
            "threads": {
                threadID: {
                    "startTime": datetime.now().isoformat(),
                    "endTime": "",
                    "messages": [],
                    "ai_type": ai_type
                },
            },
        }
   

    # Some context is required, even if it's just a refresh of what's already there.
    # In the future, we may decide to use the file data already attached to the
    # session in the message pool if that's available.
    if "files" not in data:
        return jsonify({'error': 'No file object in the request'}), 400
    files = data.get("files")
    # git_info = data.get("git_info")
    messagePool[sessionID]["files"] = [dict(file) for file in files]
    # messagePool[sessionID]["gitinfo"] = git_info
    context = {
        "files": files,
        # "git_info": {item['key']: item['value'] for item in git_info}
    }

    # Create a new AI handler for each thread/client instance, even if it's the same session.
    if not ai_handlers.get(threadID):
        ai_handler = get_ai_handler(ai_type, sessionID=sessionID, context=context) 
        ai_handlers[threadID] = ai_handler

    return jsonify({'sessionID': sessionID, 'threadID': threadID}), 200

@app.route('/chat/<sessionID>', methods=['POST'])
def answer_message(sessionID: str):
    """
    Returns a response to the chat message and saves it in the session.
    """
    
    # validate request data
    data: object = request.get_json()
    if "threadID" not in data:
        return jsonify({'error': 'No threadID in the request'}), 400
    if "message" not in data:
        return jsonify({'error': 'No message in the request'}), 400
    threadID: str = data.get("threadID")
    sessionID = sessionID.strip()
    if not validate_sessionID(sessionID):
        return jsonify({'error': 'Invalid sessionID.'}), 400
    threadID = threadID.strip()
    if not validate_threadID(sessionID, threadID):
        return jsonify({'error': 'Invalid threadID.'}), 400

    message: str = data.get("message")
    if message == "":
        response = "Sup!"
        messagePool[sessionID]["threads"][threadID]["messages"].append({"system": response})
        return jsonify({'message': response}), 200
    
    # This isn't a big deal if not passed. Treat as optional
    # Retrieve data related to the session
    files = messagePool[sessionID]["files"]
    # git_info = messagePool[sessionID]["git_info"]
    if "files" in data:
        files = data.get("files") # this is newer data
        messagePool[sessionID]["files"] = [dict(file) for file in files]
        # git_info = data.get("git_info")
        # messagePool[str(sessionID)]["gitinfo"] = git_info
        
    # Gather context for AI
    context = {
        "files": files,
        # "git_info": {item['key']: item['value'] for item in git_info}
    }

    is_first_message = data.get("initMessage")
    context_text = create_context_text(context) # Create a concise context to send to OpenAI API
    
    ai_handler: AIHandler = ai_handlers.get(threadID, get_ai_handler(DEFAULT_AI_HANDLER, sessionID, context))
    response = ai_handler.get_response(context_text, input=message, init=is_first_message)

    messagePool[sessionID]["threads"][threadID]["messages"].append({"user": message.strip()})
    messagePool[sessionID]["threads"][threadID]["messages"].append({"system": response})

    # Return message back to user
    return {'message': response}, 200
#####################################

if __name__ == '__main__':
    app.run()  