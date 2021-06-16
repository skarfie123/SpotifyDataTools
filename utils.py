import coloredlogs
from datetime import datetime
import logging

from constants import LIKES_PLAYLIST
from spotify_api import SpotifyAPI


def setup_logging():
    coloredlogs.install(
        datefmt="%I:%M:%S", fmt="[%(asctime)s] %(levelname)s %(message)s"
    )


def parse_choices(choices):
    choice_ranges = (x.split("-") for x in choices.split(","))
    choice_list = [i for r in choice_ranges for i in range(int(r[0]), int(r[-1]) + 1)]
    return choice_list


def get_playlists(
    spotify: SpotifyAPI, me, dump: str = "likes,playlists", mine: bool = False
) -> list:
    playlists = []

    # Add Likes playlist
    if "likes" in dump:
        playlists += [{"id": "likes", "name": LIKES_PLAYLIST, "tracks": []}]

    # List all playlists and the tracks in each playlist
    if "playlists" in dump:
        logging.info("Loading playlists...")
        playlist_data = spotify.list(
            "users/{user_id}/playlists".format(user_id=me["id"]), {"limit": 50}
        )
        logging.info(f"Found {len(playlist_data)} playlists")

        if mine:
            playlist_data = [p for p in playlist_data if p["owner"]["id"] == me["id"]]

        playlists += playlist_data

    return playlists


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


def list_playlists(playlists, all=True):
    # list available choices
    for i, playlist in enumerate(playlists):
        print(i, playlist["name"], sep="\t")
    if all:
        print(-1, "All", sep="\t")


def choose_playlist(playlists):
    list_playlists(playlists, all=False)

    # prompt for choices
    while True:
        try:
            choice = int(input("Choose: "))
            assert choice >= 0 and choice < len(playlists), "not in range"
            break
        except (ValueError, AssertionError):
            print("Please enter a valid integer index")

    return playlists[choice]


def choose_playlists(playlists):
    list_playlists(playlists)

    # prompt for choices
    while True:
        try:
            choices = parse_choices(input("Choose: "))
            assert all(
                choice >= -1 and choice < len(playlists) for choice in choices
            ), "not in range"
            break
        except (ValueError, AssertionError):
            print("Please enter a valid integer indices")

    if -1 not in choices:
        playlists = [playlists[choice] for choice in choices]

    return playlists


def create_playlist(spotify: SpotifyAPI, me, name: str, tracks: list = []):
    new_playlist = spotify.post(
        "users/{id}/playlists".format(**me),
        data={
            "name": name,
            "public": False,
            "description": f"Created by SpotifyDataTools at {datetime.today()}",
        },
    )
    logging.info(f"Created playlist: {name}")

    if tracks:
        add_tracks(spotify, new_playlist, tracks)
        logging.info(f"Added total {len(tracks)} tracks to playlist: {name}")

    return new_playlist


def add_tracks(spotify: SpotifyAPI, playlist, tracks: list):
    uris = [t["track"]["uri"] for t in tracks]
    i = 0
    step = 100
    while i < len(uris):
        spotify.post(
            "playlists/{id}/tracks".format(**playlist),
            data={"uris": uris[i : i + step]},
        )
        if len(tracks) > step:
            logging.debug(
                f"Added {len(uris[i : i + step])} tracks to playlist: {playlist['name']}"
            )
        i += step


def release_to_year(release):
    return int(release.split("-")[0])


def year_to_decade(year):
    return year // 10 * 10


def year_to_decade_str(year):
    return f"{year_to_decade(year):02d}s"
