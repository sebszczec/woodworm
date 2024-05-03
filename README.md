<h1>Woodworm</h1>
Botnet using an IRC server as a DNS-type hub.

Description:
<ul>
  <li>IRC</li>
  <li>TCP</li>
  <li>FTP</li>
</ul><br/>

<b>IRC</b><br/><br/>
Each node (<i>woodworm</i>) is connected to an IRC server and channel defined in config.cfg file. When someone joins the channel <i>woodworm</i> sends a BROADCAST message. As a response to this request all <i>woodworms</i> send SPREAD message containing their IP and TCP server port they host; <i>woodworms</i> store this data in internal bot database. <br />
IRC JOIN -> BROADCAST -> SPREAD -> store bot information <br/><br/>

When someone quits channel <i>woodworm</i> checks if this is a bot in his dababes, if so - it removes it.<br/>
IRC PART/QUIT -> remove bot information <br /><br />

IRC commands handled by <i>woodworm</i> when asked directly:
<ul>
  <li>HELP - list of available commands</li>
  <li>LS - list of file in storage (storage directory is defined in config.cfg gile)</li>
  <li>STAT file - prints file details</li>
  <li>STATUS - list of bots stored in botnet database</li>
  <li>SEND bot file - send a file to a bot using TCP connection</li>
</ul>
