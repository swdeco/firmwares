#!/usr/bin/env python3
"""
publish.py — stage a firmware update into this repo (swdeco/firmwares).

For each target you pass, it: copies the built firmware.bin in with a versioned name,
computes its size + CRC-32, and updates that model's entry in manifest.json. It does NOT
commit or push — it prints the git commands for you to run.

Examples
--------
Update just the mainboard of an existing model:
    python publish.py --model "Rais CVNQ" \
        --mainboard "C:/Users/babym/Documents/GitHub/Rais_slave_code/.pio/build/esp32dev/firmware.bin" 0.4.2

Update both boards:
    python publish.py --model "Logicwood" \
        --display  ".../LogicWood_display/.pio/build/esp32dev/firmware.bin" 4.3.3 \
        --mainboard ".../LogicWood_main/.pio/build/esp32dev/firmware.bin"   0.6.3

Add a brand-new model (creates its folders + manifest entry):
    python publish.py --model "Denver F2" --create \
        --display  ".../DenverF2_display/.pio/build/esp32dev/firmware.bin" 1.0.0 \
        --mainboard ".../DenverF2/.pio/build/esp32dev/firmware.bin"        1.0.0
"""
import argparse, json, os, shutil, sys, zlib, datetime

REPO = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(REPO, "manifest.json")


def slugify(model):
    return model.strip().lower().replace(" ", "-")


def crc_size(path):
    b = open(path, "rb").read()
    return len(b), "%08x" % (zlib.crc32(b) & 0xFFFFFFFF)


def stage(manifest, model, slug, target, src, version, create):
    if not os.path.isfile(src):
        sys.exit("ERROR: no such firmware .bin: " + src)
    folder = "mainboard" if target == "mainboard" else "display"
    rel = "%s/%s/%s-%s-%s.bin" % (slug, folder, slug, folder, version)
    dst = os.path.join(REPO, *rel.split("/"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    size, crc = crc_size(dst)
    manifest["models"].setdefault(model, {})[target] = {
        "version": version, "file": rel, "size": size, "crc32": crc,
    }
    print("  %-9s v%-8s  %8d bytes  crc32=%s  -> %s" % (target, version, size, crc, rel))


def main():
    ap = argparse.ArgumentParser(description="Stage a firmware update into swdeco/firmwares.")
    ap.add_argument("--model", required=True, help='exact fireplaceModel string, e.g. "Rais CVNQ"')
    ap.add_argument("--slug", help="folder slug (default: model lowercased, spaces->dashes)")
    ap.add_argument("--display", nargs=2, metavar=("BIN", "VERSION"), help="display firmware.bin + version")
    ap.add_argument("--mainboard", nargs=2, metavar=("BIN", "VERSION"), help="mainboard firmware.bin + version")
    ap.add_argument("--create", action="store_true", help="allow creating a new model entry")
    args = ap.parse_args()

    if not args.display and not args.mainboard:
        sys.exit("ERROR: pass --display and/or --mainboard.")

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    slug = args.slug or slugify(args.model)

    if args.model not in manifest["models"] and not args.create:
        sys.exit('ERROR: model "%s" is not in the manifest. Check the spelling (it must match '
                 'the fireplace\'s fireplaceModel exactly), or pass --create for a new model.'
                 % args.model)

    print('Model "%s"  (slug: %s)' % (args.model, slug))
    if args.display:
        stage(manifest, args.model, slug, "display", args.display[0], args.display[1], args.create)
    if args.mainboard:
        stage(manifest, args.model, slug, "mainboard", args.mainboard[0], args.mainboard[1], args.create)

    manifest["updated"] = datetime.date.today().isoformat()
    open(MANIFEST, "w", encoding="utf-8").write(json.dumps(manifest, indent=2) + "\n")
    print("\nmanifest.json updated. Now commit + push:\n")
    print('  git -C "%s" add -A && git -C "%s" commit -m "%s firmware update" && git -C "%s" push'
          % (REPO, REPO, args.model, REPO))


if __name__ == "__main__":
    main()
