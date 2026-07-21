#!/usr/bin/env python3
import os
import re
import sys
import time

import pylast

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

action = sys.argv[1]
artist = sys.argv[2]
album = sys.argv[3]
title = sys.argv[4]
duration = int(sys.argv[5])
progress = int(sys.argv[6]) if len(sys.argv) > 6 else 0

KNOWN_ARTISTS = {
    "tyler, the creator",
    "earth, wind & fire",
    "emerson, lake & palmer",
    "crosby, stills & nash",
    "crosby, stills, nash & young",
    "blood, sweat & tears",
    "hootie & the blowfish",
    "simon & garfunkel",
    "hall & oates",
    "sam & dave",
    "ike & tina turner",
    "kool & the gang",
    "mumford & sons",
    "nick cave & the bad seeds",
    "iron & wine",
    "belle & sebastian",
    "bruce springsteen & the e street band",
    "tom petty & the heartbreakers",
    "bob marley & the wailers",
    "huey lewis & the news",
    "sly & the family stone",
    "prince & the revolution",
    "diana ross & the supremes",
    "smokey robinson & the miracles",
    "gladys knight & the pips",
    "martha & the vandellas",
    "frankie valli & the four seasons",
    "joan jett & the blackhearts",
    "echo & the bunnymen",
    "siouxsie & the banshees",
    "elvis costello & the attractions",
    "kc & the sunshine band",
    "sonny & cher",
    "brooks & dunn",
    "angus & julia stone",
    "above & beyond",
    "chase & status",
    "macklemore & ryan lewis",
    "peter, paul and mary",
    "now, now",
}

_KNOWN_SORTED = sorted(KNOWN_ARTISTS, key=len, reverse=True)

FEAT_MARKER = re.compile(r"\s*(?:feat\.?|ft\.?|featuring)\s+", re.IGNORECASE)
ANY_SEPARATOR = re.compile(r"\s*(?:feat\.?|ft\.?|featuring|,|&)\s*", re.IGNORECASE)


def clean_artist(name):
    stripped = name.strip()
    low = stripped.lower()

    if low in KNOWN_ARTISTS:
        return stripped

    for known in _KNOWN_SORTED:
        if low.startswith(known):
            rest = stripped[len(known):]
            if rest == "" or FEAT_MARKER.match(rest) or rest[:1] in (",", "&"):
                return stripped[:len(known)].strip()

    return ANY_SEPARATOR.split(stripped, maxsplit=1)[0].strip()


artist = clean_artist(artist)

print("PLEX: Action={0} | {1} / {2} / {3} / duration={4}s / progress={5}%".format(
    action, artist, album, title, duration, progress))


def read_secret(name):
    with open("/run/secrets/" + name, encoding="utf-8") as f:
        return f.read().strip()


api_key = read_secret("lastfm_api_key")
api_secret = read_secret("lastfm_api_secret")
lastfm_username = read_secret("lastfm_username")
lastfm_password = read_secret("lastfm_password")

network = pylast.LastFMNetwork(
    api_key=api_key,
    api_secret=api_secret,
    username=lastfm_username,
    password_hash=pylast.md5(lastfm_password),
)

if action in ("start", "resume"):
    network.update_now_playing(artist=artist, album=album, title=title, duration=duration)
    print("LAST.FM: Updated now playing: {0} - {1}".format(artist, title))

elif action == "pause":
    network.update_now_playing(artist=artist, album=album, title=title, duration=1)
    print("LAST.FM: Cleared now playing (paused)")

elif action == "stop":
    elapsed = duration * progress / 100
    if progress >= 50 or elapsed >= 300:
        timestamp = int(time.time()) - int(elapsed)
        network.scrobble(artist=artist, album=album, title=title, timestamp=timestamp)
        print("LAST.FM: Scrobbled {0} - {1} at {2}% progress".format(artist, title, progress))
    else:
        print("LAST.FM: Skipped scrobble ({0}% < 50%)".format(progress))
