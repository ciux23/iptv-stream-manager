import asyncio
import base64
import re
import time
import yaml
import logging
import sys
from urllib.parse import urljoin, urlparse

from aiohttp import ClientSession, ClientTimeout, web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- COSTANTI GLOBALI IMMUTABILI ---
RAI_USER_AGENT = "rainet/4.0.5"

# Caricamento secrets locali
try:
    with open("/app/secrets.yaml") as f:
        SECRETS = yaml.safe_load(f) or {}
except FileNotFoundError:
    SECRETS = {}

TELEGRAM_BOT_TOKEN = (
    SECRETS.get("telegram", {}).get("bot_token")
)

TELEGRAM_CHAT_ID = (
    SECRETS.get("telegram", {}).get("chat_id")
)

TIMEOUT = ClientTimeout(total=25)
URI_ATTRIBUTE = re.compile(r'URI="([^"]+)"')
# ------------------------------------


# --- VARIABILI GLOBALI DI CONFIGURAZIONE ---
CHANNELS = {}
DIRECT_CHANNELS = {}
DYNAMIC_CHANNELS = {}
ALLOWED_HOST_SUFFIXES = []
CHANNEL_META = {}

try:
    with open("/app/channels_selected.yaml", "r") as f:
        selected = yaml.safe_load(f)

    CHANNEL_META = {
        c["name"].replace(" Ⓖ", "").replace(" Ⓢ", ""): c
        for c in selected.get("channels", [])
    }

    logging.info(f"Metadata canali caricati: {len(CHANNEL_META)}")

except Exception:
    logging.exception("Metadata canali non caricati")

# Cache degli URL dei canali dinamici
DYNAMIC_CACHE = {}
DYNAMIC_LOCKS = {}

# Failure threshold per health check
FAILURE_COUNT = 0
FAILURE_THRESHOLD = 3
TELEGRAM_ALERT_SENT = False

# Rinnova il token prima della sua scadenza effettiva
DYNAMIC_CACHE_MARGIN = 30
# ---------------------------------------------


def load_config(file_path="/app/config.yaml"):
    """Carica la configurazione dai file YAML."""
    global CHANNELS, DIRECT_CHANNELS
    global DYNAMIC_CHANNELS, ALLOWED_HOST_SUFFIXES

    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)

        # Domini consentiti
        ALLOWED_HOST_SUFFIXES = config.get(
            "network_config", {}
        ).get("allowed_host_suffixes", [])

        # Mappa Rai Channels
        CHANNELS = {
            slug: (name, content_id)
            for slug, (name, content_id)
            in config.get("rai_channels", {}).items()
        }

        # Mappa Direct Channels
        DIRECT_CHANNELS = {
            slug: (name, url)
            for slug, (name, url)
            in config.get("direct_channels", {}).items()
        }

        # Mappa Dynamic Channels
        DYNAMIC_CHANNELS = {
            slug: (name, asset_id)
            for slug, (name, asset_id)
            in config.get("dynamic_channels", {}).items()
        }

        logging.info("Configurazione caricata con successo.")

    except FileNotFoundError:
        logging.critical(
            "ERRORE CRITICO: File di configurazione "
            "'config.yaml' non trovato in /app. "
            "Controlla il bind mount."
        )
        sys.exit(1)

    except yaml.YAMLError:
        logging.exception("Errore di parsing di YAML")
        sys.exit(1)


# Esegui il caricamento della configurazione subito all'avvio
load_config()


def public_base(request):
    return f"{request.scheme}://{request.host}"


def encode_url(value):
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def decode_url(value):
    return base64.urlsafe_b64decode(
        value + "=" * (-len(value) % 4)
    ).decode()


async def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram non configurato")
        return

    url = (
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    try:
        async with ClientSession() as session:
            await session.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message
                }
            )

        logging.info("Notifica Telegram inviata")

    except Exception:
        logging.exception("Errore invio Telegram")


