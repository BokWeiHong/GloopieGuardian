wasmshark
=========

webshark is a browser-based packet analysis UI (built with Angular) used by the GloopieGuardian project to inspect and analyze PCAP files in a web interface.

Using webshark for GloopieGuardian
----------------------------------

- Purpose: provide a lightweight, browser-accessible network capture viewer for GloopieGuardian's analysis and demos.

Quick start
-----------

1. Install dependencies:

```bash
npm install
```

2. Start the app (optionally provide a PCAP to load automatically):

```bash
# serve and open on 0.0.0.0:8085
npm run start -- /path/to/your_capture.pcap

# or without a pcap:
npm run start
```

If you pass a PCAP path to `npm run start --`, the file will be copied to `src/assets/auto.pcap` and served by the app automatically.

3. Open the UI in a browser:

```
http://localhost:8085
```

Notes
-----
- The `start` script runs `node start.js` which launches `ng serve --port 8085 --host=0.0.0.0`.
- There are other npm scripts available (for demo or kiosk builds): `npm run demo`, `npm run start:kiosk`, and `npm run build`.

If you'd like, I can also add a short example showing how GloopieGuardian integrates with webshark (API/hooks or automation instructions). 
