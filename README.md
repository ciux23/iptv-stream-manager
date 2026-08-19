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
- Health monitoring endpoint
- Telegram notifications on service failures

## Quick Start

The prebuilt image is published on GitHub Container Registry, so no local build is required.

1. Install Docker and Docker Compose.
2. Clone this repository:

```bash
git clone https://github.com/ciux23/iptv-stream-manager.git
```

3. Enter the project directory:

```bash
cd iptv-stream-manager
```

4. Configure secrets (optional, required for Telegram alerts):

```bash
cp secrets.example.yaml secrets.yaml
```

Edit `secrets.yaml` with your Telegram bot information.

5. Start the service:

```bash
docker compose up -d
```

This pulls `ghcr.io/ciux23/iptv-stream-manager:latest` and starts the container — no build step needed.

## Building from Source

If you prefer to build the image yourself instead of using the prebuilt one:

```bash
docker compose -f compose.dev.yaml up -d --build
```

`compose.dev.yaml` builds the image locally using the included `Dockerfile`.

## Telegram Notifications

Telegram alerts are sent when the failure threshold is reached.

Create a bot using Telegram:

- Open `@BotFather`
- Create a new bot with `/newbot`
- Copy the generated bot token

The `chat_id` can be obtained by sending a message to your bot and checking Telegram updates.

Example `secrets.yaml`:

```yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

`secrets.yaml` contains private data and must not be uploaded to GitHub.
Use `secrets.example.yaml` as the template.

## Usage

After starting the container, the IPTV playlist is available at:

```text
http://YOUR_SERVER_IP:8090/playlist.m3u
```

Example:

```text
http://192.168.0.100:8090/playlist.m3u
```

## Health Check

Verify the service status:

```text
http://YOUR_SERVER_IP:8090/health
```

Example response:

```json
{
  "status": "ok",
  "channels": 81,
  "config_loaded": true,
  "failures": 0,
  "threshold": 3
}
```

When the failure threshold is reached, the status becomes `critical` and a Telegram notification is sent.

## Configuration

Main configuration file:

```text
config.yaml
```

It contains:

- allowed network domains
- channel configuration
- stream sources
- service parameters


## Project Structure

```text
iptv-stream-manager/

├── app.py
├── Dockerfile
├── compose.yaml
├── compose.dev.yaml
├── config.yaml
├── secrets.example.yaml
├── LICENSE
└── README.md
```

## Compatible IPTV Players

The generated M3U playlist can be used with IPTV clients supporting standard M3U playlists, including:

- SS IPTV (Tested on Lg WebOs TV)
- IPTV Smarters (Tested on IPTVnator on MacOs 26.6)
- Kodi (Tested on Amazon Firestick 3td Gen)
- Other compatible IPTV applications
- 

## Disclaimer

This project is provided for personal and educational purposes.

The software only manages and proxies IPTV streams provided by external sources.

The user is responsible for ensuring that all streams and content accessed through this software are used in compliance with applicable laws and the terms of service of the original providers.

The authors are not responsible for the availability, legality or content of third-party streams.
