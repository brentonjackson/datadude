# Experiments

## Experiment 1 - Chat Completions API ❌

#### Setup:
- Flask server
- Flask client

#### Procedure:
1. Server starts and listens on port 5000
2. Client sends server POST request to start session w/ file path in body
3. Server receives client request to start a session. Server creates UUID for the session, creates an entry into the message pool for the session, saves the context to be used by the AI, then sends the sessionID back to client.
4. Client gets session ID, then uses it to send message to server at POST /chat/sessionID.
5. Server receives message, asks AI what response to send back, then sends the response back to the client. This is the conversation.

This experiment just sends file data as json context to the chat completions API as a system messsage.

Subsequent messages use that context to answer questions about the directory.
For right now, I'm not including any git info functionality. Just info about the directory.

#### Background Info: Chat Completions API Overview
The primitives of the Chat Completions API are Messages, on which you perform a Completion with a Model (gpt-3.5-turbo, gpt-4, etc). 

It is lightweight and powerful, but inherently stateless, which means you have to manage conversation state, tool definitions, retrieval documents, and code execution manually.

#### Analysis:
It worked quite okay. But unfortunately, I realized it was treating the messages as one-offs and we were not having a conversation so this didn't work.

#### Conclusion:
I need to use threads. The messages should further enhance the model's information about the environment. I will start that experiment tomorrow.



## Experiment 2 - Assistants API ❌

#### Setup:
- Flask server brokers messages between client/AI Assistant
- Flask client sends messages

#### Procedure:
1. Server starts and listens on port 5000
2. Client sends server POST request to start session w/ file path and folder state in body
3. Server receives client request to start a session. Server creates UUID for the session and new thread, creates an entry into the message pool for the session/thread, sends some context to the AI model using the Assistants API, then sends the sessionID/threadID back to client.
   1. The Assistant only needs to be created once period, irregardless of the session.
4. Client gets session ID/thread ID, then uses it to send message to server at POST /chat/sessionID.
5. Server receives message, asks AI what response to send back, then sends the response back to the client. This is the conversation.

