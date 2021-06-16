import argparse
from datetime import datetime
import logging

from constants import ALBUM_TYPE_COMPILATIONS, CLIENT_ID
from spotify_api import SpotifyAPI
import utils

utils.setup_logging()

SPLIT_MODE_DATE_ADDED = "date-added"
SPLIT_MODE_RELEASE_DATE = "release-date"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Splits your playlist by the specified characteristic."
    )
    parser.add_argument(
        "--mode",
        default=SPLIT_MODE_RELEASE_DATE,
        choices=[SPLIT_MODE_RELEASE_DATE, SPLIT_MODE_DATE_ADDED],
        help=f"output format (default: {SPLIT_MODE_RELEASE_DATE})",
    )
    parser.add_argument(
        "--sc",
        "--separate-compilations",
        dest="separateCompilations",
        action="store_true",
        help="split compilations into separate playlist, because compilations have misleading release-dates (default: False)",
    )
    parser.set_defaults(separateCompilations=False)
    return parser.parse_args()


def new_playlist_name(playlists, suffix: str):
    return f"{playlists['name']}.{suffix}"


def main():
    args = parse_args()
    print(args)

    # Log into the Spotify API.
    spotify = SpotifyAPI.authorize(
        client_id=CLIENT_ID,
        scope="user-library-read playlist-read-private playlist-read-collaborative playlist-modify-private",
    )

    # Get the ID of the logged in user.
    logging.info("Loading user info...")
    me = spotify.get("me")
    logging.info("Logged in as {display_name} ({id})".format(**me))

    playlists = utils.get_playlists(spotify, me)

    playlist = utils.choose_playlist(playlists)

    utils.load_playlist(spotify, me, playlist)

    new_playlists = {}

    if args.mode == SPLIT_MODE_RELEASE_DATE:
        split_release_date(
            spotify, me, playlist, new_playlists, args.separateCompilations
        )
    elif args.mode == SPLIT_MODE_DATE_ADDED:
        split_date_added(spotify, me, playlist, new_playlists)

    for playlist_name in sorted(new_playlists.keys()):
        utils.create_playlist(spotify, me, playlist_name, new_playlists[playlist_name])


def split_release_date(
    spotify: SpotifyAPI, me, playlist, new_playlists: dict, separateCompilations: bool
):

    for t in playlist["tracks"]:
        if (
            separateCompilations
            and t["track"]["album"]["album_type"] == ALBUM_TYPE_COMPILATIONS
        ):
            name = new_playlist_name(playlist, ALBUM_TYPE_COMPILATIONS)
            if name in new_playlists:
                new_playlists[name].append(t)
            else:
                new_playlists[name] = [t]
            continue

        year = utils.release_to_year(t["track"]["album"]["release_date"])
        decade = utils.year_to_decade_str(year)

        name = new_playlist_name(playlist, decade)
        if name in new_playlists:
            new_playlists[name].append(t)
        else:
            new_playlists[name] = [t]


def split_date_added(spotify: SpotifyAPI, me, playlist, new_playlists: dict):

    for t in playlist["tracks"]:
        time = t["added_at"]
        year = datetime.fromisoformat(time.removesuffix("Z")).year
        name = f"added{year}"
        name = new_playlist_name(playlist, name)
        if name in new_playlists:
            new_playlists[name].append(t)
        else:
            new_playlists[name] = [t]


if __name__ == "__main__":
    main()