def is_allowed(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    return (
        parsed.scheme == "https"
        and any(
            host.endswith(suffix)
            for suffix in ALLOWED_HOST_SUFFIXES
        )
    )


def proxied_url(request, url):
    return f"{public_base(request)}/fetch/{encode_url(url)}"


def rewrite_manifest(request, manifest, source_url):
    def rewrite_attribute(match):
        return (
            f'URI="{proxied_url(request, urljoin(source_url, match.group(1)))}"'
        )

    lines = []

    for line in manifest.splitlines():
        if line.startswith("#"):
            lines.append(
                URI_ATTRIBUTE.sub(rewrite_attribute, line)
            )
        elif line.strip():
            lines.append(
                proxied_url(
                    request,
                    urljoin(source_url, line.strip())
                )
            )
        else:
            lines.append(line)

    return "\n".join(lines) + "\n"


async def fetch(session, url):
    global FAILURE_COUNT

    if not is_allowed(url):
        raise web.HTTPForbidden(text="Host non consentito")

    try:
        response = await session.get(
            url,
            allow_redirects=True
        )
        response.raise_for_status()

        FAILURE_COUNT = 0

        return response

    except asyncio.TimeoutError as exc:
        FAILURE_COUNT += 1
        logging.exception(f"Timeout del flusso: {url}")
        raise web.HTTPGatewayTimeout(
            text="Timeout del flusso Rai"
        ) from exc

    except Exception as exc:
        FAILURE_COUNT += 1
        logging.exception(f"Flusso non disponibile: {url}")
        raise web.HTTPBadGateway(
            text=f"Flusso non disponibile: {exc}"
        ) from exc


async def get_dynamic_stream(request, channel):
    """
    Recupera l'URL HLS di un canale dinamico tramite l'API del provider.

    L'URL viene memorizzato in cache fino a 30 secondi prima
    della scadenza del token.
    """

    if channel not in DYNAMIC_CHANNELS:
        raise web.HTTPNotFound(
            text="Canale dinamico sconosciuto"
        )

    _, asset_id = DYNAMIC_CHANNELS[channel]

    # Un lock separato per ogni canale evita richieste duplicate
    # all'API quando arrivano più richieste contemporaneamente.
    lock = DYNAMIC_LOCKS.setdefault(
        channel,
        asyncio.Lock()
    )

    async with lock:

        now = time.time()

        # --------------------------------------------------
        # CONTROLLO CACHE
        # --------------------------------------------------

        cached = DYNAMIC_CACHE.get(channel)

        if cached:
            stream_url, expires_at = cached

            if now < expires_at - DYNAMIC_CACHE_MARGIN:
                return stream_url

        # --------------------------------------------------
        # RICHIESTA NUOVO URL
        # --------------------------------------------------

        api_url = (
            "https://apid.sky.it/vdp/v1/getLivestream"
            f"?id={asset_id}&isMobile=false"
        )

        try:
            async with request.app["session"].get(
                api_url
            ) as response:

                response.raise_for_status()
                data = await response.json()

        except asyncio.TimeoutError as exc:
            logging.exception(f"Timeout API per il canale {channel}")
            raise web.HTTPGatewayTimeout(
                text=f"Timeout API per il canale {channel}"
            ) from exc

        except Exception as exc:
            logging.exception(
                f"Impossibile ottenere lo stream di {channel}"
            )
            raise web.HTTPBadGateway(
                text=(
                    f"Impossibile ottenere lo stream "
                    f"di {channel}: {exc}"
                )
            ) from exc

        # --------------------------------------------------
        # ESTRAZIONE STREAMING URL
        # --------------------------------------------------

        stream_url = data.get("streaming_url")

        if not stream_url:
            raise web.HTTPBadGateway(
                text=(
                    f"L'API non ha restituito uno "
                    f"streaming_url per {channel}"
                )
            )

        # --------------------------------------------------
        # CONTROLLO SICUREZZA URL
        # --------------------------------------------------

        if not is_allowed(stream_url):
            raise web.HTTPForbidden(
                text=(
                    f"Host dello stream non consentito "
                    f"per {channel}"
                )
            )

        # --------------------------------------------------
        # DETERMINAZIONE SCADENZA TOKEN
        # --------------------------------------------------

        expires_at = now + 240

        match = re.search(
            r"(?:^|[?~])exp=(\d+)",
            stream_url
        )

        if match:
            expires_at = int(match.group(1))

        # --------------------------------------------------
        # SALVATAGGIO CACHE
        # --------------------------------------------------

        DYNAMIC_CACHE[channel] = (
            stream_url,
            expires_at
        )

        return stream_url


async def stream(request):
    channel = request.match_info["channel"]

    # ======================================================
    # CANALE RAI
    # ======================================================

    if channel in CHANNELS:

        _, content_id = CHANNELS[channel]

        url = (
            "https://mediapolis.rai.it/"
            "relinker/relinkerServlet.htm"
        )

        url += (
            f"?cont={content_id}"
            "&output=7"
            "&forceUserAgent=rainet/4.0.5"
        )

    # ======================================================
    # CANALE DINAMICO
    # ======================================================

    elif channel in DYNAMIC_CHANNELS:

        url = await get_dynamic_stream(
            request,
            channel
        )

    # ======================================================
    # CANALE DIRETTO
    # ======================================================

    elif channel in DIRECT_CHANNELS:

        _, url = DIRECT_CHANNELS[channel]

    # ======================================================
    # CANALE SCONOSCIUTO
    # ======================================================

    else:
        raise web.HTTPNotFound(
            text="Canale sconosciuto"
        )

    # ======================================================
    # RECUPERO MANIFEST
    # ======================================================

    response = await fetch(
        request.app["session"],
        url
    )

    try:
        return web.Response(
            text=rewrite_manifest(
                request,
                await response.text(),
                str(response.url)
            ),
            content_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-store"
            },
        )

    finally:
        response.release()