This experiment sends context on first request from the client, which is sent to the assistant and can be used as a basis for the session. If there is an update, it's the client's responsibility to send those updates in the query (hopefully they're small).

The context will be saved in one file, with a set, deterministic structure. It shall be formatted in JSON and saved as a JSON document to the vector store. If it's above a certain size, we'll figure out how to reduce that size, likely by splitting each object (files info, folder info, git info) into different json files.

#### Background Info: Assistants API Overview
A typical integration of the Assistants API has the following flow:

1. Create an Assistant by defining its custom instructions and picking a model. If helpful, add files and enable tools like Code Interpreter, File Search, and Function calling.
2. Create a Thread when a user starts a conversation.
3. Add Messages to the Thread as the user asks questions.
4. Run the Assistant on the Thread to generate a response by calling the model and the tools.

For this experiment, it became apparent that I needed to create an AI base class and make separate classes for the different AI methods used, so they can be easily swapped in and out.

The primitives of the Assistants API are

- Assistants, which encapsulate a base model, instructions, tools, and (context) documents,
- Threads, which represent the state of a conversation, and
- Runs, which power the execution of an Assistant on a Thread, including textual responses and multi-step tool use.

Even though you're no longer sending the entire history each time, you will still be charged for the tokens of the entire conversation history with each Run. Therefore, best practice to stay cheap is to make a new thread for each conversation, not use one thread for each directory. This makes sense anyway because you only need one assistant period. You can use the same assistant for different folders. And different threads have different context as well. With this method, though, I will need to send some context to the assistant initially each time - and possiby delete that context or name it so that it can be retrieved by folder name.

I persist the session IDs to keep the state of the folder, so maybe I save the documents/context prepended by session ID attached to the assistant's files. Then threads are always independent of the session ID.

Is this a conflict? Each instance has different threads even on the same folder on the AI side, but on my server side, each instance has a shared object that includes all the messages sent... at least while the server is up since they're stored in-memory, but still.

Maybe on server side, I have a threads array, which contains a list of objects representing threads. Those thread objects have the messages array which contains all the messages for the individual session instance. That would be more consistent, and help me to understand individual sessions better anyway. And it makes sense to separate messages into distinct threads, because sometimes I may just wanna bullshit, have fun. That shouldn't effect other times when I need legitimage information.


Process:
1. Create session for directory. All client instances/threads share the same session context.
2. Session calls on common datadude assistant, but makes a new thread both for each session, and for each client instance. The assistant, however, can only tell the difference between threads attached to it. So it can start a new thread while using the same uploaded files. Files are the mechanism in which I upload/transfer session context to the assistant for it to use.
   1. I could name files in a way that separates sessions. For example, naming the file(s) with the context prepended with the root folder name, or prepended with the session ID. That way the session can share them, even though the assistant sees different threads
   2. With the above idea, each session spawns an assistant handler instance which runs the same AI assistant of course (DataDude). This is always the case. But in the setup of the handler, we create a new thread, since each client instance represents a new thread. Sessions are unknown to the assistant.
   3. When creating the thread, it makes sense to upload the session/folder context for it on setup. That presumes that if the session was already created, I don't need to make a new handler and I don't need to go through the setup again. I just use the message method on the handler already attached to the session.
   4. Only call the setup when creating a new session, and prepend the session ID to the files being uploaded.
   5. This works out becaues the Assistants API lets you upload files to a vector store that's attached to the assistant, but also let's you create vector stores based on the thread. So if you need to update anything, you can add it to the thread itself as a sort of temporary context that's not attached to anything else. This could be useful for things like the same repo, but different branches... Yeah, threads should be kept separate due to the same session potentially having different data because they're on different branches. In this vein, could it be better to just have the thread itself upload context?
   6. I say no, it's still good to upload some initial context to the assistant - general, basic things that could span across different branches that are true of the folder and system itself. Then for each thread, upload more and more specific context. It's okay to upload specific context immediately as well, since the thread's context will overrule it anyways... vector stores created on threads shouldn't persist long.

#### Analysis:
- It takes 3 seconds after every single query. Quite a bit longer time it seems. I'll have to test this.

#### Conclusion:
It's significantly better than chat completions API due to persistent state. But it still answers with randomness and just gets things wrong, like it's ignoring the uploaded data.
If I prompt it again to check the source, it corrects itself, but that's not ideal.


## Experiment 3 - Fine-tuning Assistants API ✅

#### Setup:
- Flask server brokers messages between client/AI Assistant
- Flask client sends messages

#### Procedure:
1. Update the parameters on the Assistant
2. Add more messages at the beginning of the thread to help guide the assistant.

I specifically added the temperature parameter to the Assistant. This is a value between 0 and 2 that makes the model more deterministic closer to 0 and more random closer to 2. I think the default value was 1.

#### Analysis:
- This significantly improved the performance of the AI assistant.
- An unexpected result of the tuning has been that the model computes and returns answers to me much, much faster. It actually can comete (still loses) with the Chat Completions API now.

#### Conclusion:
This experiment resulted in very passing performance for the Assistants API backend. I will continue using this moving forward. It's good to know that the performance of these models can be improved significantly with tuning and messing with various parameters until it works.

## Experiment 4 - Sending File Content to Assistants API ❌

#### Setup:
- Flask server brokers messages between client/AI Assistant
- Flask client sends messages

#### Procedure:
1. Add content to the context

It got ridiculously expensive. The amount of tokens when sending content easily shoots into the tens and hundreds of millions. So I decided to gzip and base64 encode.
The only issue is the Python code interpretor in OpenAI's sandboxed environment has trouble decoding and decompressing this.
I've tinkered with the prompts to instruct it on how to write Python code to resolve this issue, but it just can't seem to load the entire data structure into memory. It tries to parse the data to get the content first, when it should load the data and then read the content as bytes, instead of a string.

#### Analysis:
- This didn't work when trying to compress and encode the data.

#### Conclusion:
This experiment showed me the limitations and preferences of the code interpreter tool. Instead of doing things the right way, it will try to do things in the way it wants, and can't derive the right way because it's limited by the system it's running on. It's like a Jupyter notebook, which isn't ideal for any kind of systems programming, which it's why they say it's a sandboxed execution environment. That's code for, your code has no control over the system at all.

On the bright side, it did well when reading markdown files that were sent as plain text, not bytes.

Will just have to think of another way to upload code context at scale.

## Experiment 5 - Sending File Content to Assistants API ✅

#### Setup:
- Flask server brokers messages between client/AI Assistant
- Flask client sends messages

#### Procedure:
1. Add content to the context, but don't compress or encode.
2. Only add file content for .md or .py files.

It turns out that I had a bug in my omit logic where the .dudeignore wasn't working as expected. That was resolved and things got significantly more economical, even though I didn't compress or encode the file contents. And what I would lose due to sheer volume of data, I probably gained in terms of speed and not having to use the code interpreter tool to process everything before answering.
After a ton of testing from the last experiment to this one, I used about 10-12 cents on the API.

#### Analysis:
- The assistant responds relatively fast and is able to have a conversation about the same data.
- One drawback is that it doesn't really seem to look at all of the data at once when responding to a question. It seems to still depend on you being very specific. The more specific the better, and the less specific, the more you will have to do to prove it wrong yourself and keep the conversation on track and honest.
- Also, adding files to reference seems to make the queries take a little longer.

#### Conclusion:
I uploaded Python files as well as Markdown files. Uploading the Python file content in the context is extremely useful, much more useful than file metadata and a good amount more than markdown. It allowed me to really look at the functions and ask about it as if I had a genius tutor over my shoulder the whole way. I was even able to argue with it and change its mind, and it still gave very valuable positions no matter the side it was on. This is useful enough as it is right now to me. It's in a great spot.

## Experiment 6 - Making Retrieval Augmented Generation More Reliable

#### Setup:
- Flask server brokers messages between client/AI Assistant
- Flask client sends messages

### Goal:
- Be able to upload a codebase and for it to know the all the python or js files in the codebase and put it in a list, reliably.
- Be able to use the previous list to go into each file and do something with the file contents.

#### Procedure:
1. Add content to the context, but don't compress or encode.
2. Only add file content for .md or .py files.


#### Analysis:


#### Conclusion:








