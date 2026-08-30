# -*- coding: utf-8 -*-
"""Generate the Time Vault film through the Seedance API.

The key is read from ARK_API_KEY and is never printed, logged or written to
disk. Reference images are sent as base64 so nothing has to be hosted.

    set ARK_API_KEY=...            (cmd)
    $env:ARK_API_KEY="..."         (PowerShell)
    export ARK_API_KEY=...         (bash)

    python marketing/seedance_generate.py

Output: marketing/seedance/timevault-film.mp4
"""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seedance")
BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "dreamina-seedance-2-5-260628"

RESOLUTION = "1080p"
RATIO = "16:9"
DURATION = 30              # the model's maximum for a single generation
WATERMARK = False

# All nine, in the order the prompt numbers them. The console run used the same
# set and rendered the agents beautifully, so the look is worth keeping; what
# needed fixing was the count, and that is handled in the prompt.
REFS = [
    ("01-hourglass.png", "the Time Vault emblem, a gold and violet hourglass"),
    ("02-wordmark.png",  "the Time Vault wordmark"),
    ("03-lyra.png",      "LYRA"),
    ("04-vorian.png",    "VORIAN"),
    ("05-kairos.png",    "KAIROS"),
    ("06-solon.png",     "SOLON"),
    ("07-neris.png",     "NERIS"),
    ("08-atlas.png",     "ATLAS"),
    ("09-cirion.png",    "CIRION"),
]

PROMPT = """ASSET BINDINGS
@Image1 is the Time Vault emblem, a gold and violet hourglass. @Image2 is the
Time Vault wordmark. The seven agents are @Image3 LYRA, @Image4 VORIAN,
@Image5 KAIROS, @Image6 SOLON, @Image7 NERIS, @Image8 ATLAS, @Image9 CIRION.

SUMMARY
A gold hourglass forms out of a storm of violet particles inside a vast dark
vault, seven luminous figures rise behind it, and the mark resolves into the
Time Vault wordmark. Cinematic brand film, deep blacks, gold rim light, slow
push in and then a wide pull back.

PLOT
0-5s: Total darkness. Fine violet and white particles drift in from every edge
of frame and spiral toward the centre, gathering speed. Slow push in. A low
ambient hum rises.

5-10s: The particles collapse into the hourglass emblem from @Image1, which
ignites with gold rim light. Sand inside the glass begins to fall and every
grain glows. The push in continues. A single deep bass hit lands as the mark
ignites.

10-18s: The camera holds still and then begins a slow straight pull back.
Behind the hourglass, seven tall luminous figures fade up one after another,
all facing the camera, all standing still, spread evenly across the full width
of frame. Count them as they arrive: @Image3 furthest left, then @Image4, then
@Image5, then @Image6 standing one pace forward of the rest and closest to
camera, then @Image7, then @Image8, then @Image9 furthest right. That is seven
figures in total and every one of them is fully inside the frame, none cropped
by the left or right edge, none hidden behind the hourglass. Strings rise.

18-24s: Still pulling back, the seven dim to silhouette while the hourglass
brightens. Gold light spreads outward across the floor of the vault.

24-30s: The hourglass lifts slightly and the wordmark from @Image2 resolves
beneath it in clean gold letterforms, holding steady to the end. The particles
settle. The score lands on one sustained low note.

NOTES
A vast dark vault interior throughout, near black, deep shadows, volumetric
haze catching every beam. Palette deep black, violet, magenta and gold.
Cinematic anamorphic look, shallow depth of field, fine film grain. The
hourglass stays centred in frame for the entire shot. Agent appearances
strictly match @Image3 to @Image9 and stay consistent, no face changes. The
group is deliberately uneven, not a symmetrical arrangement: four figures
stand left of the hourglass and three stand right of it. All camera moves slow
and smooth, no handheld shake. Orchestral score with a low bass pulse and
rising strings. No dialogue. No subtitles."""


def key():
    k = os.environ.get("ARK_API_KEY", "").strip()
    if not k:
        sys.exit("FAIL: ARK_API_KEY is not set in this shell. Nothing was sent.")
    return k


def post(path, payload, api_key):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:600]
        sys.exit("FAIL: HTTP %s from the API\n%s" % (e.code, body))


def get(path, api_key):
    req = urllib.request.Request(
        BASE + path, headers={"Authorization": "Bearer " + api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


def main():
    api_key = key()
    os.makedirs(OUT, exist_ok=True)

    content = [{"type": "text", "text": PROMPT}]
    total_mb = 0.0
    for name, what in REFS:
        p = os.path.join(OUT, "upload", name)
        if not os.path.isfile(p):
            sys.exit("FAIL: %s missing" % p)
        total_mb += os.path.getsize(p) / 1048576
        content.append({"type": "image_url",
                        "image_url": {"url": data_uri(p)},
                        "role": "reference_image"})
        print("  ref: %-20s %s" % (name, what))

    if total_mb * 1.34 > 60:
        sys.exit("FAIL: references total %.1f MB encoded, over the 64 MB body limit"
                 % (total_mb * 1.34))

    payload = {"model": MODEL, "content": content,
               "resolution": RESOLUTION, "ratio": RATIO,
               "duration": DURATION, "generate_audio": True,
               "watermark": WATERMARK}

    print("\n  %s  %s  %ss  audio on  watermark %s"
          % (MODEL, RESOLUTION, DURATION, "on" if WATERMARK else "off"))
    print("  submitting...")
    task = post("/contents/generations/tasks", payload, api_key)
    tid = task.get("id")
    if not tid:
        sys.exit("FAIL: no task id returned: %s" % json.dumps(task)[:400])
    print("  task %s" % tid)

    started = time.time()
    delay = 6
    while True:
        time.sleep(delay)
        r = get("/contents/generations/tasks/" + tid, api_key)
        status = r.get("status")
        waited = time.time() - started
        print("    %-10s %4.0fs" % (status, waited))
        if status == "succeeded":
            break
        if status in ("failed", "cancelled"):
            sys.exit("FAIL: task %s\n%s" % (status, json.dumps(r)[:700]))
        if waited > 1500:
            sys.exit("FAIL: still %s after 25 minutes. Task id %s" % (status, tid))
        delay = min(delay + 2, 20)

    url = (r.get("content") or {}).get("video_url")
    if not url:
        sys.exit("FAIL: succeeded but no video_url\n%s" % json.dumps(r)[:700])

    dst = os.path.join(OUT, "timevault-film.mp4")
    print("  downloading...")
    with urllib.request.urlopen(url, timeout=300) as src, open(dst, "wb") as f:
        f.write(src.read())

    used = (r.get("usage") or {}).get("total_tokens")
    print("\n  %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1048576))
    print("  %s %s %ss" % (r.get("resolution"), r.get("ratio"), r.get("duration")))
    if used:
        print("  %s tokens, about $%.2f at 0.0064 per thousand" % (
            format(used, ","), used / 1000 * 0.0064))
    print("\n  Revoke the key now if you want to. Nothing else here needs it.")


if __name__ == "__main__":
    main()
