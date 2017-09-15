#!/usr/bin/env python3

import glob
import itertools
import operator
import os
import re
import subprocess
import sys
import traceback
import unicodedata

import znc


def debug(func):
    """Causes the wrapped function to log errors to the client

    WARNING: Leaks loads of data, ONLY use this for debugging
    """
    def debug_wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            self.PutModule("{0.__class__.__name__}: {0}".format(e))
            tb_text = traceback.format_tb(sys.exc_info()[2])
            for x in tb_text:
                self.PutModule(x)
            raise
    return debug_wrapper


class logsearch(znc.Module):
    description = "Search ZNC logs and return the results"
    module_types = [znc.CModInfo.GlobalModule, znc.CModInfo.UserModule]

    NUM_RESULTS = 30
    RESULTS_RE = re.compile("^.*/(?P<channel>.*?)/(?P<date>[0-9-]*)\.log:\[(?P<time>.*?)\] (?P<msg>.*)$")
    RESULTS_FMT = "{channel} [{date} {time}]: {msg}"

    HELP = (
        "The functionality of this module is provided by shell globbing and grep.",
        "The channel/user portion of the command uses normal globbing rules (\"*\" matches anything).",
        "The query is fed directly into \"grep -i\" and uses normal regex rules (\".*\" matches anything)."
    )
    CMDS = (
        ('?/help', 'Shows the help text'),
        ('* <query>', 'Search all logs for <query>'),
        ('#<channel> <query>', 'Search logs in <channel> for <query>'),
        ('@<user> <query>', 'Search logs to/from <user> for <query>')
    )
    EXAMPLES = (
        ('#hi hi', 'Messages in the #hi channel saying "hi"'),
        ('@NickServ .*', 'Any private messages to/from NickServ'),
        ('@* hello', 'Any private messages saying "hello"'),
        ('#* znc', 'Mentions of ZNC in any channel'),
        ('#znc* testing', 'Messages in channels starting with "znc" saying "testing"'),
        ('* znc', 'Mentions of ZNC in any logs (channel or private message)'),
        ('* ] \* .* dances', 'Dancing users in any logs'),
        ('* .*', 'Any messages in any logs')
    )

    def get_files(self, path_fmts, user, network, channel):
        paths = (f.format(user=user, network=network, channel=channel) for f in path_fmts)
        files = itertools.chain(*[glob.glob(p) for p in paths])
        # Sort by date (the filename)
        return sorted(files, key=os.path.basename, reverse=True)

    def do_search(self, channel, query):
        """Uses grep to search logs"""

        user = self.GetUser()
        network = self.GetNetwork()

        path_fmts = [
            # Support log module at global, user, and network level
            os.path.join(znc.CZNC.Get().GetZNCPath(), "moddata", "log",
                         "{user}", "{network}", "{channel}", "*.log"),
            os.path.join(user.GetUserPath(), "moddata", "log",
                         "{network}", "{channel}", "*.log"),
            os.path.join(network.GetNetworkPath(), "moddata", "log",
                         "{channel}", "*.log")
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

        cmd = ["grep", "-i", "--text", "--with-filename", "-e", query]
        cmd.extend(files)

        # Start the search, pull results out until we have enough to display
        ret = []
        code = 0
        stopping = None
        partial_results = True
        try:
            p = subprocess.Popen(cmd, stderr=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE)
        except OSError as e:
            self.PutModule("ERROR calling grep (is it available on the path?)")
            return

        for num, line in enumerate(p.stdout):
            line = line.decode("utf-8", errors="replace").rstrip()
            data = self.RESULTS_RE.match(line).groupdict()

            if stopping is not None and stopping != data["date"]:
                p.terminate()
                break

            if num >= self.NUM_RESULTS:
                stopping = data["date"]

            ret.append(data)
        else:
            partial_results = False
            code = p.wait()

        if not ret or code == 1:
            self.PutModule("No matches found")
            return
        elif code != 0:
            self.PutModule("ERROR searching logs (return code {} from grep)".format(code))
            return

        return ret, partial_results

    def limited_results(self, results):
        """Remove the oldest entries to stay within the output limit

        Returns the results sorted by channel/date/time for display
        """
        if len(results) > self.NUM_RESULTS:
            results = sorted(results, key=operator.itemgetter('date', 'time'),
                             reverse=True)[:self.NUM_RESULTS]
        return sorted(results, key=operator.itemgetter('channel', 'date', 'time'))

    def show_help(self):
        self.PutModule("{0.__class__.__name__}: {0.description}\n".format(self))
        for h in self.HELP:
            self.PutModule(h)
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

    #@debug
    def OnModCommand(self, cmd):
        """Process commands sent to the module"""
        cmd = unicodedata.normalize('NFKC', cmd).strip()
        if not cmd or " " not in cmd \
                or cmd in {"?", "help"} \
                or cmd[0] not in "*#@" \
                or (cmd[0] == "*" and not cmd.startswith("* ")):
            self.show_help()
            return

        channel, query = cmd.split(" ", 1)
        temp = self.do_search(channel, query)
        if temp:
            results, partial = temp

            for r in self.limited_results(results):
                self.PutModule(self.RESULTS_FMT.format(**r))
            if partial or len(results) > self.NUM_RESULTS:
                self.PutModule("Some earlier results not shown")
