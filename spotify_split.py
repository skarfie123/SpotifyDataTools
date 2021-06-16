import argparse
import logging

from constants import ALBUM_TYPE_COMPILATIONS, CLIENT_ID
from spotify_api import SpotifyAPI
import utils

utils.setup_logging()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Splits your playlist by the specified characteristic."
    )
    # parser.add_argument(
    #     "--mode",
    #     default="release-date",
    #     choices=["release-date", "date-added"],
    #     help="output format (default: txt)",
    # )
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

    for t in playlist["tracks"]:
        if (
            args.separateCompilations
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

    for playlist_name in sorted(new_playlists.keys()):
        utils.create_playlist(spotify, me, playlist_name, new_playlists[playlist_name])


if __name__ == "__main__":
    main()
