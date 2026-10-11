# STIG Authoring Pro

A desktop app for writing STIG benchmarks. You fill in each rule in a form (IDs, severity, NIST controls, CCIs, the vulnerability discussion, the check and the fix) and the app builds XCCDF 1.1 XML in the layout DISA STIGs use, live, in a pane next to the form. It imports existing benchmarks, exports new ones, and ships as a single Linux binary.

Writing STIG XML by hand is slow and easy to break: one unescaped `<` in a check and the whole file stops parsing. The form keeps every rule in the same shape, escapes the text for you, and the preview shows exactly what will be written.

## What it does

- **Rule editor.** One form per rule, grouped into identifiers, compliance, description, and audit and fix, plus free-form key/value attributes for anything the schema does not cover.
- **Live XML preview** with syntax highlighting, refreshed every 1.5 seconds as you type.
- **Import and export.** Reads XCCDF benchmarks (including descriptions stored as escaped text or as real subelements, since different tools write them differently) and writes them back out. Text inside CDATA is escaped so a stray `]]>` cannot break the file.
- **Rule management.** Search, add, duplicate, reorder and delete rules. Duplicates get a unique ID automatically.
- **Benchmark properties.** ID, title, description, version, publisher and release date in one dialog. Group and rule IDs left blank are derived from the benchmark ID on export.
- **Autosave and recovery.** Work is saved to `~/.stig_authoring_autosave.xml` every 1.5 seconds. If the app did not close cleanly, it offers to restore that file on the next start, and closing with unexported changes asks first.
- **Dark and light themes,** and zoom for the whole UI or just the XML pane.

`examples/demo-benchmark.xml` is a six-rule benchmark for a fictional ExampleOS. Import it to see a filled-in file. The rule text is written for the demo; the NIST and CCI references are the public mappings.

## Running it

Download the binary from the latest [release](../../releases) and run it:

```bash
chmod +x STIG-Authoring-Pro-v*-linux-x86_64
./STIG-Authoring-Pro-v*-linux-x86_64
```

Or from source, with Python 3 and Tk:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./run.sh            # or: python main.py
```

On Debian or Ubuntu, Tk comes from `sudo apt install python3-tk`.

## How it is built

| File | What it holds |
| --- | --- |
| `models.py` | `STIGRule` and `STIGBenchmark`, plain data classes |
| `engine.py` | XCCDF parsing (namespace stripping, both description formats, multi-value NIST and CCI) and generation |
| `gui.py` | The CustomTkinter app: three resizable panes, theming, zoom, autosave |
| `stig_authoring_pro.spec` | PyInstaller spec for the one-file binary |
| `.github/workflows/build-release.yml` | Builds the binary and attaches it to a GitHub release when a `v*` tag is pushed |

Python, CustomTkinter, ElementTree, PyInstaller, GitHub Actions.
