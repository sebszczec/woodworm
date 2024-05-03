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
  <li>LS - list of file in storage (storage directory is defined in config.cfg file)</li>
  <li>STAT file - prints file details</li>
  <li>STATUS - list of bots stored in botnet database</li>
  <li>SEND bot file - send a file to a bot using TCP connection</li>
</ul><br />

<b>TCP</b><br /><br />
Each <i>woodworm</i> is both: a TCP server and a TCP client to all other <i>woodworms</i> TCP servers stored in botnet database. Connection from client to server (C->S) is called TCP session and it consists of two seperate TCP socket connections: one for commands, other for binary data transfer. Connection from server to connected client (S->C) is called a reversed TCP session and allows TCP data handling if other way around is impossible.<br /><br />
Scenario: <i>woodworm A</i> <--> <i>woodworm B</i>
<ul>
  <li>Client A is connected to server B via TCP session AB</li>
  <ul><li>Two separate connection are in this session: control and data link. First to handle commands exchange, second to handle binary data</li><li>Same time server B is connected to client A via reversed TCP session R-AB. Two links are in use as above </li></ul>
  <li>Client B is connected to server A via TCP session BA</li>
  <ul><li>Two separate connection are in this session: control and data link. First to handle commands exchange, second to handle binary data</li><li>Same time server A is connected to client B via reversed TCP session R-BA. Two links are in use as above </li></ul>
  <li>When sending a file from <i>woodworm A</i> to <i>woodworm B</i> a TCP session AB will be in use</li>
  <li>When sending a file from <i>woodworm B</i> to <i>woodworm A</i> a TCP session BA will be in use</li>
</ul>

Scenario: <i>woodworm A</i> --> <i>woodworm B</i>
<ul>
  <li>Client A is connected to server B via TCP session AB</li>
  <ul><li>Two separate connection are in this session: control and data link. First to handle commands exchange, second to handle binary data</li><li>Same time server B is connected to client A via reversed TCP session R-AB. Two links are in use as above </li></ul>
  <li>Client B is NOT connected to server A, there is no TCP session BA</li>
  <li>When sending a file from <i>woodworm A</i> to <i>woodworm B</i> a TCP session AB will be in use</li>
  <li>When sending a file from <i>woodworm B</i> to <i>woodworm A</i> a TCP session R-AB will be in use</li>
</ul>
