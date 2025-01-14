import ffmpeg
import sys
import threading
import time
import subprocess
import signal
import re

active_duration = 0.0

def get_embedded_tags(filename):
    try:
        probe = ffmpeg.probe(filename)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        raise
    return probe["streams"][0]["tags"], float(probe["streams"][0]["duration"])


def parse_lyrics(lyrics_text):
    pattern = r"\[(\d{2}:\d{2}\.\d{3})\](.*?)(?=\[\d{2}:\d{2}\.\d{3}\]|$)"
    matches = re.findall(pattern, lyrics_text, re.DOTALL)
    lyrics = []

    for timestamp, text in matches:
        minutes, seconds = map(float, timestamp.split(":"))
        lyrics.append((minutes * 60 + seconds, text.strip()))

    return lyrics

def play_audio(filename):
    return subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def display_lyrics(lyrics, duration):
    global active_duration
    for timestamp, lyric in lyrics:
        while active_duration < timestamp:
            time.sleep(0.1)
        try:
            write_lyrics(
                lyric, lyrics[lyrics.index((timestamp, lyric)) + 1][0] - timestamp
            )
        except IndexError:
            write_lyrics(lyric, duration - timestamp)


def write_lyrics(content, in_time):
    if not content or in_time <= 0:
        return

    delay = in_time / len(content)

    for char in content:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)

    print()


def update_active_duration():
    global active_duration
    while active_duration < duration:
        time.sleep(1)
        active_duration += 1


def handle_exit(signum, frame):
    print("\n\nExiting...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_exit)

if __name__ == "__main__":
    FILENAME = "song.ogg"
    tags, duration = get_embedded_tags(FILENAME)

    lyrics_text = tags.get("LYRICS", "")
    lyrics = parse_lyrics(lyrics_text)
    print("Lyrics loaded successfully!\n\n")

    audio_process = play_audio(FILENAME)

    threading.Thread(target=update_active_duration, daemon=True).start()
    threading.Thread(
        target=display_lyrics, args=(lyrics, duration), daemon=True
    ).start()

    audio_process.wait()
    print("Playback completed!")
