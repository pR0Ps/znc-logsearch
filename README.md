znc-logsearch
=============
znc-logsearch is a [ZNC][] module. It allows users to search the log files made by the
[log module][] from any client.

Requirements
------------
 - The ZNC server must be running ZNC v1.6.0 or later.
 - The ZNC server must have the [log module][] enabled using the default configuration
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
The channel/user portion of the command uses normal globbing rules ("*" matches anything).
The query is fed directly into "grep -i" and uses normal regex rules (".*" matches anything).

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
+==================+===========================================================+
| Command          | Result                                                    |
+==================+===========================================================+
| #hi hi           | Messages in the #hi channel saying "hi"                   |
+------------------+-----------------------------------------------------------+
| @NickServ .*     | Any private messages to/from NickServ                     |
+------------------+-----------------------------------------------------------+
| @* hello         | Any private messages saying "hello"                       |
+------------------+-----------------------------------------------------------+
| #* znc           | Mentions of ZNC in any channel                            |
+------------------+-----------------------------------------------------------+
| #znc* testing    | Messages in channels starting with "znc" saying "testing" |
+------------------+-----------------------------------------------------------+
| * znc            | Mentions of ZNC in any logs (channel or private message)  |
+------------------+-----------------------------------------------------------+
| * ] \* .* dances | Dancing users in any logs                                 |
+------------------+-----------------------------------------------------------+
| * .*             | Any messages in any logs                                  |
+==================+===========================================================+
```

Local testing
-------------
It's possible to test the majority of the functionality of this module without having ZNC installed.
Running `./testlocal.py` will perform a search over the `moddata/log` directory in the local
directory.

This folder should have the same structure as the `moddata/log` folder that the ZNC `log` module
produces when loaded as a global module in ZNC.

License
-------
Licensed under the GNU General Public License v3.0

 [ZNC]: https://znc.in
 [log module]: https://wiki.znc.in/Log
 [`shell=True`]: https://docs.python.org/3/library/subprocess.html#security-considerations
 [`modpython`]: http://wiki.znc.in/Modpython
