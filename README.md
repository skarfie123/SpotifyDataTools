# spotify-backup

![GitHub top language](https://img.shields.io/github/languages/top/skarfie123/spotify-backup)
![GitHub issues](https://img.shields.io/github/issues/skarfie123/spotify-backup)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

A Python script that exports all of your Spotify playlists, useful for paranoid Spotify users like me, afraid that one day Spotify will go under and take all of our playlists with it!

To run the script, [save it from here](https://raw.githubusercontent.com/skarfie123/spotify-backup/master/spotify-backup.py) and double-click it. It'll ask you for a filename and then pop open a web page so you can authorize access to the Spotify API. Then the script will load your playlists and save a tab-separated file with your playlists that you can open in Excel. You can even copy-paste the rows from Excel into a Spotify playlist.

You can run the script from the command line:

    python spotify-backup.py

It'll ask you for a filename and then pop open a web page so you can authorize access to the Spotify API.

or, to get a JSON dump, use:

    python spotify-backup.py playlists.json --format=json

By default, it includes your playlists. To include your Liked Songs, you can use:

    python spotify-backup.py playlists.txt --dump=liked,playlists

If for some reason the browser-based authorization flow doesn't work, you can also [generate an OAuth token](https://developer.spotify.com/web-api/console/get-playlists/) on the developer site (with the relevant permissions) and pass it with the `--token` option.

## Permissions

- `user-library-read`
- `playlist-read-private`
- `playlist-read-collaborative`

Playlist folders don't show up in the API, sadly.

## Scripts

- `spotify-backup.py` for backing up all playlists into a filename
- `spotify-backup-single.py` for backing up playlists to individual files
- `spotify-check-duplicates.py` to list all duplicate songs in a playlist (by comparing the first few characters)
