"""Capture the README screenshots.

Runs the real app on a virtual display, loads the demo benchmark and saves
PNGs of the main views. Used by .github/workflows/screenshots.yml:

    xvfb-run -a -s "-screen 0 1600x1000x24" python scripts/screenshots.py OUTDIR

Needs ImageMagick's `import` on PATH.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from engine import parse_benchmark_xml  # noqa: E402
from gui import STIGApp  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots")
os.makedirs(OUT, exist_ok=True)
W, H = 1440, 900

app = STIGApp()
app.geometry(f"{W}x{H}+0+0")


def grab(name):
    app.update_idletasks()
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    path = os.path.join(OUT, name)
    subprocess.run(
        ["import", "-window", "root", "-crop", f"{W}x{H}+{x}+{y}", "+repage", path],
        check=True,
    )
    print("saved", path)


def load_demo():
    app.load_benchmark(parse_benchmark_xml("examples/demo-benchmark.xml"))
    app.select_rule(1)          # the high-severity SSH root logon rule
    app.update_xml_preview()


def search():
    app.search_entry.insert(0, "ssh")
    app.on_search_changed()


def clear_search():
    app.search_entry.delete(0, "end")
    app.on_search_changed()


def finish():
    app.destroy()
    os._exit(0)


# Each step runs after the previous one has had time to render and for the
# 1.5 s change checker to refresh the preview.
steps = [
    (1500, load_demo),
    (2500, lambda: grab("editor-dark.png")),
    (200, app.toggle_theme),
    (2500, lambda: grab("editor-light.png")),
    (200, app.toggle_theme),
    (1500, search),
    (2000, lambda: grab("search.png")),
    (200, clear_search),
    (500, app.open_benchmark_info),
    (2000, lambda: grab("benchmark-info.png")),
    (200, finish),
]

t = 0
for delay, fn in steps:
    t += delay
    app.after(t, fn)

app.mainloop()
