import socket
s = socket.socket()
s.settimeout(2)
r = s.connect_ex(("127.0.0.1", 1883))
print("MQTT broker 1883:", "open" if r == 0 else "closed (err=%d)" % r)
s.close()
