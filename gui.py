import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
from models import STIGBenchmark, STIGRule
from datetime import date
from engine import DEFAULT_BENCHMARK_ID, generate_benchmark_xml, parse_benchmark_xml

ctk.set_appearance_mode("dark")

AUTOSAVE_PATH = os.path.join(os.path.expanduser("~"), ".stig_authoring_autosave.xml")

# Theme palettes
THEMES = {
    "dark": {
        "COLOR_BG_DARK":        "#0d0d12",
        "COLOR_BG_MAIN":        "#111118",
        "COLOR_BG_CARD":        "#16161f",
        "COLOR_BG_INPUT":       "#1c1c28",
        "COLOR_BG_HOVER":       "#1f1f2e",
        "COLOR_BORDER":         "#2a2a3c",
        "COLOR_ACCENT":         "#5e6ad2",
        "COLOR_ACCENT_HOVER":   "#4f5bbf",
        "COLOR_TEXT_PRIMARY":   "#f1f5f9",
        "COLOR_TEXT_MUTED":     "#64748b",
        "COLOR_TEXT_DIM":       "#94a3b8",
        "COLOR_SUCCESS":        "#10b981",
        "COLOR_SUCCESS_HOVER":  "#059669",
        "COLOR_DANGER":         "#f43f5e",
        "COLOR_DANGER_HOVER":   "#e11d48",
        "COLOR_XML_TEXT":       "#cbd5e1",
        "COLOR_XML_TAG":        "#f43f5e",
        "COLOR_XML_ATTR":       "#fb923c",
        "COLOR_XML_VALUE":      "#10b981",
        "COLOR_XML_BRACKET":    "#64748b",
        "COLOR_XML_COMMENT":    "#94a3b8",
        "COLOR_XML_CDATA":      "#c084fc",
        "COLOR_SEVERITY_HIGH":  "#f43f5e",
        "COLOR_SEVERITY_MED":   "#f59e0b",
        "COLOR_SEVERITY_LOW":   "#10b981",
    },
    "light": {
        "COLOR_BG_DARK":        "#fbfbfd",
        "COLOR_BG_MAIN":        "#f4f5f8",
        "COLOR_BG_CARD":        "#e9ebf1",
        "COLOR_BG_INPUT":       "#ffffff",
        "COLOR_BG_HOVER":       "#e1e4ec",
        "COLOR_BORDER":         "#cdd2dc",
        "COLOR_ACCENT":         "#4f5bd5",
        "COLOR_ACCENT_HOVER":   "#3f4ac0",
        "COLOR_TEXT_PRIMARY":   "#141824",
        "COLOR_TEXT_MUTED":     "#5a6172",
        "COLOR_TEXT_DIM":       "#3d4454",
        "COLOR_SUCCESS":        "#059669",
        "COLOR_SUCCESS_HOVER":  "#047857",
        "COLOR_DANGER":         "#e11d48",
        "COLOR_DANGER_HOVER":   "#be123c",
        "COLOR_XML_TEXT":       "#1e2030",
        "COLOR_XML_TAG":        "#991b1b",
        "COLOR_XML_ATTR":       "#9a3412",
        "COLOR_XML_VALUE":      "#065f46",
        "COLOR_XML_BRACKET":    "#374151",
        "COLOR_XML_COMMENT":    "#4b5563",
        "COLOR_XML_CDATA":      "#5b21b6",
        "COLOR_SEVERITY_HIGH":  "#e11d48",
        "COLOR_SEVERITY_MED":   "#d97706",
        "COLOR_SEVERITY_LOW":   "#059669",
    },
}

def _apply_theme(name):
    g = globals()
    for k, v in THEMES[name].items():
        g[k] = v

# Start in dark mode
_apply_theme("dark")
COLOR_BG_DARK = COLOR_BG_DARK  # satisfy linters — all names now exist as globals
COLOR_BG_MAIN = COLOR_BG_MAIN
COLOR_BG_CARD = COLOR_BG_CARD
COLOR_BG_INPUT = COLOR_BG_INPUT
COLOR_BG_HOVER = COLOR_BG_HOVER
COLOR_BORDER = COLOR_BORDER
COLOR_ACCENT = COLOR_ACCENT
COLOR_ACCENT_HOVER = COLOR_ACCENT_HOVER
COLOR_TEXT_PRIMARY = COLOR_TEXT_PRIMARY
COLOR_TEXT_MUTED = COLOR_TEXT_MUTED
COLOR_TEXT_DIM = COLOR_TEXT_DIM
COLOR_SUCCESS = COLOR_SUCCESS
COLOR_SUCCESS_HOVER = COLOR_SUCCESS_HOVER
COLOR_DANGER = COLOR_DANGER
COLOR_DANGER_HOVER = COLOR_DANGER_HOVER
COLOR_XML_TEXT    = COLOR_XML_TEXT
COLOR_XML_TAG     = COLOR_XML_TAG
COLOR_XML_ATTR    = COLOR_XML_ATTR
COLOR_XML_VALUE   = COLOR_XML_VALUE
COLOR_XML_BRACKET = COLOR_XML_BRACKET
COLOR_XML_COMMENT = COLOR_XML_COMMENT
COLOR_XML_CDATA   = COLOR_XML_CDATA
COLOR_SEVERITY_HIGH = COLOR_SEVERITY_HIGH
COLOR_SEVERITY_MED = COLOR_SEVERITY_MED
COLOR_SEVERITY_LOW = COLOR_SEVERITY_LOW

# System font fallback
FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica Neue"


def _make_unique_id(base_id, existing_ids):
    """Return a copy ID that doesn't collide with existing_ids. Strips any prior _copy/_copy_N suffix first."""
    base = re.sub(r'_copy(?:_\d+)?$', '', base_id)
    candidate = f"{base}_copy"
    n = 2
    while candidate in existing_ids:
        candidate = f"{base}_copy_{n}"
        n += 1
    return candidate


def _bind_tree(widget, event, handler):
    """Recursively bind an event handler to a widget and all its tk descendants."""
    try:
        widget.bind(event, handler)
    except Exception:
        pass
    for child in widget.winfo_children():
        _bind_tree(child, event, handler)

class FormField(ctk.CTkFrame):
    """A standard labelled form field supporting single line or multi-line text input with custom themes."""
    def __init__(self, master, label_text, is_multiline=False, height=42, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.base_height = height
        self.is_multiline = is_multiline

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_MUTED
        )
        self.label.pack(anchor="w", padx=5, pady=(6, 2))

        if is_multiline:
            self.entry = ctk.CTkTextbox(
                self,
                height=height,
                border_width=1,
                border_color=COLOR_BORDER,
                fg_color=COLOR_BG_INPUT,
                text_color=COLOR_TEXT_PRIMARY,
                font=(FONT_FAMILY, 13),
                wrap="word",
                corner_radius=6
            )
        else:
            self.entry = ctk.CTkEntry(
                self,
                height=height,
                border_width=1,
                border_color=COLOR_BORDER,
                fg_color=COLOR_BG_INPUT,
                text_color=COLOR_TEXT_PRIMARY,
                font=(FONT_FAMILY, 13),
                corner_radius=6
            )

        self.entry.pack(fill="x", padx=5, pady=(0, 4))

    def get(self):
        if self.is_multiline:
            return self.entry.get("1.0", "end-1c")
        return self.entry.get()

    def set_value(self, val):
        if self.is_multiline:
            self.entry.delete("1.0", "end")
            self.entry.insert("1.0", val or "")
        else:
            self.entry.delete(0, "end")
            self.entry.insert(0, val or "")


