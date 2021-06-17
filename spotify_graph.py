#!/usr/bin/env python3

import argparse
import logging
from datetime import datetime
from spotify_backup import confirm_overwrite

import matplotlib.pyplot as plt

import utils
from constants import CLIENT_ID
from spotify_api import SpotifyAPI

utils.setup_logging()

GRAPH_COMPILATIONS_INCLUDE = "include"
GRAPH_COMPILATIONS_EXCLUDE = "exclude"
GRAPH_COMPILATIONS_BOTH = "both"


def parse_args():
    parser = argparse.ArgumentParser(description="Exports your Spotify playlists.")
    parser.add_argument(
        "--include",
        default="likes,playlists",
        choices=["likes,playlists", "playlists,likes", "playlists", "likes"],
        help="include playlists or likes, or both (default: playlists)",
    )
    parser.add_argument(
        "-c",
        "--compilations",
        default=GRAPH_COMPILATIONS_BOTH,
        choices=[
            GRAPH_COMPILATIONS_INCLUDE,
            GRAPH_COMPILATIONS_EXCLUDE,
            GRAPH_COMPILATIONS_BOTH,
        ],
        help=f"whether to include songs from compilations from the graphs, because compilations have misleading release-dates (default: {GRAPH_COMPILATIONS_BOTH})",
    )
    parser.add_argument(
        "--mine",
        dest="mine",
        action="store_true",
        help="show only playlists owned by you (default: False)",
    )
    parser.add_argument(
        "--save",
        dest="save",
        action="store_true",
        help="save the plots as images (default: False)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        action="store_true",
        help="say yes to all overwrite confirmations (default: False)",
    )
    parser.set_defaults(mine=False, save=False, yes=False)
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

    if len(playlists) == 1:
        playlist = playlists[0]
        utils.load_playlist(spotify, me, playlist)
    else:
        name = input("What's the name for this set of playlists? ")
        for p in playlists:
            utils.load_playlist(spotify, me, p)
        playlist = {
            "name": name,
            "tracks": [t for p in playlists for t in p["tracks"]],
        }

    for plot in [plot_release_date, plot_date_added, plot_release_vs_added]:
        plt.figure()
        if args.compilations in [GRAPH_COMPILATIONS_BOTH, GRAPH_COMPILATIONS_INCLUDE]:
            plot(playlist, excludeCompilations=False)
        if args.compilations in [GRAPH_COMPILATIONS_BOTH, GRAPH_COMPILATIONS_EXCLUDE]:
            plot(playlist, excludeCompilations=True)

        filename = f"{playlist['name'].replace(' ', '_')}_{plot.__name__}.png"
        if args.save and confirm_overwrite(filename, args.yes):
            plt.savefig(filename)
            logging.info(f"Saved {filename}")

    if not args.save:
        plt.show()


def plot_release_date(playlist, excludeCompilations: bool):
    tracks = exclude_compilations(playlist["tracks"], excludeCompilations)

    years = {}
    decades = {}
    for t in tracks:

        if t["track"]["album"]["release_date"] is None:
            continue

        year = (
            utils.release_to_year(t["track"]["album"]["release_date"]) + 0.5
        )  # add 0.5 to make the bars aligned
        if year in years:
            years[year] += 1
        else:
            years[year] = 1

        decade = utils.year_to_decade(year) + 5  # add 5 to make the bars aligned
        if decade in decades:
            decades[decade] += 1
        else:
            decades[decade] = 1

    plt.bar(
        sorted(decades.keys()),
        [decades[d] for d in sorted(decades.keys())],
        width=10,
        label=f"Per Decade ({'Exc.' if excludeCompilations else 'Inc.'} Compilations)",
        zorder=1,
    )
    plt.bar(
        sorted(years.keys()),
        [years[y] for y in sorted(years.keys())],
        label=f"Per Year ({'Exc.' if excludeCompilations else 'Inc.'} Compilations)",
        zorder=2,
    )

    plt.title(playlist["name"])
    plt.xlabel("Release Date")
    plt.ylabel("Count")
    plt.legend()


def plot_date_added(playlist, excludeCompilations: bool):
    tracks = exclude_compilations(playlist["tracks"], excludeCompilations)

    years = {}
    for t in tracks:

        year = (
            datetime.fromisoformat(t["added_at"].removesuffix("Z")).year + 0.5
        )  # add 0.5 to make the bars aligned
        if year in years:
            years[year] += 1
        else:
            years[year] = 1

    plt.bar(
        sorted(years.keys()),
        [years[d] for d in sorted(years.keys())],
        width=1,
        label=f"{'Exc.' if excludeCompilations else 'Inc.'} Compilations",
    )

    plt.title(playlist["name"])
    plt.xlabel("Date Added")
    plt.ylabel("Count")
    plt.legend()


def plot_release_vs_added(playlist, excludeCompilations: bool):
    tracks = exclude_compilations(playlist["tracks"], excludeCompilations)

    plt.scatter(
        [
            datetime.fromisoformat(t["added_at"].removesuffix("Z"))
            for t in tracks
            if t["track"]["album"]["release_date"] is not None
        ],
        [
            utils.release_to_year(t["track"]["album"]["release_date"])
            for t in tracks
            if t["track"]["album"]["release_date"] is not None
        ],
        marker=("." if excludeCompilations else "o"),
        label=f"{'Exc.' if excludeCompilations else 'Inc.'} Compilations",
    )

    plt.title(playlist["name"])
    plt.xlabel("Date Added")
    plt.ylabel("Release Date")


def exclude_compilations(tracks: list, excludeCompilations: bool):
    return [
        t
        for t in tracks
        if (
            not excludeCompilations
            or t["track"]["album"]["album_type"]
            not in [
                "compilation",
                None,
            ]
        )
    ]


if __name__ == "__main__":
    main()
