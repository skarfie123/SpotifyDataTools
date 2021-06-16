# Spotify Data Tools

![GitHub top language](https://img.shields.io/github/languages/top/skarfie123/SpotifyDataTools)
![GitHub issues](https://img.shields.io/github/issues/skarfie123/SpotifyDataTools)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

A Python script that exports all of your Spotify playlists, useful for paranoid Spotify users like me, afraid that one day Spotify will go under and take all of our playlists with it!

It'll ask you for a filename and then pop open a web page so you can authorize access to the Spotify API. Then the script will load your playlists and save tab-separated files with your playlists that you can open in Excel. You can even copy-paste the rows from Excel into a Spotify playlist.

If for some reason the browser-based authorization flow doesn't work, you can also [generate an OAuth token](https://developer.spotify.com/web-api/console/get-playlists/) on the developer site (with the relevant permissions) and pass it with the `--token` option.

Playlist folders don't show up in the API, sadly.

## Permissions

- `user-library-read`
- `playlist-read-private`
- `playlist-read-collaborative`
- `playlist-modify-private`

## Backup

You can run the script from the command line:

`python spotify_backup.py`

or, to get a JSON dump, use:

`python spotify_backup.py --format=json`

By default, it includes your playlists and Likes. To include only your playlists, you can use:

`python spotify_backup.py --dump=playlists`

By default, it creates a file for each playlist, but you can dump to a single file:

`python spotify_backup.py playlists.txt --single`

By default, it includes all playlists you have followed, but you can choose only those that are owned by you:

`python spotify_backup.py --mine`

You can check for duplicates in your playlists:

`python spotify_backup.py --check-duplicates`

## Split

Split a playlist by decade:

`python spotify_backup.py`

Separate compilations (because their release dates are misleading):

`python spotify_backup.py --separate-compilations`

Split by year added:

`python spotify_backup.py --mode date-added`
