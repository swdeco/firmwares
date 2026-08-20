# swdeco / firmwares

Over-the-air firmware for the Decoflame fireplaces. The phone app reads the connected
fireplace's **model** and looks it up in [`manifest.json`](manifest.json) to find the right
**display** and **mainboard** firmware, then flashes both over Bluetooth.

**This repo is public** so the app can always fetch firmware with no token. Put **only**
compiled `.bin` files here — no source.

---

## How the app uses this

1. The app reads the fireplace's `fireplaceModel` (one of the fixed strings below).
2. It fetches `manifest.json` from
   `https://raw.githubusercontent.com/swdeco/firmwares/main/manifest.json`.
3. It looks up `models[<model>]` → `display` and `mainboard` `{version, file}`.
4. It downloads each `.bin` from `baseUrl + file` and flashes it over BLE (display flashes
   itself; the mainboard is flashed by the display relaying over the internal UART).

The app computes the image CRC-32 and the firmware verifies it end-to-end, so a bad download
can never brick a board. The optional `crc32` in the manifest lets the app also catch a
truncated download *before* it starts flashing.

## Model keys (must match the app exactly)

`manifest.json` keys are the exact `fireplaceModel` strings the firmware reports:

`Denver F6` · `Logicwood` · `Nordpais` · `Hybrid mist` · `Denver F2` · `Rais CVNQ` · `Rais Visio`

A model with no entry in `manifest.json` shows as "no firmware published" in the app. Folders
are pre-created for every model; fill them in as you build each one.

## Layout

```
manifest.json
<model-slug>/
  display/<model>-display-<version>.bin
  mainboard/<model>-mainboard-<version>.bin
```

Model slugs: `logicwood`, `rais-cvnq`, `rais-visio`, `hybrid-mist`, `denver-f2`,
`denver-f6`, `nordpais`.

## Publishing a new firmware

1. Build the board's firmware in PlatformIO. The image is
   `<repo>/.pio/build/esp32dev/firmware.bin`.
   - **Bump `firmwareVersion`** in that board's `src/main.cpp` *before* building, so the
     version shown in the app matches the running firmware.
2. Copy it here with a **versioned filename**, e.g.
   `logicwood/display/logicwood-display-4.1.0.bin` (keep old versions for rollback).
3. Update that model's `version`, `file`, `size`, and `crc32` in `manifest.json`.
   Compute size + crc32 with:
   ```bash
   python -c "import zlib,sys;b=open(sys.argv[1],'rb').read();print('size',len(b),'crc32','%08x'%(zlib.crc32(b)&0xffffffff))" firmware.bin
   ```
4. Commit and push. The app picks it up on its next check.

> If two models share an identical binary (rebrands often do), point both entries at the
> same `file` — no need to duplicate the `.bin`.

## Currently published

| Model | Display | Mainboard |
|-------|---------|-----------|
| Logicwood | 4.1.0 | 0.4.0 |

_(Other models: folders ready, firmware not published yet.)_
