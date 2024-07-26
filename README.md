## Requirements

- Python 3.10+
- discord.py
- mcrcon
- sqlite3

## Before Running

- open `statics.py`
	- insert your bot_token
	- insert user_ids of the authorized users to use the commands

## Available Commands

```
- /add <NAME> <IP> <ROCNPORT> <RCONPASSWORD> => adds a server to the DB
- /edit <NAME> OPTIONAL: <IP> <ROCNPORT> <RCONPASSWORD> => edits an existing server
- /delete <NAME> => deletes a server from DB
- /list => lists all servers, their name, ip, port and password
- /rcon <NAME/ALL> <COMMAND> => sends a Rcon command to the selected/all server/s
```