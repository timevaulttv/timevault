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

# Only the two brand assets. Seven agent portraits in one 30 second shot is
# what produced six figures instead of seven in the console, and every extra
# reference costs stability.
REFS = [
    ("01-hourglass.png", "the Time Vault emblem, a gold and violet hourglass"),
    ("02-wordmark.png",  "the Time Vault wordmark"),
]

PROMPT = """ASSET BINDINGS
@Image1 is the Time Vault emblem, a gold and violet hourglass. @Image2 is the
Time Vault wordmark.

SUMMARY
A freelancer works alone at night and is met with silence after delivering,
then the same moment replays with the payment already sealed in gold before
the work begins, and the film resolves on the Time Vault mark. Cinematic
realistic short film, cold blue night turning to warm gold, locked-off camera
with two slow push ins.

PLOT
0-5s: Night. A freelancer sits at a cluttered desk in a small flat, face lit
only by a monitor. They click once to send a delivery, lean back, and let out
a small satisfied breath. A soft click, then room tone.

5-11s: The camera holds the identical framing while time passes around them.
Light from the window cycles from night to day to night twice. Coffee cups
gather on the desk. Their posture sinks lower with each cycle and the
satisfaction drains out of their face. The monitor glow stays cold and
constant.

11-15s: Close on their hand lifting a phone, thumb hovering over an unanswered
message thread, then setting the phone face down without sending anything.
They rub their eyes. Silence apart from a clock.

15-17s: Cut to black. One thin horizontal line of gold light draws itself
across the centre of the darkness and holds.

17-24s: The same desk and the same person, but the order is reversed. Before
they begin working, a warm gold seal of light closes over a shape on the desk
and locks with a solid mechanical sound. They work, then click once to
deliver. The gold light immediately releases and flows across the desk toward
them. They look up, caught off guard, and a real smile arrives. The room is
now lit gold rather than cold blue.

24-30s: The desk falls away into darkness. The hourglass emblem from @Image1
resolves at the centre in gold, sand falling inside the glass, with the
wordmark from @Image2 beneath it. The score lands on one sustained low note.

NOTES
Cinematic realistic short film throughout, 35mm cinema lens, shallow depth of
field, fine film grain, authentic skin texture, natural performance, no
beautification. The first half is cold blue and grey and the second half is
warm gold; that colour turn is the point of the film and must be obvious.
Camera locked off apart from one very slow push in during 17-24s and another
during 24-30s. Keep the same person, the same desk and the same framing across
both halves so the reversal reads. Score is sparse piano and low strings,
patient in the first half, opening up at the 17 second mark. Room tone and
small practical sounds only. No dialogue. No subtitles."""


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
