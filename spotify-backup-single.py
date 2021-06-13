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
    parser.add_argument(
        "--format",
        default="txt",
        choices=["json", "txt"],
        help="output format (default: txt)",
    )
    args = parser.parse_args()

    # If they didn't give a filename, then just prompt them. (They probably just double-clicked.)

    # Log into the Spotify API.
    if args.token:
        spotify = SpotifyAPI(args.token)
    else:
        spotify = SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope="user-library-read playlist-read-private playlist-read-collaborative",
        )

    # Get the ID of the logged in user.
    me = spotify.get("me")
    logging.info("Logged in as {display_name} ({id})".format(**me))

    # List all playlists and all track in each playlist.
    playlists = spotify.list(
        "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
    )
    for i, playlist in enumerate(playlists):
        print(i, playlist["name"], sep="\t")
    print(len(playlists), "Likes", sep="\t")
    print(-1, "All", sep="\t")
    while True:
        try:
            chose = int(input("Choose: "))
            assert chose >= -1 and chose <= len(playlists), "not in range"
            break
        except (ValueError, AssertionError):
            print("Please enter a valid integer index")
    if not chose == -1:
        chosens = [chose]
    else:
        chosens = [i for i in range(len(playlists) + 1)]
    for chosen in chosens:
        if chosen == len(playlists):
            # Make a likes playlist
            likes = spotify.list(
                "users/{user_id}/tracks".format(user_id=me["id"]), {"limit": 50}
            )
            chosen_playlist = {"id": "likes", "name": "Likes", "tracks": []}
            for track in likes:
                chosen_playlist["tracks"].append(track)
            logging.info(f"Loading playlist: Likes ({len(likes)} songs)")
        else:
            logging.info(
                "Loading playlist: {name} ({tracks[total]} songs)".format(
                    **playlists[chosen]
                )
            )
            playlists[chosen]["tracks"] = spotify.list(
                playlists[chosen]["tracks"]["href"], {"limit": 100}
            )
            chosen_playlist = playlists[chosen]

        # Write the file.
        filename = (
            "".join([x if x.isalnum() else "_" for x in chosen_playlist["name"]])
            + "."
            + args.format
        )
        with open(filename, "w", encoding="utf-8") as f:
            # JSON file.
            if args.format == "json":
                json.dump(chosen_playlist, f)

            # Tab-separated file.
            elif args.format == "txt":
                f.write(chosen_playlist["name"] + "\n")
                for i, track in enumerate(chosen_playlist["tracks"]):
                    try:
                        f.write(
                            "{index}\t{name}\t{artists}\t{album}\n".format(
                                index=i,
                                name=track["track"]["name"],
                                artists=", ".join(
                                    [
                                        artist["name"]
                                        for artist in track["track"]["artists"]
                                    ]
                                ),
                                album=track["track"]["album"]["name"],
                            )
                        )
                    except:
                        print("Error with track: ", track)
        logging.info("Wrote file: " + filename)


if __name__ == "__main__":
    main()
