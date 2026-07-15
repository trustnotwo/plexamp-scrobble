#!/usr/bin/env python3
import os
import sys
import time
import re
import pylast
import subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
action = sys.argv[1]       # "start", "resume", "pause", or "stop"
artist = sys.argv[2]
album = sys.argv[3]
title = sys.argv[4]
duration = int(sys.argv[5])
progress = int(sys.argv[6]) if len(sys.argv) > 6 else 0
# Strip featured artists
artist = re.split(r'\s*(feat\.?|ft\.?|featuring|,|&)\s*', artist, flags=re.IGNORECASE)[0].strip()
print("PLEX: Action={0} | {1} / {2} / {3} / duration={4}s / progress={5}%".format(
    action, artist, album, title, duration, progress))
def read_secret(name):
    with open("/run/secrets/" + name, encoding="utf-8") as f:
        return f.read().strip()
api_key = read_secret("lastfm_api_key")
api_secret = read_secret("lastfm_api_secret")
lastfm_username = read_secret("lastfm_username")
lastfm_password = read_secret("lastfm_password")
network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret,
                               username=lastfm_username, password_hash=pylast.md5(lastfm_password))
if action in ("start", "resume"):
    network.update_now_playing(artist=artist, album=album, title=title, duration=duration)
    print("LAST.FM: Updated now playing: {0} - {1}".format(artist, title))
elif action == "pause":
    # Expire now playing immediately
    network.update_now_playing(artist=artist, album=album, title=title, duration=1)
    print("LAST.FM: Cleared now playing (paused)")
elif action == "stop":
    if progress >= 50:
        timestamp = int(time.time()) - int(duration * progress / 100)
        network.scrobble(artist=artist, album=album, title=title, timestamp=timestamp)
        print("LAST.FM: Scrobbled {0} - {1} at {2}% progress".format(artist, title, progress))
    else:
        print("LAST.FM: Skipped scrobble ({0}% < 50%)".format(progress))
