# pyGadu
Simple implementation of Gadu-Gadu server in python 3.

## Depends
Depends ```colorlog``` for colored console. If you don't need it you can modify ```logger.py```.
```
pip install colorlog
```

## How to run?
```
python pygadu.py REMOTE_ADDR
```
Where ```REMOTE_ADDR``` is yours public IP address.

## How add accounts?
You can create accounts manually by adding it to ```database.db```(SQLite3) in table ```users```.

## What is supported?
Client version: ```Gadu-Gadu Client build 8.0.0.10102```

## Protocol support
### Response
* GG_WELCOME - 100%
* GG_LOGIN80_OK = 100%
* GG_LOGIN_FAILED = 100%
* GG_NOTIFY_REPLY80 = 100%
* GG_STATUS80 = 100%
* GG_RECV_MSG80 = 0% (specified client version is not working with it)
* GG_RECV_MSG = 100%
* GG_PONG = 0%
* GG_DISCONNECTING = 100%

### Request
* GG_LOGIN80 - 100%
* GG_NEW_STATUS80 - 100%
* GG_NOTIFY_FIRST - 100%
* GG_NOTIFY_LAST - 100%
* GG_SEND_MSG80 - 100%
* GG_PING - 100%
* GG_ADD_NOTIFY - 100%
* GG_REMOVE_NOTIFY - 100%

### Actual state
* Client can connect and log in
* Client can change status
* Client can have buddies and check their status and description
* Client can send simple messages to other clients (one to one)
* Messages are queued in database when recipient is offline

### Not working
* Other protocol messages...

## Credits
* ardecht
* libgadu - http://libgadu.net/protocol/