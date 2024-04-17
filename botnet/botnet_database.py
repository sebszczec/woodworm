class BotnetDatabase:
    def __init__(self):
        self.botnet = {}

    def add_bot(self, bot):
        self.botnet[bot.get_id()] = bot

    def remove_bot(self, bot):
        del self.botnet[bot.get_id()]

    def get_bots(self):
        return self.botnet

    def get_bot(self, bot_id):
        return self.botnet.get(bot_id)
    
    def get_bot_by_ircknick(self, irc_nick):
        for bot in self.botnet.values():
            if bot.get_irc_nick() == irc_nick:
                return bot
        return None
    
    def is_empty(self):
        return len(self.botnet) == 0
    
    def is_bot_present(self, bot_id):
        return bot_id in self.botnet
