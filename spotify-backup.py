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
        "--dump",
        default="playlists",
        choices=["likes,playlists", "playlists,likes", "playlists", "likes"],
        help="dump playlists or likes, or both (default: playlists)",
    )
    parser.add_argument(
        "--format",
        default="txt",
        choices=["json", "txt"],
        help="output format (default: txt)",
    )
    parser.add_argument("file", help="output filename", nargs="?")
    args = parser.parse_args()

    # If they didn't give a filename, then just prompt them. (They probably just double-clicked.)
    while not args.file:
        args.file = input("Enter a file name (e.g. playlists.txt): ")
        args.format = args.file.split(".")[-1]

    # Log into the Spotify API.
    if args.token:
        spotify = SpotifyAPI(args.token)
    else:
        spotify = SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope="user-library-read playlist-read-private playlist-read-collaborative",
        )

    # Get the ID of the logged in user.
    logging.info("Loading user info...")
    me = spotify.get("me")
    logging.info("Logged in as {display_name} ({id})".format(**me))

    playlists = []

    # List likes songs
    if "likes" in args.dump:
        logging.info("Loading likes songs...")
        likes = spotify.list(
            "users/{user_id}/tracks".format(user_id=me["id"]), {"limit": 50}
        )
        playlists += [{"id": "likes", "name": "Likes", "tracks": likes}]
        logging.info(f"Loading playlist: Likes ({len(likes)} songs)")

    # List all playlists and the tracks in each playlist
    if "playlists" in args.dump:
        logging.info("Loading playlists...")
        playlist_data = spotify.list(
            "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
        )
        logging.info(f"Found {len(playlist_data)} playlists")

        # List all tracks in each playlist
        for playlist in playlist_data:
            logging.info(
                "Loading playlist: {name} ({tracks[total]} songs)".format(**playlist)
            )
            playlist["tracks"] = spotify.list(
                playlist["tracks"]["href"], {"limit": 100}
            )
        playlists += playlist_data

    # Write the file.
    logging.info("Writing files...")
    with open(args.file, "w", encoding="utf-8") as f:
        # JSON file.
        if args.format == "json":
            json.dump(playlists, f)

        # Tab-separated file.
        elif args.format == "txt":
            for playlist in playlists:
                f.write(playlist["name"] + "\n")
                logging.info("Saving " + playlist["name"])
                for track in playlist["tracks"]:
                    if track["track"] is None:
                        logging.error(f'{track}["track"] is None')
                        continue
                    f.write(
                        "{name}\t{artists}\t{album}\t{uri}\n".format(
                            uri=track["track"]["uri"],
                            name=track["track"]["name"],
                            artists=", ".join(
                                [artist["name"] for artist in track["track"]["artists"]]
                            ),
                            album=track["track"]["album"]["name"],
                        )
                    )
                f.write("\n")
    logging.info("Wrote file: " + args.file)


if __name__ == "__main__":
    main()
