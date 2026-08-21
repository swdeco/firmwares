# How to publish a firmware update

This is the recurring "cut a new firmware release" runbook for **`swdeco/firmwares`**. When
you have a new build for a board, this is exactly what to add/modify here so the phone app
picks it up.

The app never talks to this repo's source — it just fetches **`manifest.json`**, finds the
connected fireplace's model, and downloads the `.bin` listed there. So publishing = **put the
`.bin` in + point the manifest at it + push.**

---

## The 5 golden rules (read once)

1. **The version must be HIGHER than what's on the board.** The app offers an update whenever
   the manifest version differs from the installed version. Always bump up, or a board that's
   already current won't show an update.
2. **The model key must EXACTLY match the fireplace's `fireplaceModel`** (`"Rais CVNQ"`,
   `"Hybrid mist"`, …). It is the lookup key. A mismatch = the app shows "no firmware for this
   model."
3. **First install is always over USB.** A board can only receive a BLE update if it's already
   running OTA-capable firmware. The very first time (or after a non-OTA build), flash it with
   `pio run -t upload`. After that it's all over Bluetooth.
4. **CRC must match the file.** It's checked before flashing. Let `publish.py` compute it — a
   hand-typed CRC that's wrong = the update refuses with "checksum mismatch."
5. **Public repo, no secrets.** Only compiled `.bin`s + `manifest.json` go here. Never source,
   tokens, or keys.

---

## Repo layout

```
manifest.json                         <- the index the app reads
<model-slug>/
  display/<slug>-display-<version>.bin
  mainboard/<slug>-mainboard-<version>.bin
```
Slugs: `logicwood`, `rais-cvnq`, `rais-visio`, `hybrid-mist`, `denver-f2`, `denver-f6`,
`nordpais`. Keep **versioned filenames** (immutable) so old versions stay for rollback.

---

## The fast way (recommended) — `publish.py`

1. **Bump the version in the source first**, then build, so the number the app shows matches
   the running firmware:
   - Edit `firmwareVersion` in that board's `src/main.cpp`.
   - `pio run -d <that_repo>` (the image is `<repo>/.pio/build/esp32dev/firmware.bin`).
2. **Stage it here** (updates the `.bin` + `manifest.json` in one shot):
   ```bash
   python publish.py --model "Rais CVNQ" \
       --display  "C:/Users/babym/Documents/GitHub/Rais-display/.pio/build/esp32dev/firmware.bin" 4.1.2 \
       --mainboard "C:/Users/babym/Documents/GitHub/Rais_slave_code/.pio/build/esp32dev/firmware.bin" 0.4.2
   ```
   Pass only `--display` **or** only `--mainboard` if you're updating one board. For a brand
   new model, add `--create`.
3. **Commit + push** (the script prints this exact line):
   ```bash
   git -C "C:/Users/babym/Documents/GitHub/firmwares" add -A && git -C "C:/Users/babym/Documents/GitHub/firmwares" commit -m "Rais CVNQ firmware update" && git -C "C:/Users/babym/Documents/GitHub/firmwares" push
   ```

Done. The app shows the new version on its next check.

---

## The manual way (what the script does)

For a display update of, say, Logicwood to `4.3.3`:

1. **Build** (after bumping `firmwareVersion` in `LogicWood_display/src/main.cpp`).
2. **Copy the image** in with a versioned name:
   `logicwood/display/logicwood-display-4.3.3.bin`
3. **Compute size + CRC-32:**
   ```bash
   python -c "import zlib,sys;b=open(sys.argv[1],'rb').read();print('size',len(b),'crc32','%08x'%(zlib.crc32(b)&0xffffffff))" logicwood/display/logicwood-display-4.3.3.bin
   ```
4. **Edit that model/target block in `manifest.json`** — `version`, `file`, `size`, `crc32`:
   ```json
   "Logicwood": {
     "display":   { "version": "4.3.3", "file": "logicwood/display/logicwood-display-4.3.3.bin", "size": 2603840, "crc32": "abcd1234" },
     "mainboard": { "version": "0.6.2", "file": "logicwood/mainboard/logicwood-mainboard-0.6.2.bin", "size": 1218560, "crc32": "5a40d0d8" }
   }
   ```
   Leave the other target untouched if you didn't rebuild it.
5. **Commit + push.**

---

## Adding a brand-new model

The folders for all seven models already exist. To publish one for the first time:

- Make sure that fireplace's **firmware has the OTA capability** (see
  `LogicWood_display/BLE_OTA_PORTING_GUIDE.md`) and USB-flash both boards once.
- Run `publish.py --model "<Exact Model>" --create --display ... <ver> --mainboard ... <ver>`
  (or hand-add the `"<Exact Model>": { ... }` block to `manifest.json`).
- Model key ↔ slug: `Denver F6`→`denver-f6`, `Logicwood`→`logicwood`, `Nordpais`→`nordpais`,
  `Hybrid mist`→`hybrid-mist`, `Denver F2`→`denver-f2`, `Rais CVNQ`→`rais-cvnq`,
  `Rais Visio`→`rais-visio`.

> If two models run an identical binary (rebrands often do), point both entries at the same
> `file` — no need to duplicate the `.bin`.

---

## `manifest.json` field reference

| Field | Meaning |
|-------|---------|
| `schemaVersion` | leave at `1` |
| `updated` | date stamp (the script sets it) |
| `baseUrl` | raw base for downloads; leave as the swdeco raw URL |
| `models["<Model>"]` | keyed by the exact `fireplaceModel` string |
| `…display` / `…mainboard` | one block per board |
| `version` | shown in the app; **bump it every release** |
| `file` | path relative to `baseUrl` |
| `size` | exact byte count of the `.bin` |
| `crc32` | lowercase 8-hex zlib CRC-32 of the `.bin` |

---

## Verify & roll back

- **Verify the push:** `curl -s https://raw.githubusercontent.com/swdeco/firmwares/main/manifest.json`
  should show the new version; the app should then offer it, and after updating show the new
  version with an "Installed" badge.
- **Roll back:** because filenames are versioned, the old `.bin` is still here — just point that
  model's `manifest.json` entry back at the previous `file`/`version`/`size`/`crc32` and push.
  (The board must be running OTA-capable firmware to accept the rollback over BLE.)
