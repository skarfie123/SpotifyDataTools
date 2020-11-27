spotify-backup
==============

![GitHub top language](https://img.shields.io/github/languages/top/skarfie123/spotify-backup?style=plastic)

A Python 3 script that exports all of your Spotify playlists, useful for paranoid Spotify users like me, afraid that one day Spotify will go under and take all of our playlists with it!

Run the scripts from the command line:

    python spotify-backup.py

It'll ask you for a filename and then pop open a web page so you can authorize access to the Spotify API.

Adding `--format=json` will give you a JSON dump with everything that the script gets from the Spotify API. If for some reason the browser-based authorization flow doesn't work, you can also [generate an OAuth token](https://developer.spotify.com/web-api/console/get-playlists/) on the developer site (with the `playlist-read-private` permission) and pass it with the `--token` option.

Collaborative playlists and playlist folders don't show up in the API, sadly.

## Scripts:

- `spotify-backup.py` for backing up all playlists into a filename
- `spotify-backup-single.py` for backing up playlists to individual files
- `spotify-check-duplicates.py` to list all duplicate songs in a playlist (by comparing the first few characters)
