# Woodworm

A distributed botnet framework using an IRC server as a command and control hub.

## Overview

Woodworm is a decentralized network where each node (woodworm instance) communicates through an IRC server to coordinate file distribution and command execution across the botnet. The system supports three main communication channels:

- **IRC**: Command and control through IRC server
- **TCP**: Direct peer-to-peer connections between nodes
- **FTP**: File management and storage

## Features

### IRC Protocol

Each woodworm node connects to a configured IRC server and channel. The IRC connection manages botnet coordination:

- **Node Discovery**: When a node joins the channel, it sends a `BROADCAST` message. All active nodes respond with a `SPREAD` message containing their IP address and TCP port, which are stored in the local botnet database
- **Node Removal**: When a node leaves (PART/QUIT), it's removed from all botnet databases
- **Message Flow**: `IRC JOIN` → `BROADCAST` → `SPREAD` → store bot information

#### Available IRC Commands

- `HELP` - Display available commands
- `LS` - List files in local storage
- `STAT <file>` - Print file details and information
- `STATUS` - Display all registered bots in the botnet database
- `SEND <bot> <file>` - Send a file to another bot using TCP connection
- `WGET <file>` - Download a file from a web URL

### TCP Protocol

Each woodworm instance acts as both a TCP server and client, creating a mesh network between nodes. TCP connections consist of two separate socket connections: one for command exchange and one for binary data transfer.

#### Connection Types

**TCP Session**: A client-to-server connection (e.g., `TCP AB` means Client A connects to Server B)

**Reversed TCP Session**: A server-to-client connection (e.g., `R-AB` means Server B connects back to Client A)

#### Connectivity Scenarios

**Scenario 1: Bidirectional Connection (A ↔ B)**
- Client A ↔ Server B: `TCP AB` (commands and data) + `R-AB` (reverse connection)
- Client B ↔ Server A: `TCP BA` (commands and data) + `R-BA` (reverse connection)
- File A→B uses `TCP AB`; File B→A uses `TCP BA`

**Scenario 2: Unidirectional - A Behind Firewall (A → B)**
- Client A connects to Server B: `TCP AB` + `R-AB` (reverse connection)
- Client B cannot connect to Server A (firewall blocks)
- File A→B uses `TCP AB`; File B→A uses `R-AB`

**Scenario 3: Unidirectional - B Behind Firewall (A ← B)**
- Client B connects to Server A: `TCP BA` + `R-BA` (reverse connection)
- Client A cannot connect to Server B (firewall blocks)
- File A→B uses `R-BA`; File B→A uses `TCP BA`

### FTP Protocol

Each woodworm instance runs an FTP server for file management:

- Upload files to the node's local storage
- Remove files from storage
- Configured via `config.json` with custom credentials and passive port range

## Installation

### Prerequisites

- Python 3.7+
- Required Python packages: `pyftpdlib>=1.7.0`, `requests>=2.28.0`

### Setup

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.json` file in the project root:

```json
{
    "general": {
        "pathToFiles": "/path/to/storage",
        "fileListRefreshTime": 60,
        "syncFiles": true,
        "fileSyncTime": 65,
        "tcpPort": 3000
    },
    "irc": {
        "nick": "woodworm_instance",
        "channel": "#botnet",
        "domain": "example.com",
        "server": "irc.example.com",
        "port": 6667
    },
    "ftp": {
        "port": 3021,
        "passiveRangeStart": 60000,
        "passiveRangeStop": 65535,
        "user": "woodworm",
        "password": "secure_password"
    }
}
```

### Configuration Parameters

**General Settings:**
- `pathToFiles`: Directory for file storage and synchronization
- `fileListRefreshTime`: Interval (seconds) to refresh local file list
- `syncFiles`: Enable automatic file synchronization across nodes
- `fileSyncTime`: Interval (seconds) for file sync operations
- `tcpPort`: Port for TCP server operations

**IRC Settings:**
- `nick`: Nickname for this node on the IRC server
- `channel`: IRC channel to join
- `domain`: Domain identifier for the node
- `server`: IRC server address
- `port`: IRC server port

**FTP Settings:**
- `port`: FTP server port
- `passiveRangeStart` / `passiveRangeStop`: Passive mode port range
- `user`: FTP username
- `password`: FTP password

## Usage

```bash
# Run with default config.json
python main.py

# Run with custom config file
python main.py config_custom.json

# Run as docker
docker compose build # will download code from repository, does not use local code
docker compose run --rm stock-monitor

```

## Important Notes

⚠️ **Firewall Configuration**: All ports configured in `config.json` (TCP, FTP, IRC) must be accessible through your firewall for proper operation.

## License

MIT License - Copyright (c) 2024 sebszczec
