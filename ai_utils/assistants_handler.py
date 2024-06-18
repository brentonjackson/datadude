from openai import OpenAI
from ai_utils.ai_base import AIHandler
import json
import time
import os

def show_json(obj):
    dict = json.loads(obj.model_dump_json())
    print(json.dumps(dict, indent=2, sort_keys=True))

def create_temp_file(data, filename):
    """
    creates temp file w/ data in it
    """
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    path = "tmp/" + filename
    with open(path, 'wb') as file:
        file.write(data)
    return path

def delete_temp_folder(filename):
    """
    removes the tmp folder and all files within
    """
    os.rmdir("tmp")
    os.remove("tmp/" + filename)
    return


class AssistantsHandler(AIHandler):
    """
    This AI handler persists message state in the forms of threads.
    """
    def __init__(self, sessionID: str, context: object):
        self.client = OpenAI()
        self.assistant = None
        self.thread_id = None
        self.sessionID = sessionID
        self.vector_store_id = None
        self.run = None
        if sessionID and context:
            # this is skipped when running test scripts
            self.setup(context)

    def setup(self, sessionContext: object):
        """
        Loads AI assistant and creates a new thread.
        """
        # The assistant only needs to be created once. It should not be created every time.
        # At most, we should find the assistant, then load it here.
        my_assistants = self.client.beta.assistants.list(
            order="desc",
        )
        # if my_assistants.has_next_page(): 
        #     print("dude you got a lot of assistants.")
        # do some pagination https://platform.openai.com/docs/api-reference/assistants/listAssistants
        
        if len(my_assistants.data) > 0:
            # get data dude directory assistant
            assistants_list = my_assistants.data
            # could've used a for loop for this search, but this oneliner is nice
            data_dude_assistant = next((assistant for assistant in assistants_list if assistant.name == "DataDude Directory Assistant"), None)
            self.assistant = data_dude_assistant
        
        if self.assistant == None:
            self.assistant = self.client.beta.assistants.create(
                instructions=f"""You are DataDude, an expert filesystem detective. Answer queries very accurately, according to the files uploaded in the vector stores. To read the file contents,
                    read the JSON File: Open the <id>_context.json file and load the entire file content.
                    <id> is the id at the end of the name of the vector store attached to the current thread. 
                    All responses should be text. If not, send a url link to the asset instead of the asset itself.
                    When the user references 'this folder' or 'this project', assume they are referring to the information about
                    the uploaded directory captured in the previously mentioned json file.
                    """,
                # instructions=f"""You are DataDude, an expert filesystem detective. Answer queries very accurately, according to the files uploaded in the vector stores. To read the file contents, write Python code to:
                #     1. Read the JSON File: Open the {self.sessionID}_context.json file and load the entire file object, not just the content key.
                #     2. Extract Encoded Content: Access the base64 encoded content from the JSON data as bytes, not a string. This is important.
                #     3. Base64 Decode: Decode the base64 encoded string to get the gzip compressed binary data.
                #     4. Gzip Decompress: Decompress the gzip data to retrieve the original content.
                #     5. Write to stdout: Print the decompressed content or save to a new file.
                    
                #     All responses should be text. If not, send a url link to the asset instead of the asset itself.
                #     When the user references 'this folder' or 'this project', assume they are referring to the information about
                #     the uploaded directory.
                #     """,
                name="DataDude Directory Assistant",
                tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
                model="gpt-3.5-turbo", # https://platform.openai.com/docs/models,
                temperature=0.0 # makes things more deterministic, up to 2 makes things more random
            )


        
        my_vector_stores = self.client.beta.vector_stores.list(order="desc")
        if len(my_vector_stores.data) > 0:
            # get latest vector store
            vector_store_list = my_vector_stores.data
            # could've used a for loop for this search, but this oneliner is nice
            vector_store = next((vector_store for vector_store in vector_store_list if vector_store.name == "Directory Context Files " + self.sessionID), None)
            if vector_store and vector_store.status != "expired":
                self.vector_store_id = vector_store.id
       
        if self.vector_store_id == None:
            # Create vector store for the session/directory
            vector_store = self.client.beta.vector_stores.create(
                name="Directory Context Files " + self.sessionID, 
                expires_after={"days": 2, "anchor": "last_active_at"},
            )
            self.vector_store_id = vector_store.id
        
        # Create temp file with data to upload to thread
        file_path = create_temp_file(json.dumps(sessionContext).encode('utf-8'), self.sessionID + "_context.json")
        file_stream = open(file_path, "rb")
        
        # Delete old files uploaded attached to the vector store and uploaded
        self.delete_session_files()
        
        # Create new file batch and upload to vector store
        # It is better to create the file separately, then add to vector store and poll
        # That way you have control over the chunking strategy and can play around with it.
        uploaded_file = self.client.files.create(file=file_stream, purpose="assistants") # file size up to 512 MB
        file_id = uploaded_file.id
        self.client.files.wait_for_processing(id=file_id)
        if uploaded_file.status == "error":
            # Error
            print(f"assistants_handler.py: Error: File failed to upload")
            exit(1)
        self.client.beta.vector_stores.files.create(self.vector_store_id, file_id=file_id, extra_body={
            "chunking_strategy": {
                "type": "static",
                "static": {
                    "max_chunk_size_tokens": 4096,
                    "chunk_overlap_tokens": int(4096/2) # max overlap tokens
                }
            }
        } )
        self.client.beta.vector_stores.files.poll(vector_store_id=self.vector_store_id, file_id=file_id)

        # Create new thread and attach vector store to it
        thread = self.client.beta.threads.create(
            tool_resources={
                "file_search":{
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )
        self.thread_id = thread.id

    def get_response(self, input: str):
        """
        Adds message to the thread and creates a Run.
        Runs indicate to an Assistant it should look at the messages in the Thread and take action: either by adding a single response, or using tools.
        
        We don't care about context or an init message because the Assistant itself holds the context.
        """

        user_message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=f"{input.strip()}",
        )
        
        # Create a Run
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant.id,
            additional_instructions="Ignore any file beginning with a '.', or any file in a folder starting with a '.', like .git or .ssh for example. When the user asks about anything related to a file/folder's time, use the lastModified value of the respective file/folder. Answer the query by looking at the uploaded file content."
        )
        self.run = run
        
        # Runs are async, so we have to wait til it completed processing
        self.wait_on_run()
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread_id,
            run_id=self.run.id
        )
        print("Thread ID:", self.thread_id)
        print("Run steps:")
        for step in run_steps.data:
            show_json(step.step_details)

        # List the Messages in the Thread to see what got added by the Assistant.
        # Listed from oldest first (asc), and filter only messages after the user message.
        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id, order="asc", after=user_message.id)
        
        message_response = []
        for message in messages:
            # print(message)
            if message.content[0].type == 'text':
                message_response.append(message.content[0].text.value)
            if message.content[0].type == 'image_url':
                message_response.append(message.content[0].image_url.url)
            if message.content[0].type == 'image_file':
                message_response.append("File ID: " + message.content[0].image_file.file_id)
        if not message_response:
            return "Error occurred. Please repeat your message."

        # combine messages
        combined_message = ' '.join(message_response)
        return combined_message

    
    def wait_on_run(self):
        while self.run.status == "queued" or self.run.status == "in_progress":
            # print("Run status: ", self.run.status)
            self.run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=self.run.id,
            )
            time.sleep(0.5)

    def delete_vectore_stores(self):
        vector_stores = self.client.beta.vector_stores.list(order="desc", limit=100)
        ctr = 1
        for store in vector_stores:
            # delete it
            self.client.beta.vector_stores.delete(store.id)
            ctr += 1
        print(f"deleted {ctr-1} vector stores")

    def delete_files(self):
        files = self.client.files.list(purpose="assistants")
        ctr = 1
        for file in files:
            # delete it
            self.client.files.delete(file.id)
            ctr += 1
        print(f"deleted {ctr-1} files")

    
    def delete_session_files(self):
        files = self.client.files.list(purpose="assistants")
        ctr = 1
        for file in files:
            # delete it
            file_session = file.filename.split("_")
            if file_session[0] == self.sessionID:
                self.client.files.delete(file.id)
            ctr += 1
        print(f"deleted {ctr-1} old files")

    def get_thread_messages(self, thread_id: str):
        """
        Helper to save thread messages, given you know the thread id
        """
        thread_messages = self.client.beta.threads.messages.list(thread_id, order='asc', limit=100)
        content = []
        for message in thread_messages.data:
            if message.role == 'assistant':
                speaker = "Datadude:\t\t"
            else:
                speaker = "Me:\t\t\t\t\t"
            
            if message.content[0].type == 'text':
                content.append(speaker + message.content[0].text.value)
            if message.content[0].type == 'image_url':
                content.append(speaker + message.content[0].image_url.url)
            if message.content[0].type == 'image_file':
                content.append(speaker + "File ID: " + message.content[0].image_file.file_id)
            
        return content

