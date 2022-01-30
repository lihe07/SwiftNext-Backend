import socketio

client = socketio.Client()

client.on("connect", lambda: print("Connected"))

if __name__ == '__main__':
    client.connect("wss://api.imlihe.com")