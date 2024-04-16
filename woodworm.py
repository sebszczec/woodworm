from irc import irc_service


def main():
    irc_connection = irc_service.IRCConnection('open.ircnet.net', 6667, 'woodworm', '#vorest')
    irc_connection.connect()
    irc_connection.listener()

if __name__ == "__main__":
    main()
