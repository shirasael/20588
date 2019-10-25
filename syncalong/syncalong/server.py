import time
from server.music_server import MusicServer

if __name__ == "__main__":
    music_file = r"D:\itai\pyhton\a.mp3"
    ms = MusicServer("0.0.0.0", 22222)
    ms.start()
    while True:
        try:
            while len(ms.clients) <= 1:
                continue
            ms.serve_music_file(music_file)
            ms.signal_play_all(music_file)
            time.sleep(10)
            ms.signal_stop_all()
            ms.clients = []
        except:
            print('Some Error has accured')