async def proxy_fetch(request):
    try:
        url = decode_url(
            request.match_info["encoded_url"]
        )

    except Exception as exc:
        raise web.HTTPBadRequest(
            text="URL non valido"
        ) from exc

    response = await fetch(
        request.app["session"],
        url
    )

    try:
        content_type = response.headers.get(
            "Content-Type",
            "application/octet-stream"
        )

        if (
            "mpegurl" in content_type.lower()
            or response.url.path.endswith(".m3u8")
        ):

            return web.Response(
                text=rewrite_manifest(
                    request,
                    await response.text(),
                    str(response.url)
                ),
                content_type=(
                    "application/vnd.apple.mpegurl"
                ),
                headers={
                    "Cache-Control": "no-store"
                },
            )

        return web.Response(
            body=await response.read(),
            headers={
                "Content-Type": content_type,
                "Cache-Control": "no-store"
            },
        )

    finally:
        response.release()


async def playlist(request):
    lines = ['#EXTM3U url-tvg="https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz"']

    base = public_base(request)

    # ======================================================
    # CANALI RAI
    # ======================================================

    for slug, (name, _) in CHANNELS.items():

        meta = CHANNEL_META.get(name, {})

        lines += [
            (
                '#EXTINF:-1 '
                f'tvg-id="{meta.get("tvg_id","")}" '
                f'tvg-name="{name}" '
                f'tvg-logo="{meta.get("logo","")}" '
                f'group-title="{meta.get("group","Italia")}",'
                f'{name}'
            ),
            f"{base}/stream/{slug}"
        ]

    # ======================================================
    # CANALI DINAMICI
    # ======================================================

    for slug, (name, _) in DYNAMIC_CHANNELS.items():

        meta = CHANNEL_META.get(name, {})

        lines += [
            (
                '#EXTINF:-1 '
                f'tvg-id="{meta.get("tvg_id","")}" '
                f'tvg-name="{name}" '
                f'tvg-logo="{meta.get("logo","")}" '
                f'group-title="{meta.get("group","Italia")}",'
                f'{name}'
            ),
            f"{base}/stream/{slug}"
        ]

    # ======================================================
    # CANALI DIRETTI
    # ======================================================

    for slug, (name, url) in DIRECT_CHANNELS.items():

        meta = CHANNEL_META.get(name, {})

        lines += [
            (
                '#EXTINF:-1 '
                f'tvg-id="{meta.get("tvg_id","")}" '
                f'tvg-name="{name}" '
                f'tvg-logo="{meta.get("logo","")}" '
                f'group-title="{meta.get("group","Italia")}",'
                f'{name}'
            ),
            url
        ]

    return web.Response(
        text="\n".join(lines) + "\n",
        content_type="audio/x-mpegurl"
    )


async def health(request):
    global FAILURE_COUNT, TELEGRAM_ALERT_SENT

    if FAILURE_COUNT >= FAILURE_THRESHOLD:
        status = "critical"

        if not TELEGRAM_ALERT_SENT:
            await send_telegram(
                "⚠️ IPTV Stream Manager: failure threshold raggiunta"
            )
            TELEGRAM_ALERT_SENT = True

    else:
        status = "ok"
        TELEGRAM_ALERT_SENT = False

    return web.json_response({
        "status": status,
        "channels": len(CHANNEL_META),
        "config_loaded": True,
        "failures": FAILURE_COUNT,
        "threshold": FAILURE_THRESHOLD
    })


async def startup(app):
    app["session"] = ClientSession(
        timeout=TIMEOUT,
        headers={
            "User-Agent": RAI_USER_AGENT
        }
    )


async def cleanup(app):
    await app["session"].close()


app = web.Application()

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)

app.router.add_get(
    "/health",
    health
)

app.router.add_get(
    "/playlist.m3u",
    playlist
)

app.router.add_get(
    "/stream/{channel}",
    stream
)

app.router.add_get(
    "/fetch/{encoded_url}",
    proxy_fetch
)

web.run_app(
    app,
    host="0.0.0.0",
    port=8080
)