class FormDropdown(ctk.CTkFrame):
    """A standard labelled form dropdown with custom themes, backed by CTkComboBox (readonly)."""
    def __init__(self, master, label_text, options, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._dropdown_options = options

        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=(FONT_FAMILY, 10, "bold"),
            text_color=COLOR_TEXT_MUTED,
        )
        self.label.pack(anchor="w", padx=5, pady=(6, 2))

        self.entry = ctk.CTkComboBox(
            self,
            values=options,
            height=38,
            fg_color=COLOR_BG_INPUT,
            button_color=COLOR_BORDER,
            button_hover_color=COLOR_BG_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 13),
            corner_radius=6,
            border_color=COLOR_BORDER,
            border_width=1,
            state="readonly",
        )
        self.entry.set(options[0] if options else "")
        self.entry.pack(fill="x", padx=5, pady=(0, 4))

    def get(self):
        return self.entry.get()

    def set_value(self, val):
        self.entry.set(val if val in self._dropdown_options else (self._dropdown_options[0] if self._dropdown_options else ""))


class FormRow(ctk.CTkFrame):
    """Horizontal container to host multiple side-by-side FormFields."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="x", pady=4)


class STIGApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STIG Authoring Pro")
        
        # Maximize the window size by default
        self.geometry("1400x950")
        self.resizable(True, True)
        
        # State variables
        self.benchmark = STIGBenchmark()
        self.active_rule_index = None
        self.rule_buttons = []
        self.custom_field_widgets = []
        self.current_theme = "dark"
        self._check_id = None
        self._last_saved_xml = ""   # tracks what was last exported / the initial state

        # Zoom scale factor (starts at 1.0 / 100%)
        self.zoom_scale = 1.0
        # Dedicated XML Preview font size (starts at 13pt)
        self.xml_font_size = 13
        self._last_paned_width = 0
        self._sash_after_id = None

        # Configure root window
        self.configure(fg_color=COLOR_BG_MAIN)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # PanedWindow — gives draggable sashes between the three panels
        self.paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL,
            sashwidth=5, sashpad=0,
            bg=COLOR_BORDER, relief="flat", bd=0
        )
        self.paned.grid(row=0, column=0, sticky="nsew")

        self.sidebar_pane = tk.Frame(self.paned, bg=COLOR_BG_CARD)
        self.editor_pane  = tk.Frame(self.paned, bg=COLOR_BG_MAIN)
        self.preview_pane = tk.Frame(self.paned, bg=COLOR_BG_MAIN)

        self.paned.add(self.sidebar_pane, minsize=200, width=310)
        self.paned.add(self.editor_pane,  minsize=350, width=700)
        self.paned.add(self.preview_pane, minsize=200)

        # Build panel contents
        self.create_sidebar()
        self.create_editor_panel()
        self.create_preview_panel()

        # Set 20/50/30 sash positions after the window is actually rendered
        self.after(100, self._set_initial_sashes)
        self.paned.bind("<Configure>", self._on_paned_configure)
        
        # Load starting default blank STIG
        default_bench = STIGBenchmark({
            "benchmark_id": DEFAULT_BENCHMARK_ID,
            "title": "New STIG Benchmark",
            "description": "",
            "version": "1",
            "release_info": date.today().isoformat(),
            "publisher": "draft",
            "rules": [{
                "group_id": "",
                "group_title": "",
                "group_description": "",
                "rule_id": "",
                "severity": "medium",
                "title": "",
                "vuln_discussion": "",
                "nist_control": "",
                "cci": "",
                "rationale": "",
                "manual_check": "",
                "fix_text": ""
            }]
        })
        self.load_benchmark(default_bench)
        # Treat the startup state as "already saved" so closing immediately never warns
        self._last_saved_xml = generate_benchmark_xml(self.benchmark)

        # Wire up close-window handler before starting the daemon
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Auto-update background daemon
        self.check_for_changes()

        # Offer autosave recovery after the window is fully visible
        self.after(600, self._restore_autosave_if_exists)
        
        # Bind global mouse wheel event listener (scrolls whatever container is under cursor)
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", self._on_global_mousewheel)
        self.bind_all("<Button-5>", self._on_global_mousewheel)
        
        # Bind global Zoom Shortcuts (Ctrl +, Ctrl -, Ctrl 0)
        self.bind_all("<Control-equal>", self.zoom_in)
        self.bind_all("<Control-plus>", self.zoom_in)
        self.bind_all("<Control-minus>", self.zoom_out)
        self.bind_all("<Control-0>", self.zoom_reset)
        
        # Bind Ctrl+A to select all text in the focused widget
        self.bind_all("<Control-a>", self._select_all)
        self.bind_all("<Control-A>", self._select_all)
        
        # Attempt window maximization based on platform support
        self.after(50, self.maximize_window)

    def maximize_window(self):
        """Helper to maximize the window at start across platforms."""
        try:
            self.attributes("-zoomed", True)
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                pass

    def _on_global_mousewheel(self, event):
        """Scrolls the appropriate parent container when scroll wheel triggers over any element."""
        x, y = self.winfo_pointerxy()
        try:
            widget = self.winfo_containing(x, y)
        except Exception:
            return  # pointer is over a native dialog not in tkinter's widget tree
        if not widget:
            return

        # Use bounding box to find which scrollable frame the pointer is over.
        # Tree-walking misses the target because CTkScrollableFrame children are
        # actually parented to the internal _scrollable_frame, not the outer frame.
        canvas_to_scroll = None
        for frame in (self.rule_scroll, self.rule_list_frame):
            try:
                fx, fy = frame.winfo_rootx(), frame.winfo_rooty()
                fw, fh = frame.winfo_width(), frame.winfo_height()
                if fx <= x <= fx + fw and fy <= y <= fy + fh:
                    canvas_to_scroll = frame._parent_canvas
                    break
            except Exception:
                continue

        if canvas_to_scroll is None:
            return

        if event.num == 4:
            canvas_to_scroll.yview_scroll(-2, "units")
        elif event.num == 5:
            canvas_to_scroll.yview_scroll(2, "units")
        elif event.delta:
            scroll_amount = int(-1 * (event.delta / 60))
            if scroll_amount == 0:
                scroll_amount = -1 if event.delta > 0 else 1
            canvas_to_scroll.yview_scroll(scroll_amount, "units")

    # --- Zoom Controls ---

    def zoom_in(self, event=None):
        self.zoom_scale = min(2.5, self.zoom_scale + 0.1)
        self.apply_zoom()

    def zoom_out(self, event=None):
        self.zoom_scale = max(0.6, self.zoom_scale - 0.1)
        self.apply_zoom()

    def zoom_reset(self, event=None):
        self.zoom_scale = 1.0
        self.apply_zoom()

    def zoom_xml_in(self):
        """Specifically scales up the XML code preview font size."""
        self.xml_font_size = min(30, self.xml_font_size + 1)
        self.apply_xml_zoom()

    def zoom_xml_out(self):
        """Specifically scales down the XML code preview font size."""
        self.xml_font_size = max(8, self.xml_font_size - 1)
        self.apply_xml_zoom()

    def _set_initial_sashes(self):
        """Position pane sashes for a 20 / 50 / 30 split."""
        w = self.paned.winfo_width()
        if w < 10:
            self.after(50, self._set_initial_sashes)
            return
        self._apply_sash_proportions(w)
        self.apply_xml_zoom()

    def _apply_sash_proportions(self, w):
        """Place sashes at 20/50/30 for the given paned width."""
        self.paned.sash_place(0, int(w * 0.20), 0)
        self.paned.sash_place(1, int(w * 0.70), 0)

    def _on_paned_configure(self, event=None):
        """Re-applies 20/50/30 sash split when the window is resized."""
        w = self.paned.winfo_width()
        if w < 10 or w == self._last_paned_width:
            return
        self._last_paned_width = w
        # Defer sash placement so tkinter finishes its own layout pass first
        if self._sash_after_id is not None:
            self.after_cancel(self._sash_after_id)
        self._sash_after_id = self.after(20, lambda: self._apply_sash_proportions(w))

    def toggle_theme(self):
        """Switches between dark and light themes by rebuilding the UI with new colors."""
        self.save_active_rule_details()
        saved_benchmark = self.benchmark
        saved_index = self.active_rule_index
        saved_zoom = self.zoom_scale

        self.current_theme = "light" if self.current_theme == "dark" else "dark"

        # Cancel both timers before touching any widgets
        if self._check_id is not None:
            self.after_cancel(self._check_id)
            self._check_id = None
        if self._sash_after_id is not None:
            self.after_cancel(self._sash_after_id)
            self._sash_after_id = None

        # Update color constants BEFORE destroying so the new values are
        # ready when we recreate widgets. We deliberately do NOT call
        # ctk.set_appearance_mode() — it schedules internal after() callbacks
        # that fire after the destroy and crash on the stale Tcl commands.
        # Every widget in this app uses explicit hex colors, so CTK's
        # internal appearance mode is not needed for visual correctness.
        _apply_theme(self.current_theme)

        # Update root window and sash color. The three pane tk.Frames
        # (sidebar_pane / editor_pane / preview_pane) are fully covered by their
        # CTkFrame children (pack fill="both" expand=True), so their bg never
        # shows — no need to configure them here. More importantly, calling
        # pane.configure(bg=...) would walk CTK's chained monkey-patch and crash
        # on the already-destroyed CTkFrame from the previous toggle.
        self.configure(fg_color=COLOR_BG_MAIN)
        self.paned.configure(bg=COLOR_BORDER)

        # Destroy old panels
        self.sidebar.destroy()
        self.editor_frame.destroy()
        self.preview_frame.destroy()
        self.rule_buttons = []
        self.custom_field_widgets = []

        # Rebuild with new colors
        self.create_sidebar()
        self.create_editor_panel()
        self.create_preview_panel()

        # Restore event bindings (destroyed with the old widgets)
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", self._on_global_mousewheel)
        self.bind_all("<Button-5>", self._on_global_mousewheel)
        self.bind_all("<Control-equal>", self.zoom_in)
        self.bind_all("<Control-plus>", self.zoom_in)
        self.bind_all("<Control-minus>", self.zoom_out)
        self.bind_all("<Control-0>", self.zoom_reset)
        self.bind_all("<Control-a>", self._select_all)
        self.bind_all("<Control-A>", self._select_all)

        # Restore state — set benchmark/index directly instead of going through
        # load_benchmark (which would set index=0, render, then we'd override it,
        # causing a double-render with the wrong active rule on the first pass).
        self.benchmark = saved_benchmark
        self.active_rule_index = saved_index
        self.zoom_scale = saved_zoom
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()
        self.apply_zoom()

        # Reset paned width so the Configure handler can re-fire and reapply sashes
        self._last_paned_width = 0
        self.after(100, self._set_initial_sashes)

        # Restart the auto-save timer (was cancelled above)
        self.check_for_changes()

    def apply_xml_zoom(self):
        """Applies zoom to the XML preview textbox font."""
        size = max(8, int(self.xml_font_size * self.zoom_scale))
        font_code = ("Consolas", size) if os.name == "nt" else ("Courier", size)
        self.preview_textbox.configure(font=font_code)

    def apply_zoom(self):
        """Dynamically scales all UI element dimensions, height offsets, and font sizes based on current zoom_scale."""
        scale = self.zoom_scale
        
        # Calculate scaled fonts
        font_title = (FONT_FAMILY, int(24 * scale), "bold")
        font_subtitle = (FONT_FAMILY, int(12 * scale))
        font_label = (FONT_FAMILY, int(12 * scale), "bold")
        font_input = (FONT_FAMILY, int(13 * scale))
        font_btn_bold = (FONT_FAMILY, int(13 * scale), "bold")
        
        # Reconfigure header labels
        self.title_lbl.configure(font=(FONT_FAMILY, int(15 * scale), "bold"))
        self.subtitle_lbl.configure(font=(FONT_FAMILY, int(15 * scale), "bold"))
        self.rule_editor_label.configure(font=(FONT_FAMILY, int(18 * scale), "bold"))
        self.preview_lbl.configure(font=(FONT_FAMILY, int(18 * scale), "bold"))

        # Search
        self.search_entry.configure(font=font_input, height=int(34 * scale))

        # Preview console
        self.refresh_btn.configure(font=(FONT_FAMILY, int(11 * scale), "bold"), height=int(28 * scale), width=int(90 * scale))
        self.apply_xml_zoom()

        # Sidebar action buttons
        for btn in (self.add_btn, self.import_btn, self.export_btn):
            btn.configure(font=font_input, height=int(32 * scale))
        for btn in (self.dup_btn, self.del_btn, self.bench_info_btn,
                    self.move_up_btn, self.move_down_btn):
            btn.configure(font=(FONT_FAMILY, int(11 * scale)), height=int(28 * scale))
        
        # Rebuild rule navigation buttons
        self.update_sidebar_rule_list()
        
        # Reconfigure Rule Editor Inputs
        for field in self.rule_fields.values():
            field.label.configure(font=font_label)
            if field.is_multiline:
                field.entry.configure(font=font_input, height=int(field.base_height * scale))
            else:
                field.entry.configure(font=font_input, height=int(42 * scale))

        self.severity_field.label.configure(font=font_label)
        self.severity_field.entry.configure(font=font_input, dropdown_font=font_input, height=int(42 * scale))

        # Reconfigure Custom Section Header
        self.custom_label.configure(font=(FONT_FAMILY, int(12 * scale), "bold"))
        self.add_custom_btn.configure(font=(FONT_FAMILY, int(11 * scale), "bold"), height=int(28 * scale), width=int(110 * scale))
        
        # Reconfigure Custom Field Rows
        for key_entry, val_entry, _ in self.custom_field_widgets:
            key_entry.configure(font=(FONT_FAMILY, int(12 * scale)), height=int(36 * scale))
            val_entry.configure(font=(FONT_FAMILY, int(12 * scale)), height=int(36 * scale))

    # --- UI Layout Design ---

    def create_sidebar(self):
        """Creates the navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self.sidebar_pane, corner_radius=0,
                                    fg_color=COLOR_BG_CARD, border_width=0)
        self.sidebar.pack(fill="both", expand=True)
        self.sidebar.grid_rowconfigure(3, weight=1)  # rule list expands
        self.sidebar.grid_columnconfigure(0, weight=1)

        # --- Row 0: Header ---
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=18, pady=(22, 10), sticky="ew")

        self.title_lbl = ctk.CTkLabel(
            self.logo_frame, text="STIG Authoring",
            font=(FONT_FAMILY, 15, "bold"), text_color=COLOR_TEXT_PRIMARY
        )
        self.title_lbl.pack(side="left")

        self.subtitle_lbl = ctk.CTkLabel(
            self.logo_frame, text="Pro",
            font=(FONT_FAMILY, 15, "bold"), text_color=COLOR_ACCENT
        )
        self.subtitle_lbl.pack(side="left", padx=(3, 0))

        theme_icon = "☀" if self.current_theme == "dark" else "☾"
        self.theme_btn = ctk.CTkButton(
            self.logo_frame, text=theme_icon, width=28, height=28,
            fg_color="transparent", hover_color=COLOR_BG_HOVER,
            text_color=COLOR_TEXT_DIM, font=(FONT_FAMILY, 14),
            corner_radius=6, command=self.toggle_theme
        )
        self.theme_btn.pack(side="right")

        # --- Row 1: Search ---
        # No textvariable: CTkEntry never shows placeholder_text when one is set.
        self.search_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="Search rules...",
            height=34, font=(FONT_FAMILY, 12),
            border_color=COLOR_BORDER, fg_color=COLOR_BG_INPUT,
            text_color=COLOR_TEXT_PRIMARY, corner_radius=6
        )
        self.search_entry.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        # --- Row 2: Divider ---
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLOR_BORDER).grid(
            row=2, column=0, sticky="ew", padx=0, pady=0
        )

        # --- Row 3: Scrollable rule list (expands to fill) ---
        self.rule_list_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_TEXT_DIM
        )
        self.rule_list_frame.grid(row=3, column=0, padx=0, pady=0, sticky="nsew")

        # --- Row 4: Divider ---
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLOR_BORDER).grid(
            row=4, column=0, sticky="ew", padx=0, pady=0
        )

        # --- Row 5: Bottom action buttons (full-width vertical stack) ---
        self.action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=12, pady=12, sticky="ew")

        self.add_btn = ctk.CTkButton(
            self.action_frame, text="+ New Rule",
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            height=34, font=(FONT_FAMILY, 12, "bold"),
            text_color="#ffffff", corner_radius=6, command=self.add_rule
        )
        self.add_btn.pack(fill="x", pady=(0, 6))

        self.dup_btn = ctk.CTkButton(
            self.action_frame, text="Duplicate Rule",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.duplicate_rule
        )
        self.dup_btn.pack(fill="x", pady=(0, 5))

        # Move Up / Move Down — side-by-side row
        move_row = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        move_row.pack(fill="x", pady=(0, 5))
        self.move_up_btn = ctk.CTkButton(
            move_row, text="▲  Up",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.move_rule_up
        )
        self.move_up_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self.move_down_btn = ctk.CTkButton(
            move_row, text="▼  Down",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.move_rule_down
        )
        self.move_down_btn.pack(side="left", expand=True, fill="x")

        self.del_btn = ctk.CTkButton(
            self.action_frame, text="Delete Rule",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_DANGER, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.delete_rule
        )
        self.del_btn.pack(fill="x", pady=(0, 8))

        # Thin divider before document-level actions
        ctk.CTkFrame(self.action_frame, height=1, fg_color=COLOR_BORDER).pack(fill="x", pady=(0, 8))

        self.bench_info_btn = ctk.CTkButton(
            self.action_frame, text="Benchmark Info",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.open_benchmark_info
        )
        self.bench_info_btn.pack(fill="x", pady=(0, 5))

        self.import_btn = ctk.CTkButton(
            self.action_frame, text="Import XML",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.import_xml
        )
        self.import_btn.pack(fill="x", pady=(0, 5))

        self.export_btn = ctk.CTkButton(
            self.action_frame, text="Export XML",
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            height=30, font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_DIM, corner_radius=6,
            border_width=1, border_color=COLOR_BORDER,
            command=self.export_xml
        )
        self.export_btn.pack(fill="x")

    def create_editor_panel(self):
        """Creates the center form editor."""
        self.editor_frame = ctk.CTkFrame(self.editor_pane, fg_color=COLOR_BG_MAIN)
        self.editor_frame.pack(fill="both", expand=True)
        self.editor_frame.grid_rowconfigure(1, weight=1)
        self.editor_frame.grid_columnconfigure(0, weight=1)
        
        # Row 0: Rule Title Header
        self.rule_editor_label = ctk.CTkLabel(
            self.editor_frame,
            text="(New Rule)",
            font=(FONT_FAMILY, 18, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.rule_editor_label.grid(row=0, column=0, padx=8, pady=(22, 8), sticky="w")
        
        # Row 1: Scrollable editor (no tabview — single pane)
        self.rule_scroll = ctk.CTkScrollableFrame(
            self.editor_frame,
            fg_color="transparent",
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_TEXT_DIM
        )
        self.rule_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 15))
        
        self.rule_fields = {}

        def section_header(text):
            f = ctk.CTkFrame(self.rule_scroll, fg_color="transparent")
            f.pack(fill="x", padx=8, pady=(18, 2))
            ctk.CTkLabel(f, text=text, font=(FONT_FAMILY, 10, "bold"),
                         text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkFrame(f, height=1, fg_color=COLOR_BORDER).pack(
                side="left", fill="x", expand=True, padx=(8, 0))

        # — Identifiers —
        section_header("IDENTIFIERS")
        row1 = FormRow(self.rule_scroll)
        self.rule_fields["group_id"] = FormField(row1, "Group ID")
        self.rule_fields["group_id"].pack(side="left", expand=True, fill="x", padx=5)
        self.rule_fields["rule_id"] = FormField(row1, "Rule ID")
        self.rule_fields["rule_id"].pack(side="left", expand=True, fill="x", padx=5)
        self.rule_fields["stig_id"] = FormField(row1, "STIG ID (Rule Version)")
        self.rule_fields["stig_id"].pack(side="left", expand=True, fill="x", padx=5)

        row1b = FormRow(self.rule_scroll)
        self.rule_fields["group_title"] = FormField(row1b, "Group Title")
        self.rule_fields["group_title"].pack(side="left", expand=True, fill="x", padx=5)
        self.rule_fields["title"] = FormField(row1b, "Rule Title")
        self.rule_fields["title"].pack(side="left", expand=True, fill="x", padx=5)

        # — Compliance —
        section_header("COMPLIANCE")
        row2 = FormRow(self.rule_scroll)
        self.severity_field = FormDropdown(row2, "Severity", options=["low", "medium", "high"])
        self.severity_field.pack(side="left", expand=True, fill="x", padx=5)
        self.rule_fields["nist_control"] = FormField(row2, "NIST Controls (one per line)", is_multiline=True, height=60)
        self.rule_fields["nist_control"].pack(side="left", expand=True, fill="x", padx=5)
        self.rule_fields["cci"] = FormField(row2, "CCI IDs (one per line)", is_multiline=True, height=60)
        self.rule_fields["cci"].pack(side="left", expand=True, fill="x", padx=5)

        # — Description —
        section_header("DESCRIPTION")
        row3 = FormRow(self.rule_scroll)
        self.rule_fields["group_description"] = FormField(row3, "Group Description", is_multiline=True, height=60)
        self.rule_fields["group_description"].pack(fill="x", expand=True, padx=5)

        row4 = FormRow(self.rule_scroll)
        self.rule_fields["vuln_discussion"] = FormField(row4, "Vulnerability Discussion", is_multiline=True, height=130)
        self.rule_fields["vuln_discussion"].pack(fill="x", expand=True, padx=5)

        row5 = FormRow(self.rule_scroll)
        self.rule_fields["rationale"] = FormField(row5, "Rationale", is_multiline=True, height=85)
        self.rule_fields["rationale"].pack(fill="x", expand=True, padx=5)

        # — Audit & Fix —
        section_header("AUDIT & FIX")
        row6 = FormRow(self.rule_scroll)
        self.rule_fields["manual_check"] = FormField(row6, "Check Content", is_multiline=True, height=140)
        self.rule_fields["manual_check"].pack(fill="x", expand=True, padx=5)

        row7 = FormRow(self.rule_scroll)
        self.rule_fields["fix_text"] = FormField(row7, "Fix Text", is_multiline=True, height=140)
        self.rule_fields["fix_text"].pack(fill="x", expand=True, padx=5)

        # — Custom Attributes —
        section_header("CUSTOM ATTRIBUTES")
        self.custom_section = ctk.CTkFrame(self.rule_scroll, fg_color=COLOR_BG_INPUT,
                                           corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.custom_section.pack(fill="x", pady=(4, 20), padx=5)

        self.custom_header_frame = ctk.CTkFrame(self.custom_section, fg_color="transparent")
        self.custom_header_frame.pack(fill="x", padx=12, pady=8)

        self.custom_label = ctk.CTkLabel(
            self.custom_header_frame, text="Key / Value Pairs",
            font=(FONT_FAMILY, 11, "bold"), text_color=COLOR_TEXT_DIM
        )
        self.custom_label.pack(side="left")

        self.add_custom_btn = ctk.CTkButton(
            self.custom_header_frame, text="+ Add",
            width=70, height=24,
            fg_color=COLOR_BG_CARD, hover_color=COLOR_BG_HOVER,
            font=(FONT_FAMILY, 11), text_color=COLOR_ACCENT,
            corner_radius=5, border_width=1, border_color=COLOR_BORDER,
            command=self.add_blank_custom_field
        )
        self.add_custom_btn.pack(side="right")

        self.custom_fields_container = ctk.CTkFrame(self.custom_section, fg_color="transparent")
        self.custom_fields_container.pack(fill="x", padx=12, pady=(0, 10))
        

    def create_preview_panel(self):
        """Creates the live XML preview console."""
        self.preview_frame = ctk.CTkFrame(self.preview_pane, fg_color=COLOR_BG_MAIN)
        self.preview_frame.pack(fill="both", expand=True)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        # Row 0: Large Header
        self.preview_header_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self.preview_header_frame.grid(row=0, column=0, padx=5, pady=(20, 10), sticky="ew")
        
        self.preview_lbl = ctk.CTkLabel(
            self.preview_header_frame,
            text="XML Preview",
            font=(FONT_FAMILY, 18, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.preview_lbl.pack(side="left")

        # Zoom Controls
        self.zoom_ctrl_frame = ctk.CTkFrame(self.preview_header_frame, fg_color="transparent")
        self.zoom_ctrl_frame.pack(side="right", padx=(10, 0))

        for text, cmd in (("-", self.zoom_xml_out), ("+", self.zoom_xml_in)):
            ctk.CTkButton(
                self.zoom_ctrl_frame, text=text, width=26, height=26,
                fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
                text_color=COLOR_TEXT_DIM, font=(FONT_FAMILY, 13, "bold"),
                corner_radius=5, border_width=1, border_color=COLOR_BORDER,
                command=cmd
            ).pack(side="left", padx=2)

        self.xml_minus_btn = self.zoom_ctrl_frame.winfo_children()[0]
        self.xml_plus_btn  = self.zoom_ctrl_frame.winfo_children()[1]

        self.refresh_btn = ctk.CTkButton(
            self.preview_header_frame, text="Sync",
            width=60, height=26,
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            text_color=COLOR_TEXT_DIM, font=(FONT_FAMILY, 11),
            border_width=1, border_color=COLOR_BORDER, corner_radius=5,
            command=self.on_manual_refresh
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))
        
        # Row 1: Monospace XML display text console
        self.preview_textbox = ctk.CTkTextbox(
            self.preview_frame, 
            border_width=1, 
            border_color=COLOR_BORDER, 
            fg_color=COLOR_BG_DARK, 
            font=("Consolas", 12) if os.name == "nt" else ("Courier", 12),
            text_color=COLOR_XML_TEXT,
            wrap="none",
            corner_radius=8
        )
        self.preview_textbox.grid(row=1, column=0, padx=5, pady=(0, 15), sticky="nsew")
        self.preview_textbox.configure(state="disabled")

        # Config color tags for XML syntax highlighting — colors are theme-aware globals
        self.preview_textbox.tag_config("xml_bracket", foreground=COLOR_XML_BRACKET)
        self.preview_textbox.tag_config("xml_tag",     foreground=COLOR_XML_TAG)
        self.preview_textbox.tag_config("xml_attr",    foreground=COLOR_XML_ATTR)
        self.preview_textbox.tag_config("xml_value",   foreground=COLOR_XML_VALUE)
        self.preview_textbox.tag_config("xml_comment", foreground=COLOR_XML_COMMENT)
        self.preview_textbox.tag_config("xml_cdata",   foreground=COLOR_XML_CDATA)

    # --- Controller Logic ---

    def load_benchmark(self, benchmark):
        """Loads a STIGBenchmark object completely and populates the UI fields."""
        self.benchmark = benchmark

        # Select the first rule with actual content; fall back to index 0
        if benchmark.rules:
            self.active_rule_index = next(
                (i for i, r in enumerate(benchmark.rules)
                 if r.title.strip() or r.group_title.strip()),
                0
            )
        else:
            self.active_rule_index = None
            
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()

    def update_sidebar_rule_list(self):
        """Clears and rebuilds the rule navigation buttons in the sidebar."""
        for card in self.rule_buttons:
            card.destroy()
        self.rule_buttons.clear()

        search_text = self.search_entry.get().strip().lower()
        id_font    = (FONT_FAMILY, int(11 * self.zoom_scale), "bold")
        title_font = (FONT_FAMILY, int(11 * self.zoom_scale))
        sev_font   = (FONT_FAMILY, int(9  * self.zoom_scale), "bold")

        SEV_COLOR = {"high": COLOR_SEVERITY_HIGH, "medium": COLOR_SEVERITY_MED, "low": COLOR_SEVERITY_LOW}

        for idx, rule in enumerate(self.benchmark.rules):
            if search_text:
                if not (search_text in rule.rule_id.lower() or
                        search_text in rule.title.lower() or
                        search_text in rule.group_id.lower() or
                        search_text in rule.stig_id.lower()):
                    continue

            is_active  = (idx == self.active_rule_index)
            card_color = COLOR_BG_MAIN if is_active else "transparent"
            border_c   = COLOR_ACCENT  if is_active else COLOR_BG_CARD

            card = ctk.CTkFrame(
                self.rule_list_frame,
                fg_color=card_color, corner_radius=7,
                border_width=1, border_color=border_c
            )
            card.pack(fill="x", padx=8, pady=3)
            card.associated_index = idx

            # Top row: ID pill + severity badge
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(8, 2))

            # The STIG ID (e.g. EXOS-00-000100) is what reviewers refer to a rule by;
            # fall back to the long XCCDF IDs only when it is blank.
            # (Export writes the benchmark version into a blank STIG ID, so skip that.)
            stig_id = rule.stig_id if rule.stig_id != self.benchmark.version else ""
            id_str = stig_id or rule.rule_id or rule.group_id or "New Rule"
            ctk.CTkLabel(top, text=id_str, font=id_font,
                         text_color=COLOR_ACCENT if is_active else COLOR_TEXT_DIM,
                         anchor="w").pack(side="left")

            sev = (rule.severity or "medium").lower()
            sev_color = SEV_COLOR.get(sev, COLOR_SEVERITY_MED)
            ctk.CTkLabel(top, text=sev.upper(), font=sev_font,
                         text_color=sev_color, anchor="e").pack(side="right")

            # Title line
            title_str = rule.title or "(No Title)"
            if len(title_str) > 64:
                title_str = title_str[:64].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
            ctk.CTkLabel(card, text=title_str, font=title_font,
                         text_color=COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_MUTED,
                         anchor="w", wraplength=220, justify="left").pack(
                fill="x", padx=10, pady=(0, 8))

            # Bind click recursively to every tk descendant so clicks on label
            # text (which lands on CTkLabel's internal tk.Label) still register.
            _bind_tree(card, "<Button-1>", lambda e, i=idx: self.select_rule(i))
            _bind_tree(card, "<Enter>", lambda e, c=card, a=is_active: c.configure(
                fg_color=COLOR_BG_MAIN if not a else COLOR_BG_MAIN))
            _bind_tree(card, "<Leave>", lambda e, c=card, a=is_active: c.configure(
                fg_color=COLOR_BG_MAIN if a else "transparent"))

            self.rule_buttons.append(card)

        # Empty-state feedback when search yields nothing
        if search_text and not self.rule_buttons:
            no_result_lbl = ctk.CTkLabel(
                self.rule_list_frame,
                text="No rules match your search.",
                font=(FONT_FAMILY, 11), text_color=COLOR_TEXT_MUTED,
                anchor="center"
            )
            no_result_lbl.pack(pady=24)
            self.rule_buttons.append(no_result_lbl)

    def select_rule(self, index):
        """Saves current rule fields, changes selection, and loads new rule fields."""
        if self.active_rule_index == index:
            return
        
        self.save_active_rule_details()
        self.active_rule_index = index
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()

    def load_active_rule_details(self):
        """Fills Rule Editor fields with current values of the active STIGRule."""
        if self.active_rule_index is None or not (0 <= self.active_rule_index < len(self.benchmark.rules)):
            for field in self.rule_fields.values():
                field.set_value("")
            self.severity_field.set_value("medium")
            for _, _, frame in self.custom_field_widgets:
                frame.destroy()
            self.custom_field_widgets.clear()
            self.rule_editor_label.configure(text="No Rule Selected")
            return
            
        rule = self.benchmark.rules[self.active_rule_index]
        
        # Display the rule title as the main editor header, fallback to rule ID if title is empty
        title_text = rule.title.strip() or rule.rule_id.strip() or "(New Rule)"
        self.rule_editor_label.configure(text=title_text)
        
        # Set values
        self.rule_fields["group_id"].set_value(rule.group_id)
        self.rule_fields["rule_id"].set_value(rule.rule_id)
        self.rule_fields["stig_id"].set_value(rule.stig_id)
        self.rule_fields["group_title"].set_value(rule.group_title)
        self.rule_fields["group_description"].set_value(rule.group_description)
        self.severity_field.set_value(rule.severity)
        self.rule_fields["title"].set_value(rule.title)
        self.rule_fields["nist_control"].set_value(rule.nist_control)
        self.rule_fields["cci"].set_value(rule.cci)
        self.rule_fields["vuln_discussion"].set_value(rule.vuln_discussion)
        self.rule_fields["rationale"].set_value(rule.rationale)
        self.rule_fields["manual_check"].set_value(rule.manual_check)
        self.rule_fields["fix_text"].set_value(rule.fix_text)
        
        # Load custom fields
        for _, _, frame in self.custom_field_widgets:
            frame.destroy()
        self.custom_field_widgets.clear()
        
        if rule.custom_fields:
            for k, v in rule.custom_fields.items():
                self.add_custom_field_row(k, v)

    def save_active_rule_details(self):
        """Reads input fields from the active tab and writes them to the STIGRule object."""
        if self.active_rule_index is None or not (0 <= self.active_rule_index < len(self.benchmark.rules)):
            return
        try:
            rule = self.benchmark.rules[self.active_rule_index]
            rule.group_id          = self.rule_fields["group_id"].get()
            rule.rule_id           = self.rule_fields["rule_id"].get()
            rule.stig_id           = self.rule_fields["stig_id"].get()
            rule.group_title       = self.rule_fields["group_title"].get()
            rule.group_description = self.rule_fields["group_description"].get()
            rule.severity          = self.severity_field.get()
            rule.title             = self.rule_fields["title"].get()
            rule.nist_control      = self.rule_fields["nist_control"].get()
            rule.cci               = self.rule_fields["cci"].get()
            rule.vuln_discussion   = self.rule_fields["vuln_discussion"].get()
            rule.rationale         = self.rule_fields["rationale"].get()
            rule.manual_check      = self.rule_fields["manual_check"].get()
            rule.fix_text          = self.rule_fields["fix_text"].get()
            custom_fields = {}
            for key_entry, val_entry, _ in self.custom_field_widgets:
                k = key_entry.get().strip()
                v = val_entry.get()
                if k:
                    custom_fields[k] = v
            rule.custom_fields = custom_fields
        except tk.TclError:
            pass  # widgets were destroyed mid-rebuild; skip this save cycle

    # --- Custom Fields Dynamic Rows ---

    def add_blank_custom_field(self):
        self.add_custom_field_row("", "")
        self.update_xml_preview()

    def add_custom_field_row(self, key="", val=""):
        row_frame = ctk.CTkFrame(self.custom_fields_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=4)
        
        input_font = (FONT_FAMILY, int(12 * self.zoom_scale))
        input_height = int(36 * self.zoom_scale)
        
        key_entry = ctk.CTkEntry(
            row_frame, 
            placeholder_text="Key / Name", 
            width=140,
            height=input_height,
            border_color=COLOR_BORDER,
            fg_color=COLOR_BG_INPUT,
            text_color=COLOR_TEXT_PRIMARY,
            font=input_font,
            corner_radius=6
        )
        key_entry.insert(0, key)
        key_entry.pack(side="left", padx=(0, 5))
        
        val_entry = ctk.CTkEntry(
            row_frame, 
            placeholder_text="Value", 
            height=input_height,
            border_color=COLOR_BORDER,
            fg_color=COLOR_BG_INPUT,
            text_color=COLOR_TEXT_PRIMARY,
            font=input_font,
            corner_radius=6
        )
        val_entry.insert(0, val)
        val_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        del_btn = ctk.CTkButton(
            row_frame, 
            text="✖", 
            width=28, 
            height=28,
            fg_color=COLOR_DANGER, 
            hover_color=COLOR_DANGER_HOVER,
            text_color="#ffffff",
            font=(FONT_FAMILY, 11, "bold"),
            corner_radius=6,
            command=lambda rf=row_frame: self.remove_custom_field_row(rf)
        )
        del_btn.pack(side="right")
        
        self.custom_field_widgets.append((key_entry, val_entry, row_frame))

    def remove_custom_field_row(self, row_frame):
        for i, (_, _, r_frame) in enumerate(self.custom_field_widgets):
            if r_frame == row_frame:
                row_frame.destroy()
                self.custom_field_widgets.pop(i)
                break
        self.save_active_rule_details()
        self.update_xml_preview()

    # --- Action Commands ---

    def add_rule(self):
        """Appends a new default blank STIGRule, updates navigation and focuses the new rule."""
        self.save_active_rule_details()
        
        new_rule_data = {
            "group_id": "",
            "group_title": "",
            "group_description": "",
            "rule_id": "",
            "severity": "medium",
            "title": "",
            "vuln_discussion": "",
            "nist_control": "",
            "cci": "",
            "rationale": "",
            "manual_check": "",
            "fix_text": ""
        }
        
        self.benchmark.rules.append(STIGRule(new_rule_data))
        self.active_rule_index = len(self.benchmark.rules) - 1
        
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()

    def duplicate_rule(self):
        """Duplicates the active rule with copied ID tags."""
        if self.active_rule_index is None or not (0 <= self.active_rule_index < len(self.benchmark.rules)):
            messagebox.showwarning("No Selection", "Select a rule to duplicate.")
            return
            
        self.save_active_rule_details()
        
        orig_rule = self.benchmark.rules[self.active_rule_index]
        dup_dict = orig_rule.to_dict()

        existing_group_ids = {r.group_id for r in self.benchmark.rules}
        existing_rule_ids  = {r.rule_id  for r in self.benchmark.rules}
        dup_dict["group_id"] = _make_unique_id(dup_dict["group_id"], existing_group_ids) if dup_dict["group_id"] else ""
        dup_dict["rule_id"]  = _make_unique_id(dup_dict["rule_id"],  existing_rule_ids)  if dup_dict["rule_id"]  else ""
        dup_dict["title"]    = f"{dup_dict['title']} (Copy)"
        
        dup_rule = STIGRule(dup_dict)
        self.benchmark.rules.insert(self.active_rule_index + 1, dup_rule)
        
        self.active_rule_index += 1
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()

    def delete_rule(self):
        """Deletes the active rule."""
        if self.active_rule_index is None or not (0 <= self.active_rule_index < len(self.benchmark.rules)):
            messagebox.showwarning("No Selection", "Select a rule to delete.")
            return
            
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this rule?"):
            return
            
        self.benchmark.rules.pop(self.active_rule_index)
        
        if not self.benchmark.rules:
            self.active_rule_index = None
        else:
            self.active_rule_index = max(0, self.active_rule_index - 1)
            
        self.update_sidebar_rule_list()
        self.load_active_rule_details()
        self.update_xml_preview()

    def import_xml(self):
        """Imports a STIG XML file.
        Full Benchmark files (root = <Benchmark>) replace the entire working document.
        Individual Group/Rule files (root = <Group>) append their rule to the current list.
        """
        file_path = filedialog.askopenfilename(
            title="Import STIG XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            imported = parse_benchmark_xml(file_path)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to parse XML file:\n{str(e)}")
            return

        if not imported.rules:
            messagebox.showwarning("Import", "No rules found in the selected file.")
            return

        self.save_active_rule_details()
        n = len(imported.rules)

        if imported.is_benchmark_file:
            # Full Benchmark file — replace the working document entirely
            self.load_benchmark(imported)
            # Treat the freshly-imported state as "saved" so closing immediately doesn't warn
            self._last_saved_xml = generate_benchmark_xml(self.benchmark)
            messagebox.showinfo(
                "Import Complete",
                f"Loaded {n} rule{'s' if n != 1 else ''} from:\n{imported.title or os.path.basename(file_path)}"
            )
        else:
            # Individual Group/Rule file — append to the current benchmark
            existing_ids = {r.rule_id for r in self.benchmark.rules if r.rule_id}
            conflicts = [r.rule_id for r in imported.rules if r.rule_id in existing_ids]
            if conflicts:
                conflict_list = "\n".join(f"  • {rid}" for rid in conflicts[:10])
                if len(conflicts) > 10:
                    conflict_list += f"\n  … and {len(conflicts) - 10} more"
                if not messagebox.askyesno(
                    "Duplicate Rule IDs",
                    f"The imported file contains rule IDs that already exist:\n{conflict_list}\n\n"
                    "Import anyway? Duplicates will be appended as-is."
                ):
                    return
            first_new_idx = len(self.benchmark.rules)
            self.benchmark.rules.extend(imported.rules)
            self.active_rule_index = first_new_idx
            self.update_sidebar_rule_list()
            self.load_active_rule_details()
            self.update_xml_preview()
            messagebox.showinfo(
                "Import Complete",
                f"Added {n} rule{'s' if n != 1 else ''} from:\n{os.path.basename(file_path)}"
            )

    def export_xml(self):
        """Exports the active STIG Benchmark. Returns True on success, False if cancelled/failed."""
        self.save_active_rule_details()

        # Warn if the benchmark has no rules
        if not self.benchmark.rules:
            if not messagebox.askyesno(
                "Empty Benchmark",
                "This benchmark contains no rules. Export an empty STIG XML anyway?"
            ):
                return False

        # Warn about rules missing required IDs
        blank_id_rules = [
            i + 1 for i, r in enumerate(self.benchmark.rules)
            if not r.rule_id.strip() and not r.group_id.strip()
        ]
        if blank_id_rules:
            nums = ", ".join(str(n) for n in blank_id_rules[:10])
            if len(blank_id_rules) > 10:
                nums += f" … and {len(blank_id_rules) - 10} more"
            if not messagebox.askyesno(
                "Missing Rule IDs",
                f"Rule(s) #{nums} have no Group ID or Rule ID set.\n"
                "Auto-generated IDs will be used for export. Continue?"
            ):
                return False

        # Warn about custom-field rows with blank keys
        if self.active_rule_index is not None:
            blank_key_count = sum(
                1 for k, _, _ in self.custom_field_widgets
                if not k.get().strip()
            )
            if blank_key_count:
                messagebox.showwarning(
                    "Empty Custom Field Keys",
                    f"{blank_key_count} custom attribute row(s) have no key name and will be skipped in the export."
                )

        file_path = filedialog.asksaveasfilename(
            title="Export STIG XML",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            initialfile=f"{self.benchmark.benchmark_id}.xml"
        )
        if not file_path:
            return False

        try:
            xml_content = generate_benchmark_xml(self.benchmark)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
            self._last_saved_xml = xml_content
            self._delete_autosave()
            messagebox.showinfo("Success", f"Successfully exported XML to:\n{file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export XML file:\n{str(e)}")
            return False

    # --- Live Preview Updates ---

    def on_search_changed(self, *args):
        self.update_sidebar_rule_list()

    def on_manual_refresh(self):
        self.save_active_rule_details()
        self.update_xml_preview()

    def update_xml_preview(self):
        """Builds XML data, renders it, and applies IDE-like syntax coloring."""
        try:
            xml_content = generate_benchmark_xml(self.benchmark)
        except Exception as e:
            xml_content = f"Error generating XML preview:\n{str(e)}"

        # Preserve scroll position so auto-save doesn't jump back to the top
        try:
            ypos = self.preview_textbox.yview()[0]
        except Exception:
            ypos = 0.0

        # Temporarily enable textbox to update, then disable to keep read-only
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", xml_content)

        # Colorize XML text with tags
        self.highlight_xml_preview()

        self.preview_textbox.configure(state="disabled")

        # Restore scroll position
        self.preview_textbox.yview_moveto(ypos)

    def highlight_xml_preview(self):
        """Helper that scans the XML string and applies colors to tags, attributes, values, and comments."""
        text = self.preview_textbox.get("1.0", "end-1c")
        
        # Reset syntax tags
        for tag in ["xml_tag", "xml_bracket", "xml_attr", "xml_value", "xml_comment", "xml_cdata"]:
            self.preview_textbox.tag_remove(tag, "1.0", "end")
            
        # 1. Highlight XML Comments
        for m in re.finditer(r"<!--.*?-->", text, re.DOTALL):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.preview_textbox.tag_add("xml_comment", start, end)
            
        # 2. Highlight CDATA blocks and HTML/XML escaped tags (&lt; / &gt;)
        for m in re.finditer(r"<!\[CDATA\[.*?\]\]>|&lt;.*?&gt;", text, re.DOTALL):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.preview_textbox.tag_add("xml_cdata", start, end)
            
        # 3. Highlight standard XML tags and attributes
        for m in re.finditer(r"<[^>]+>", text):
            tag_content = m.group(0)
            if tag_content.startswith("<!--") or tag_content.startswith("<![CDATA["):
                continue
                
            start_pos = m.start()
            end_pos = m.end()
            
            # Apply base bracket highlight (<, >, </, />)
            self.preview_textbox.tag_add("xml_bracket", f"1.0 + {start_pos} chars", f"1.0 + {end_pos} chars")
            
            # Extract and highlight Tag name (Benchmark, Rule, Group, title...)
            name_match = re.match(r"^</?([a-zA-Z0-9_\-:]+)", tag_content)
            if name_match:
                n_start = start_pos + name_match.start(1)
                n_end = start_pos + name_match.end(1)
                self.preview_textbox.tag_add("xml_tag", f"1.0 + {n_start} chars", f"1.0 + {n_end} chars")
                
            # Extract and highlight attribute pairs (id="...", xml:lang="...")
            for attr_m in re.finditer(r"([a-zA-Z0-9_\-:]+)\s*=\s*(['\"])(.*?)\2", tag_content):
                attr_start = start_pos + attr_m.start(1)
                attr_end = start_pos + attr_m.end(1)
                self.preview_textbox.tag_add("xml_attr", f"1.0 + {attr_start} chars", f"1.0 + {attr_end} chars")
                
                val_start = start_pos + attr_m.start(2)
                val_end = start_pos + attr_m.end(0)
                self.preview_textbox.tag_add("xml_value", f"1.0 + {val_start} chars", f"1.0 + {val_end} chars")

    def _select_all(self, event=None):
        """Selects all text in the currently focused entry or textbox widget."""
        widget = self.focus_get()
        if widget is None:
            return
        try:
            if isinstance(widget, ctk.CTkTextbox) or hasattr(widget, 'tag_add'):
                widget.tag_add("sel", "1.0", "end")
            else:
                widget.select_range(0, "end")
                widget.icursor("end")
        except Exception:
            pass
        return "break"

    # --- Exit / Autosave ---

    def _write_autosave(self):
        try:
            xml = generate_benchmark_xml(self.benchmark)
            with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
                f.write(xml)
        except Exception:
            pass

    def _delete_autosave(self):
        try:
            if os.path.exists(AUTOSAVE_PATH):
                os.remove(AUTOSAVE_PATH)
        except Exception:
            pass

    def _restore_autosave_if_exists(self):
        if not os.path.exists(AUTOSAVE_PATH):
            return
        if messagebox.askyesno(
            "Recover Previous Session",
            "An auto-save from a previous session was found.\n"
            "Restore unsaved work?",
            icon="warning"
        ):
            try:
                recovered = parse_benchmark_xml(AUTOSAVE_PATH)
                if recovered.rules:
                    self.load_benchmark(recovered)
                    self._last_saved_xml = generate_benchmark_xml(self.benchmark)
            except Exception as e:
                messagebox.showerror("Recovery Failed", f"Could not restore autosave:\n{e}")
        else:
            self._delete_autosave()

    def _on_close(self):
        self.save_active_rule_details()
        try:
            current_xml = generate_benchmark_xml(self.benchmark)
        except Exception:
            current_xml = ""

        if current_xml != self._last_saved_xml:
            answer = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes that haven't been exported.\n\n"
                "Export before closing?"
            )
            if answer is None:   # Cancel → stay open
                return
            if answer:           # Yes → export first
                if not self.export_xml():
                    return       # user cancelled the file dialog → stay open

        self._delete_autosave()
        self.destroy()

    # --- Rule Reordering ---

    def move_rule_up(self):
        if self.active_rule_index is None or self.active_rule_index == 0:
            return
        self.save_active_rule_details()
        i = self.active_rule_index
        rules = self.benchmark.rules
        rules[i - 1], rules[i] = rules[i], rules[i - 1]
        self.active_rule_index -= 1
        self.update_sidebar_rule_list()
        self.update_xml_preview()

    def move_rule_down(self):
        if self.active_rule_index is None or self.active_rule_index >= len(self.benchmark.rules) - 1:
            return
        self.save_active_rule_details()
        i = self.active_rule_index
        rules = self.benchmark.rules
        rules[i], rules[i + 1] = rules[i + 1], rules[i]
        self.active_rule_index += 1
        self.update_sidebar_rule_list()
        self.update_xml_preview()

    # --- Benchmark Metadata Editor ---

    def open_benchmark_info(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Benchmark Properties")
        self.update_idletasks()
        dx = self.winfo_rootx() + (self.winfo_width() - 520) // 2
        dy = self.winfo_rooty() + (self.winfo_height() - 420) // 3
        dlg.geometry(f"520x420+{max(dx, 0)}+{max(dy, 0)}")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(fg_color=COLOR_BG_MAIN)

        ctk.CTkLabel(
            dlg, text="Benchmark Properties",
            font=(FONT_FAMILY, 15, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(padx=24, pady=(20, 14), anchor="w")

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="x", padx=24, expand=False)

        meta_fields = [
            ("Benchmark ID",       "benchmark_id",  ""),
            ("Title",              "title",         ""),
            ("Version",            "version",       ""),
            ("Release Date",       "release_info",  "YYYY-MM-DD"),
            ("Publisher",          "publisher",     ""),
        ]
        entries = {}
        for label_text, attr, placeholder in meta_fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=label_text, width=110, anchor="w",
                font=(FONT_FAMILY, 12), text_color=COLOR_TEXT_MUTED
            ).pack(side="left")
            ent = ctk.CTkEntry(
                row, height=32, font=(FONT_FAMILY, 12),
                fg_color=COLOR_BG_INPUT, text_color=COLOR_TEXT_PRIMARY,
                border_color=COLOR_BORDER, corner_radius=5,
                placeholder_text=placeholder
            )
            ent.insert(0, getattr(self.benchmark, attr, "") or "")
            ent.pack(side="left", fill="x", expand=True)
            entries[attr] = ent

        ctk.CTkLabel(
            form, text="Description", anchor="w",
            font=(FONT_FAMILY, 12), text_color=COLOR_TEXT_MUTED
        ).pack(fill="x", pady=(10, 2))
        desc_box = ctk.CTkTextbox(
            form, height=80, font=(FONT_FAMILY, 12),
            fg_color=COLOR_BG_INPUT, text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_BORDER, border_width=1, corner_radius=5
        )
        desc_box.insert("1.0", self.benchmark.description or "")
        desc_box.pack(fill="x")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=16, side="bottom")

        def _save():
            for attr, ent in entries.items():
                setattr(self.benchmark, attr, ent.get().strip())
            self.benchmark.description = desc_box.get("1.0", "end-1c").strip()
            self.update_xml_preview()
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text="Save", command=_save,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color="#ffffff", height=32, font=(FONT_FAMILY, 12, "bold"),
            corner_radius=6
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            btn_row, text="Cancel", command=dlg.destroy,
            fg_color=COLOR_BG_INPUT, hover_color=COLOR_BG_HOVER,
            text_color=COLOR_TEXT_DIM, height=32, font=(FONT_FAMILY, 12),
            border_width=1, border_color=COLOR_BORDER, corner_radius=6
        ).pack(side="right")

    def check_for_changes(self):
        """Checks for editing modifications every 1.5 seconds, auto-saving and updating the UI dynamically."""
        self.save_active_rule_details()
        self.update_xml_preview()
        self._write_autosave()
        self._check_id = None  # clear before rescheduling
        
        # Update the Rule Editor header and rebuild the sidebar card list when title/ID changes
        if self.active_rule_index is not None and 0 <= self.active_rule_index < len(self.benchmark.rules):
            rule = self.benchmark.rules[self.active_rule_index]
            title_text = rule.title.strip() or rule.rule_id.strip() or "(New Rule)"
            if self.rule_editor_label.cget("text") != title_text:
                self.rule_editor_label.configure(text=title_text)
                self.update_sidebar_rule_list()
                    
        self._check_id = self.after(1500, self.check_for_changes)


if __name__ == "__main__":
    app = STIGApp()
    app.mainloop()