import sys

from syncalong.main import client_main, server_main

def main():
    arg = sys.argv[1]
    if arg == "client":
        client_main.main()
    elif arg == "server":
        server_main.main()
    else:
        print("Please select 'client' or 'server'.")


if __name__ == "__main__":
    main()