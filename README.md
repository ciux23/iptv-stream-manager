# IPTV Stream Manager

IPTV Stream Manager is a lightweight IPTV proxy and playlist manager based on Python and aiohttp.

It generates a personal IPTV playlist compatible with M3U players such as SS IPTV, IPTV Smarters, Kodi and other compatible clients.

The project provides a ready-to-use configuration with selected channels, metadata, logos and HLS stream proxy support.

## Features

- Automatic M3U playlist generation
- Rai channels support
- Mediaset channels support
- Dynamic stream support
- HLS proxy and manifest rewriting
- Channel metadata support:
  - channel name
  - tvg-id
  - logo
  - group information
- Docker Compose deployment


## Requirements

Before starting, make sure your system has:

- Docker installed
- Docker Compose installed

The project can run on:

- Raspberry Pi
- NAS systems
- Linux servers
- Any machine supporting Docker containers


## Installation

Clone the repository:

```bash
git clone https://github.com/ciux23/iptv-stream-manager.git
```

Enter the project directory:

```bash
cd iptv-stream-manager
```

Start the container:

```bash
docker compose up -d
```


## Usage

After starting the container, the IPTV playlist is available at:

```text
http://YOUR_SERVER_IP:8090/playlist.m3u
```

Replace `YOUR_SERVER_IP` with the IP address of the machine running the container.

Example:

```text
http://192.168.0.100:8090/playlist.m3u
```

Add this URL to your IPTV player.


## Health Check

To verify that the service is running correctly:

```text
http://YOUR_SERVER_IP:8090/health
```

A working installation will return:

```text
OK
```


## Configuration

The main configuration file is:

```text
config.yaml
```

It contains:

- allowed network domains
- channel configuration
- stream sources
- service parameters


The file:

```text
channels_selected.yaml
```

contains channel metadata used to generate the IPTV playlist:

- channel name
- tvg-id
- logo
- group information


## Project Structure

```text
iptv-stream-manager/

├── app.py
├── compose.yaml
├── config.yaml
├── channels_selected.yaml
├── LICENSE
└── README.md
```
## Compatible IPTV Players

The generated M3U playlist can be used with IPTV clients supporting standard M3U playlists, including:

- SS IPTV
- IPTV Smarters
- Kodi
- Other compatible IPTV applications


## Disclaimer

This project is provided for personal and educational purposes.

The software only manages and proxies IPTV streams provided by external sources.

The user is responsible for ensuring that all streams and content accessed through this software are used in compliance with applicable laws and the terms of service of the original providers.

The authors are not responsible for the availability, legality or content of third-party streams.
