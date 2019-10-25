from client.client import Client

if __name__ == "__main__":
    c = Client("10.0.0.5", 22222, '10.0.0.5', r'C:\temp\syncalong')
    c.start()
