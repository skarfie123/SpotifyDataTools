#!/usr/bin/env python3

import argparse
import json
import logging
from spotify_api import SpotifyAPI

logging.basicConfig(level=20, datefmt="%I:%M:%S", format="[%(asctime)s] %(message)s")


def main():
    # Parse arguments.
    parser = argparse.ArgumentParser(
        description="Exports your Spotify playlists. By default, opens a browser window "
        + "to authorize the Spotify Web API, but you can also manually specify"
        + " an OAuth token with the --token option."
    )
    parser.add_argument(
        "--token",
        metavar="OAUTH_TOKEN",
        help="use a Spotify OAuth token (requires the "
        + "`playlist-read-private` permission)",
    )
    args = parser.parse_args()

    # If they didn't give a filename, then just prompt them. (They probably just double-clicked.)

    # Log into the Spotify API.
    if args.token:
        spotify = SpotifyAPI(args.token)
    else:
        spotify = SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934", scope="playlist-read-private"
        )

    # Get the ID of the logged in user.
    me = spotify.get("me")
    log("Logged in as {display_name} ({id})".format(**me))

    # List all playlists and all track in each playlist.
    playlists = spotify.list(
        "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
    )
    for i, playlist in enumerate(playlists):
        print(i, playlist["name"], sep="\t")
    while True:
        try:
            chosen = int(input("Choose: "))
            assert chosen >= 0 and chosen < len(playlists), "not in range"
            break
        except (ValueError, AssertionError):
            print("Please enter a valid integer index")
    print(playlists[chosen]["name"])
    log("Loading playlist: {name} ({tracks[total]} songs)".format(**playlists[chosen]))
    playlists[chosen]["tracks"] = spotify.list(
        playlists[chosen]["tracks"]["href"], {"limit": 100}
    )

    # Write the file.
    with open(
        playlists[chosen]["name"] + "_duplicates.txt", "w", encoding="utf-8"
    ) as f:
        # Tab-separated file.
        f.write(playlists[chosen]["name"] + " duplicates\n")
        print("[", end="")
        for i, track1 in enumerate(playlists[chosen]["tracks"]):
            if i % int(len(playlists[chosen]["tracks"]) / 10) == 0:
                print("=", end="")
            # print(i%(len(playlists[chosen]['tracks'])/10), i, end="")
            for j, track2 in enumerate(playlists[chosen]["tracks"]):
                try:
                    if (
                        i < j
                        and track1["track"]["name"][:5] == track2["track"]["name"][:5]
                        and track1["track"]["artists"] == track2["track"]["artists"]
                    ):
                        f.write(
                            "{index}\t{name}\t{artists}\t{album}\n".format(
                                index=i,
                                name=track1["track"]["name"],
                                artists=", ".join(
                                    [
                                        artist["name"]
                                        for artist in track1["track"]["artists"]
                                    ]
                                ),
                                album=track1["track"]["album"]["name"],
                            )
                        )
                        f.write(
                            "{index}\t{name}\t{artists}\t{album}\n\n".format(
                                index=j,
                                name=track2["track"]["name"],
                                artists=", ".join(
                                    [
                                        artist["name"]
                                        for artist in track2["track"]["artists"]
                                    ]
                                ),
                                album=track2["track"]["album"]["name"],
                            )
                        )
                except:
                    if not track1["track"]:
                        print("Error with track1: ", i)
                        break
                    else:
                        print("Error with track2: ", j)
        print("]")
    log("Wrote file: " + playlists[chosen]["name"] + "_duplicates.txt")


if __name__ == "__main__":
    main()
