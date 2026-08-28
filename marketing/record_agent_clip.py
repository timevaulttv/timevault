# -*- coding: utf-8 -*-
"""Record a short clip of an agent answering a real question, live.

This is the proof clip. Nothing here is staged: it opens the live site, types a
question into the Agent Console, and waits for whatever the model actually
sends back. If the backend is down the script says so and writes nothing,
because a clip of a broken agent is worse than no clip.

Silent by design. It carries three burned-in lines and is meant to be posted
without a voice over.

    python marketing/record_agent_clip.py            # VORIAN, the default
    python marketing/record_agent_clip.py KAIROS

Output: marketing/demo/agent-<name>.mp4
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo")
RAW = os.path.join(OUT, "ag-raw")
APP = "https://timevault.tv/app"
HEALTH = "https://timevault.tv/api/lyra/health"
FONT = "C\\:/Windows/Fonts/seguisb.ttf"
W, H = 1280, 800

# The question has to be one a script could not fake. This is the hardest thing
# you can ask an arbiter, and the answer is different every time.
QUESTIONS = {
    "VORIAN": "What happens when the buyer and the freelancer both have a fair case?",
    "KAIROS": "How do you verify a deliverable you have never seen before?",
    "SOLON":  "I design brand identities. What should I charge per hour?",
    "LYRA":   "I have never used a crypto app. Where do I start?",
    "NERIS":  "How is a Skill Score different from a star rating?",
    "ATLAS":  "How do you match a buyer to a provider without keywords?",
    "CIRION": "What does the treasury actually hold right now?",
}


def glide(page, x1, y1, x2, y2, ms, steps=44):
    for i in range(steps + 1):
        t = i / steps
        e = t * t * (3 - 2 * t)
        page.mouse.move(x1 + (x2 - x1) * e, y1 + (y2 - y1) * e)
        page.wait_for_timeout(int(ms / steps))


def reach(page, sel, ms=1200, frm=None):
    el = page.query_selector(sel)
    if not el:
        return None
    b = el.bounding_box()
    if b:
        f = frm or (W * 0.45, H * 0.7)
        glide(page, f[0], f[1], b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, ms)
    return el


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


def preflight():
    """Refuse to record a broken agent."""
    try:
        req = urllib.request.Request(HEALTH, headers={"User-Agent": "timevault-recorder"})
        body = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as exc:
        sys.exit("FAIL: /health unreachable (%s). Nothing recorded." % exc)
    if body.get("upstream") != "ok":
        sys.exit("FAIL: upstream is '%s', not ok. Fix the backend before recording."
                 % body.get("upstream"))
    print("  upstream ok, agents are answering")


def main():
    agent = (sys.argv[1] if len(sys.argv) > 1 else "VORIAN").upper()
    if agent not in QUESTIONS:
        sys.exit("FAIL: no question written for %s. Pick one of: %s"
                 % (agent, ", ".join(sorted(QUESTIONS))))
    question = QUESTIONS[agent]

    preflight()

    if os.path.isdir(RAW):
        shutil.rmtree(RAW)
    os.makedirs(RAW, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-device-scale-factor=1", "--hide-scrollbars"])
        ctx = browser.new_context(viewport={"width": W, "height": H},
                                  record_video_dir=RAW,
                                  record_video_size={"width": W, "height": H},
                                  device_scale_factor=1)
        page = ctx.new_page()
        t0 = time.time()
        marks = []

        def mark(name):
            marks.append({"name": name, "t": round(time.time() - t0, 2)})

        page.goto(APP, wait_until="networkidle")
        page.wait_for_timeout(1800)

        mark("open")
        el = reach(page, '[data-section="agents"]', 1100)
        if not el:
            sys.exit("FAIL: agent console nav not found")
        el.click()
        page.wait_for_timeout(2200)          # the seven of them on screen

        mark("pick")
        card = reach(page, '.agent-card[data-agent="%s"]' % agent, 1300)
        if not card:
            sys.exit("FAIL: no card for %s" % agent)
        card.click()
        page.wait_for_timeout(1500)

        inp = page.query_selector("#agentChatInp")
        if not inp:
            sys.exit("FAIL: chat input never appeared")
        b = inp.bounding_box()
        if b:
            glide(page, W * 0.5, b["y"] - 190, b["x"] + 60, b["y"] + b["height"] / 2, 800, steps=24)
        inp.click()

        mark("ask")
        inp.type(question, delay=46)         # slow enough to read along
        page.wait_for_timeout(700)
        page.keyboard.press("Enter")

        # Wait on the real thing. settle() strips .typing-msg once the model
        # replies, so that class disappearing is the signal.
        mark("wait")
        try:
            page.wait_for_selector(".typing-msg", timeout=6000)
            page.wait_for_selector(".typing-msg", state="detached", timeout=60000)
        except Exception:
            sys.exit("FAIL: no reply inside 60s. Nothing written.")

        mark("answer")
        page.wait_for_timeout(600)
        reply = page.evaluate(
            "() => { const m = document.querySelectorAll('#agentChatBox .agent-chat-msg.bot');"
            "return m.length ? m[m.length - 1].textContent.trim() : ''; }")
        if len(reply) < 40:
            sys.exit("FAIL: reply was empty or an error string: %r" % reply[:120])
        print("  %s answered in %d characters" % (agent, len(reply)))
        print("  \"%s...\"" % reply[:96].replace("\n", " "))

        # A good answer runs longer than the box. Land on the first line of it,
        # hold, then walk down at reading pace: showing the tail of a reply
        # nobody watched arrive is worse than showing none of it.
        page.evaluate(
            "() => { const b = document.getElementById('agentChatBox');"
            "const m = b && b.querySelectorAll('.agent-chat-msg.bot');"
            "if (b && m && m.length) b.scrollTop = m[m.length - 1].offsetTop - 8; }")
        page.wait_for_timeout(3200)

        steps = page.evaluate(
            "() => { const b = document.getElementById('agentChatBox');"
            "return b ? Math.max(0, b.scrollHeight - b.clientHeight - b.scrollTop) : 0; }")
        if steps > 4:
            for i in range(34):
                page.evaluate("(d) => { const b = document.getElementById('agentChatBox');"
                              "if (b) b.scrollTop += d; }", steps / 34.0)
                page.wait_for_timeout(105)
        page.wait_for_timeout(2600)          # hold on the last line

        mark("end")
        ctx.close()
        browser.close()

    src = [f for f in os.listdir(RAW) if f.endswith(".webm")]
    if not src:
        sys.exit("FAIL: no video written")

    webm = os.path.join(RAW, src[0])
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", webm],
        capture_output=True, text=True).stdout.strip())

    # Playwright opens the video file before the page paints, so the take starts
    # with a few seconds of blank white. On a black-backed brand that flash is
    # the first thing anyone sees. The gap between the file length and the last
    # mark is exactly that pre-roll, so cutting it needs no pixel guessing, and
    # once it is gone the marks line up with the trimmed video as recorded.
    lead = max(0.0, dur - marks[-1]["t"])
    m = {x["name"]: x["t"] for x in marks}

    # Cut to the first settled frame rather than the first painted one. Loading
    # the dashboard costs several seconds against networkidle, and none of it
    # is worth a viewer's attention: the clip should open on the console, ready.
    start = lead + m["open"]
    m = {k: v - m["open"] for k, v in m.items()}
    body = dur - start
    print("  trimming %.2fs of lead-in and page load, %.1fs of clip left" % (start, body))

    lines = [
        (m["open"] + 0.6, m["pick"] + 1.4, "Seven agents. All of them answering right now."),
        (m["wait"] + 1.0, m["answer"] + 0.2, "Thinking. A live API call, not a lookup table."),
        (m["answer"] + 0.6, body - 0.3, "A real model, not a script. No wallet, no signup."),
    ]
    lines = [(s, e, t) for s, e, t in lines if e - s > 1.2]
    chain = "[0:v]"
    for i, (s, e, text) in enumerate(lines):
        last = i == len(lines) - 1
        chain += ("drawtext=fontfile='%s':text='%s':fontcolor=%s:fontsize=30"
                  ":box=1:boxcolor=black@0.66:boxborderw=20:x=54:y=h-118"
                  ":enable='between(t,%.2f,%.2f)'"
                  % (FONT, esc(text), "#F0DA9B" if last else "white@0.97", s, e))
        chain += "[out]" if last else ","

    out = os.path.join(OUT, "agent-%s.mp4" % agent.lower())
    fpath = os.path.join(OUT, "ag_filter.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(chain)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-ss", "%.3f" % start, "-i", webm,
                    "-filter_complex_script", fpath, "-map", "[out]",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "22",
                    "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an",
                    out], check=True)
    os.remove(fpath)
    shutil.rmtree(RAW, ignore_errors=True)

    final = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", out],
                           capture_output=True, text=True).stdout.strip()
    print("  %s (%.1f MB, %ss)" % (out, os.path.getsize(out) / 1048576, final))


if __name__ == "__main__":
    main()
