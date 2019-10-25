import time
from server.music_server import MusicServer

if __name__ == "__main__":
    music_file = r'D:\itai\pyhton\Always Dreaming - Same Town Forever.mp3'
    ms = MusicServer("0.0.0.0", 22222)
    ms.start()
    while True:
        while len(ms.clients) == 0:
            continue
        ms.serve_music_file(music_file)
        ms.signal_play_all(music_file)
        time.sleep(10)
        ms.signal_stop_all()
        ms.clients = []