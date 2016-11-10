#!/usr/bin/python

from slackclient import SlackClient
import ConfigParser
import sys


class SlackBot:

    def __init__(self, **kwargs):
        self.channel = kwargs["channel"]
        self.slack_client = SlackClient(kwargs["api_token"])
        self.severity_levels = {"Average" :   "warning",
                                "High"    :   "warning",
                                "Warning" :   "warning",
                                "Disaster":   "danger"}

    def api_call(self, call, *args, **kwargs):
        "Sends API call to Slack and raises exception on error"
        api_response = self.slack_client.api_call(call, *args, **kwargs)
        if not api_response["ok"]:
            raise RuntimeError(api_response["error"])

    def send(self, to, message, severity):
        if self.slack_client.rtm_connect():
            if to != "null":
                if to == "channel":
                    to = "<!channel>"
                else:
                    to = "<@%s>" % to
                message = "%s: %s" % (to, message)
            attachment = dict()
            attachment["text"] = message
            attachment["fallback"] = message
            color = "good"
            if severity and severity in self.severity_levels:
                color = self.severity_levels[severity]
            attachment["color"] = color
            self.api_call("chat.postMessage", channel=self.channel,
                           attachments=[attachment], as_user=True)
        else:
            raise RuntimeError("Connection failed")


if __name__ == "__main__":
    (to, severity, message) = sys.argv[1:]
    config = ConfigParser.ConfigParser()
    config.read("/usr/lib/zabbix/scripts/conf/notifier.conf")
    bot = SlackBot(api_token=config.get("DEFAULT", "api_token"),
                   channel=config.get("DEFAULT", "channel"))
    bot.send(to, message, severity)
