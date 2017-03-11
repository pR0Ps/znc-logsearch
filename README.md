znc-logsearch
=============
znc-logsearch is a [ZNC][] module. It allows users to search the log files made by the
[log module][] from any client.

Requirements
------------
 - The ZNC server must have the [log module][] enabled for there to be any logs to search.
 - The ZNC server must have `grep` on the PATH of the user ZNC is running under.

Warning
-------
This executes commands on the ZNC server based on user input.

Requested channel/user names are checked for potential directory traversal. The paths of the files
to search are gathered in pure Python (using the `glob` module) and fed into `grep` WITHOUT using
the [`shell=True`][] argument.

With that being said, I make no guarantees that this is foolproof, use this module at your own risk.

Installation
------------
1. Make sure [`modpython`][] is loaded
2. Copy `logsearch.py` into the ZNC modules directory.
3. Load the module using `/msg *status loadmodule logsearch`
   - By default the module is loaded at the global level which allows all users to use it
   - To load the module at the user level instead use `/msg *status loadmodule --type=user logsearch`

Usage
-----
```
logsearch: Search ZNC logs and return the results

The functionality of this module is provided by shell globbing and grep.
This means that the channel/user portion of the command obeys normal globbing rules.
The query is fed directly into "grep -i", which means that normal regex is supported.

Commands:
+====================+========================================+
| Command            | Description                            |
+====================+========================================+
| ?/help             | Shows the help text                    |
+--------------------+----------------------------------------+
| * <query>          | Search all logs for <query>            |
+--------------------+----------------------------------------+
| #<channel> <query> | Search logs in <channel> for <query>   |
+--------------------+----------------------------------------+
| @<user> <query>    | Search logs to/from <user> for <query> |
+====================+========================================+

Examples:
+==================+====================================================+
| Command          | Result                                             |
+==================+====================================================+
| #hi hi           | Search for messages in the #hi channel saying "hi" |
+------------------+----------------------------------------------------+
| @* hello         | Search for any private messages saying "hello"     |
+------------------+----------------------------------------------------+
| #* znc           | Search for mentions of ZNC in any channel          |
+------------------+----------------------------------------------------+
| * znc            | Search all channel and user logs for znc           |
+------------------+----------------------------------------------------+
| #znc* testing    | Search channels starting with "znc" for "testing"  |
+------------------+----------------------------------------------------+
| * ] \* .* dances | Search all logs for dancing users                  |
+==================+====================================================+
```

License
-------
Licensed under the GNU General Public License v3.0

 [ZNC]: https://znc.in
 [log module]: https://wiki.znc.in/Log
 [`shell=True`]: https://docs.python.org/3/library/subprocess.html#security-considerations
 [`modpython`]: http://wiki.znc.in/Modpython
