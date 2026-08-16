# IPTV Stream Manager

IPTV Stream Manager è un servizio web basato su Python e aiohttp per la gestione di playlist IPTV compatibili con client come SS IPTV.

Il progetto permette di gestire differenti tipologie di stream:

- Canali Rai con recupero e gestione automatica dello stream.
- Canali diretti tramite URL HLS/M3U8 configurati manualmente.
- Canali dinamici con recupero dell'indirizzo dello stream dal provider.

## Funzionalità

- Generazione automatica della playlist M3U.
- Endpoint IPTV dedicati.
- Proxy degli stream quando necessario.
- Riscrittura dei manifest HLS.
- Gestione dei canali tramite file config.yaml.
- Health check del servizio.
- Compatibilità con client IPTV come SS IPTV.
## Struttura del progetto

iptv-stream-manager/

- app.py
- config.yaml
- compose.yaml
- README.md
- .gitignore

## Configurazione

La configurazione dei canali viene gestita tramite il file config.yaml.

Il progetto supporta tre sezioni principali:

### Canali Rai

Canali gestiti tramite identificativo del contenuto Rai.

### Canali diretti

Canali con URL diretto HLS/M3U8 configurato manualmente.

### Canali dinamici

Canali per i quali l'indirizzo dello stream viene recuperato dinamicamente.
## Endpoint disponibili

| Endpoint | Descrizione |
|---|---|
| `/health` | Stato del servizio |
| `/playlist.m3u` | Playlist IPTV generata |
| `/stream/{channel}` | Stream di un canale |
| `/fetch/{encoded_url}` | Proxy di una risorsa dello stream |

## Avvio con Docker Compose

Il servizio può essere avviato tramite Docker Compose:

docker compose up -d

Il container espone la porta:

8090 -> 8080

La porta 8090 sull'host è stata scelta per evitare conflitti con altri servizi già presenti.

La porta interna del container rimane 8080.
## Utilizzo con SS IPTV

Dopo l'avvio del servizio, la playlist è disponibile tramite:

http://HOST:8090/playlist.m3u

Sostituire HOST con l'indirizzo del dispositivo dove gira il servizio.

## Health Check

Verifica stato servizio:

http://HOST:8090/health

## Note

Gli URL degli stream dipendono dai rispettivi provider e possono cambiare nel tempo.

Il repository non contiene credenziali personali o configurazioni specifiche dell'installazione locale.

## Disclaimer

This project is provided for personal and educational purposes.

The software only manages and proxies IPTV streams provided by external sources.

The user is responsible for ensuring that all streams and content accessed through this software are used in compliance with applicable laws and the terms of service of the original providers.

The authors are not responsible for the availability, legality or content of third-party streams.
