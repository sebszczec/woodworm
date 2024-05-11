import random

class BotnetDatabase:
    def __init__(self):
        self.botnet = {}

    def add_bot(self, bot):
        self.botnet[bot.get_ircNick()] = bot

    def remove_bot(self, bot):
        del self.botnet[bot.get_ircNick()]

    def get_bots(self):
        return self.botnet

    def get_bot(self, ircNick):
        return self.botnet.get(ircNick)
    
    def get_random_bot(self):
        if not self.is_empty():
            return random.choice(list(self.botnet.values()))
        else:
            return None
    
    def is_empty(self):
        return len(self.botnet) == 0

