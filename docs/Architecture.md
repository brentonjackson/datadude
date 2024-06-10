# System Architecture

DataDude is a client-server system. The server is managed by the system, and the user can instantiate clients anywhere to start a session.

## Architecture Overview

1.	Server:
    - Manages overall state and client connections.
    - Performs operations such as file analysis, optimization, and collaboration features.
    - Exposes APIs for clients to interact with.
    - Run as a system service.
2.	Clients:
    - Connect to the server via sockets
    - Interacts with the server by having a chat conversation.
    - Can be instantiated from the terminal or through an app
    - ~~Opens a chat window for each session~~

## Technologies

- **Server**: Python, ~~SQLite~~
- **Client**: ~~ElectronJS, SocketIO~~ Python