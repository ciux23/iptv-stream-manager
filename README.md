# IPTV Stream Manager

IPTV Stream Manager è un servizio web basato su Python e aiohttp per gestire una playlist IPTV destinata a client come SS IPTV.

Il progetto supporta tre tipologie di canali:

- Canali Rai: lo stream viene individuato e gestito dal servizio.
- Canali diretti: utilizzano direttamente un URL HLS/M3U8 configurato.
- Canali dinamici: l'URL dello stream viene recuperato dinamicamente dal provider.

## Funzionalità

- Generazione automatica della playlist M3U.
- Gestione separata dei canali Rai, diretti e dinamici.
- Proxy degli stream quando necessario.
- Riscrittura dei manifest HLS.
- Controllo degli host autorizzati.
- Endpoint di health check.
- Configurazione dei canali tramite config.yaml.

## Struttura del progetto

iptv-stream-manager/

- app.py
- config.yaml
- compose.yaml
- README.md

## Configurazione

I canali sono configurati nel file config.yaml.

Le sezioni principali sono:

rai_channels

Contiene i canali Rai gestiti tramite content_id.

direct_channels

Contiene canali con URL diretto HLS/M3U8.

dynamic_channels

Contiene canali per i quali l'indirizzo dello stream viene recuperato dinamicamente dal provider.

## Endpoint disponibili

/health

Verifica lo stato del servizio.

/playlist.m3u

Restituisce la playlist IPTV generata.

/stream/{channel}

Gestisce lo stream di un canale.

/fetch/{encoded_url}

Gestisce il proxy di una risorsa dello stream.

## Avvio con Docker Compose

Il progetto include un file compose.yaml.

Avvio:

docker compose up -d

Il servizio utilizza Python 3.13 e installa automaticamente le dipendenze necessarie.

La porta configurata è:

8090 sull'host verso 8080 nel container

La porta 8090 è stata scelta per evitare conflitti con altri servizi già presenti sul sistema.

## Utilizzo con SS IPTV

Dopo l'avvio la playlist è disponibile tramite:

http://HOST:8090/playlist.m3u

Sostituire HOST con l'indirizzo del dispositivo dove è in esecuzione il servizio.

## Health Check

Per verificare il funzionamento:

http://HOST:8090/health

## Note

Gli URL degli stream dipendono dai rispettivi provider e possono cambiare nel tempo.

Il repository non contiene credenziali personali o configurazioni specifiche dell'installazione locale.
