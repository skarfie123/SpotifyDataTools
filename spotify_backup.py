#!/usr/bin/env python3

import argparse
import json
import logging
import os
from io import TextIOWrapper

import click

import utils
from constants import CLIENT_ID
from spotify_api import SpotifyAPI

utils.setup_logging()


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


def parse_args():
    parser = argparse.ArgumentParser(description="Exports your Spotify playlists.")
    parser.add_argument(
        "--include",
        default="likes,playlists",
        choices=["likes,playlists", "playlists,likes", "playlists", "likes"],
        help="include playlists or likes, or both (default: playlists)",
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
    return parser.parse_args()


def main():
    args = parse_args()

    # Log into the Spotify API.
    spotify = SpotifyAPI.authorize(
        client_id=CLIENT_ID,
        scope="user-library-read playlist-read-private playlist-read-collaborative",
    )

    me = utils.login(spotify)

    playlists = utils.get_playlists(spotify, me, args.include, args.mine)

    playlists = utils.choose_playlists(playlists)

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
            utils.load_playlist(spotify, me, playlist)

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

            utils.load_playlist(spotify, me, playlist)

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
