#!/usr/bin/env python3

import argparse
import json
import logging
import os
from io import TextIOWrapper
from ssl import wrap_socket

import click
import coloredlogs

from spotify_api import SpotifyAPI

coloredlogs.install(datefmt="%I:%M:%S", fmt="[%(asctime)s] %(levelname)s %(message)s")

LIKES_PLAYLIST = "Likes"


def load_playlist(spotify: SpotifyAPI, me, playlist):
    if playlist["name"] == LIKES_PLAYLIST:
        # List all liked tracks
        playlist["tracks"] = spotify.list(
            "users/{user_id}/tracks".format(user_id=me["id"]), {"limit": 50}
        )
        logging.info(f"Loaded {playlist['name']} ({len(playlist['tracks'])} songs)")
    else:
        # List all tracks in playlist
        logging.info(
            f"Loading playlist: {playlist['name']} ({playlist['tracks']['total']} songs)"
        )
        playlist["tracks"] = spotify.list(playlist["tracks"]["href"], {"limit": 100})


def write_playlist(f: TextIOWrapper, playlist):
    """Write playlist to a file"""
    f.write(playlist["name"] + "\n")
    for i, track in enumerate(playlist["tracks"]):
        if track["track"] is None:
            logging.error(f'{track}["track"] is None')
            continue
        write_track(f, track, i + 1)


def write_duplicates(f: TextIOWrapper, playlist):
    """Write duplicates to a file"""
    f.write(playlist["name"] + " duplicates\n")
    for i, track1 in enumerate(playlist["tracks"]):
        if track1["track"] is None:
            continue
        for j, track2 in enumerate(playlist["tracks"]):
            if track2["track"] is None:
                continue
            if (
                i < j
                and track1["track"]["name"][:5] == track2["track"]["name"][:5]
                and track1["track"]["artists"] == track2["track"]["artists"]
            ):
                write_track(f, track1, i + 1)
                write_track(f, track2, j + 1)


def write_track(f: TextIOWrapper, track, index):
    """Write a track as TabSeperatedValues to a file"""
    f.write(
        "{index}\t{name}\t{artists}\t{album}\t{uri}\n".format(
            index=index,
            uri=track["track"]["uri"],
            name=track["track"]["name"],
            artists=", ".join([artist["name"] for artist in track["track"]["artists"]]),
            album=track["track"]["album"]["name"],
        )
    )


def playlist_filename(playlist):
    return "".join([x if x.isalnum() else "_" for x in playlist["name"]])


def confirm_overwrite(filename: str, yes: bool = False):
    return (
        yes
        or not os.path.exists(filename)
        or click.confirm(f"{filename} already exists, do you want to overwrite?")
    )


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
        default="likes,playlists",
        choices=["likes,playlists", "playlists,likes", "playlists", "likes"],
        help="dump playlists or likes, or both (default: playlists)",
    )
    parser.add_argument(
        "--folder",
        default="backup",
        help="folder to save each file, normal mode only (default: backup)",
    )
    parser.add_argument(
        "--format",
        default="txt",
        choices=["json", "txt"],
        help="output format (default: txt)",
    )
    parser.add_argument(
        "--single",
        dest="single",
        action="store_true",
        help="dump all chosen playlists into single file (default: False)",
    )
    parser.add_argument(
        "--mine",
        dest="mine",
        action="store_true",
        help="save only playlists owned by you (default: False)",
    )
    parser.add_argument(
        "--cd",
        "--check-duplicates",
        dest="checkDuplicates",
        action="store_true",
        help="check for duplicates, normal mode only (default: False)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        action="store_true",
        help="say yes to all overwrite confirmations (default: False)",
    )
    parser.set_defaults(single=False, mine=False, checkDuplicates=False, yes=False)
    parser.add_argument("file", help="output filename for single file mode", nargs="?")
    args = parser.parse_args()

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

    # Add Likes playlist
    if "likes" in args.dump:
        playlists += [{"id": "likes", "name": LIKES_PLAYLIST, "tracks": []}]

    # List all playlists and the tracks in each playlist
    if "playlists" in args.dump:
        logging.info("Loading playlists...")
        playlist_data = spotify.list(
            "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
        )
        logging.info(f"Found {len(playlist_data)} playlists")

        if args.mine:
            playlist_data = [p for p in playlist_data if p["owner"]["id"] == me["id"]]

        playlists += playlist_data

    if not args.single:
        # list choices
        for i, playlist in enumerate(playlists):
            print(i, playlist["name"], sep="\t")
        print(-1, "All", sep="\t")

        # prompt for choice
        while True:
            try:
                choice = int(input("Choose: "))
                assert choice >= -1 and choice < len(playlists), "not in range"
                break
            except (ValueError, AssertionError):
                print("Please enter a valid integer index")

        if choice != -1:
            playlists = [playlists[choice]]

    if args.single:
        if args.file and not confirm_overwrite(args.file, args.yes):
            args.file = None

        # If they didn't give a filename, then just prompt them.
        while not args.file:
            args.file = input("Enter a file name (e.g. playlists.txt): ")
            args.format = args.file.split(".")[-1]

            if args.file and not confirm_overwrite(args.file, args.yes):
                args.file = None

        for playlist in playlists:
            load_playlist(spotify, me, playlist)

        with open(args.file, "w", encoding="utf-8") as f:
            logging.info("Writing file: " + f.name)

            if args.format == "json":
                json.dump(playlists, f)
            elif args.format == "txt":
                for playlist in playlists:
                    logging.info("Writing " + playlist["name"])
                    write_playlist(f, playlist)

                    f.write("\n")
    else:
        os.makedirs(args.folder, exist_ok=True)

        for playlist in playlists:
            filename = os.path.join(
                args.folder, playlist_filename(playlist) + "." + args.format
            )

            if not confirm_overwrite(filename, args.yes):
                continue

            load_playlist(spotify, me, playlist)

            with open(filename, "w", encoding="utf-8") as f:
                logging.info("Writing file: " + f.name)

                if args.format == "json":
                    json.dump(playlist, f)
                elif args.format == "txt":
                    write_playlist(f, playlist)

            if args.checkDuplicates:
                duplicates_filename = os.path.join(
                    args.folder, playlist_filename(playlist) + "_duplicates.txt"
                )

                if not confirm_overwrite(duplicates_filename, args.yes):
                    continue

                with open(duplicates_filename, "w", encoding="utf-8") as f:
                    logging.info("Writing file: " + f.name)

                    write_duplicates(f, playlist)


if __name__ == "__main__":
    main()
