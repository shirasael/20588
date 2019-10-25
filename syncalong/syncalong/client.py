from client.client import Client

if __name__ == "__main__":
    c = Client("localhost", 22222, '127.0.0.1', r'C:\temp\syncalong')
    c.start()
