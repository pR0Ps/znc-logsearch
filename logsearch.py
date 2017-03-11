import glob
import itertools
import os
import re
import subprocess
import unicodedata

import znc

class logsearch(znc.Module):
    description = "Search ZNC logs and return the results"
    module_types = [znc.CModInfo.GlobalModule, znc.CModInfo.UserModule]

    NUM_RESULTS = 10
    RESULTS_RE = re.compile("^.*/(?P<channel>.*?)/(?P<date>[0-9-]*)\.log:\[(?P<time>.*?)\] (?P<msg>.*)$")
    RESULTS_FMT = "{channel} [{date} {time}]: {msg}"

    CMDS = (
        ('?/help', 'Shows the help text'),
        ('* <query>', 'Search all logs for <query>'),
        ('#<channel> <query>', 'Search logs in <channel> for <query>'),
        ('@<user> <query>', 'Search logs to/from <user> for <query>')
    )
    EXAMPLES = (
        ('#hi hi', 'Search for messages in the #hi channel saying "hi"'),
        ('@* hello', 'Search for any private messages saying "hello"'),
        ('#* znc', 'Search for mentions of ZNC in any channel'),
        ('* znc', 'Search all channel and user logs for znc'),
        ('#znc* testing', 'Search channels starting with "znc" for "testing"'),
        ('* ] \* .* dances', 'Search all logs for dancing users')
    )

    def get_files(self, path_fmts, user, network, channel):
        paths = (f.format(user=user, network=network, channel=channel) for f in path_fmts)
        files = itertools.chain(*[glob.glob(p) for p in paths])
        return files

    def do_search(self, channel, query):
        """Uses grep to search logs"""

        user = self.GetUser()
        network = self.GetNetwork()

        path_fmts = [
            # Support log module at global, user, and network level
            os.path.join(znc.CZNC.Get().GetZNCPath(), "moddata", "log", "{user}", "{network}", "{channel}", "*.log"),
            os.path.join(user.GetUserPath(), "moddata", "log", "{network}", "{channel}", "*.log"),
            os.path.join(network.GetNetworkPath(), "moddata", "log", "{channel}", "*.log")
        ]

        disp_channel = channel
        channel = channel.lower()
        user_name = user.GetUserName().lower()
        network_name = network.GetName().lower()

        # Collect all the log files to be searched
        if channel != "*":
            chan_type = "channel" if channel.startswith("#") else "user"
            if os.sep in channel:
                self.PutModule("Invalid {} name".format(chan_type))
                return

            # Strip "@" from start of username
            if chan_type is "user":
                channel = "[!#]{}".format(channel[1:])

            files = self.get_files(path_fmts, user_name, network_name, channel)
            if not files:
                self.PutModule("No log files for {} '{}' found".format(chan_type, disp_channel))
                return

            self.PutModule("Results of searching the logs of {}s matching '{}' for '{}':".format(chan_type, disp_channel, query))
        else:
            files = self.get_files(path_fmts, user_name, network_name, "*")
            if not files:
                self.PutModule("No log files found (have you enabled the log module?)")
                return

            self.PutModule("Results of searching all logs for '{}':".format(query))

        cmd = ["grep", "-i", query]
        cmd.extend(files)

        p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = (x.decode("utf-8") for x in p.communicate())
        code = p.returncode

        if code == 1:
            self.PutModule("No matches found")
            return
        elif code != 0:
            self.PutModule("ERROR searching logs (return code {}):".format(code))
            self.PutModule(err)

        return [self.RESULTS_FMT.format(**self.RESULTS_RE.match(x).groupdict()) for x in out.splitlines()]

    def show_help(self):
        self.PutModule("{0.__class__.__name__}: {0.description}".format(self))
        self.PutModule("\nThe functionality of this module is provided by shell globbing and grep.")
        self.PutModule("This means that the channel/user portion of the command obeys normal globbing rules.")
        self.PutModule("The query is fed directly into \"grep -i\", which means that normal regex is supported.")

        self.PutModule("\nCommands:")
        tbl = znc.CTable()
        tbl.AddColumn("Command")
        tbl.AddColumn("Description")
        for k, v in self.CMDS:
            tbl.AddRow()
            tbl.SetCell("Command", k)
            tbl.SetCell("Description", v)
        self.PutModule(tbl)

        self.PutModule("\nExamples:")
        tbl = znc.CTable()
        tbl.AddColumn("Command")
        tbl.AddColumn("Result")
        for k, v in self.EXAMPLES:
            tbl.AddRow()
            tbl.SetCell("Command", k)
            tbl.SetCell("Result", v)
        self.PutModule(tbl)

    def OnModCommand(self, cmd):
        """Process commands sent to the module"""
        cmd = unicodedata.normalize('NFKC', cmd).strip()
        if not cmd or " " not in cmd or cmd in ("?", "help") or cmd[0] not in "*#@":
            self.show_help()
            return

        channel, query = cmd.split(" ", 1)
        try:
            results = self.do_search(channel, query)
        except Exception as e:
            self.PutModule("{0.__class__.__name__}: {0}".format(e))
            return

        if results:
            num = len(results)
            for r in results[:self.NUM_RESULTS]:
                self.PutModule(r)
            if num > self.NUM_RESULTS:
                self.PutModule("{} more results not shown".format(num - self.NUM_RESULTS))
