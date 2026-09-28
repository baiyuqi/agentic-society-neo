"""ttkbootstrap design system — typography + spacing + chart plumbing.

``set_theme`` switches the active theme (ttkbootstrap's 30 curated light/dark
families) and, in one place, restyles every ttk widget's font and syncs
matplotlib. Because the theme is global Tcl state, every plain ``tkinter.ttk``
widget follows automatically; the helpers below are thin wrappers so panels
express typographic hierarchy (H1/H2/H3/subtitle/caption) instead of
hand-picking fonts and spacing.
"""
import ttkbootstrap as ttk
import tkinter as tk
import matplotlib

# --- Spacing scale (px) --------------------------------------------------------
XS, S, M, L, XL, XXL = 4, 8, 12, 16, 24, 32
SIDEBAR_WIDTH = 450
PAGE_PADDING = 24

# --- Typography scale ----------------------------------------------------------
# One family (Segoe UI) at a fixed set of sizes/weights. Panels reference these
# through the H1/H2/H3/subtitle/caption helpers rather than inline font tuples,
# so hierarchy stays consistent and a font change is a one-line edit here.
FONT_FAMILY = 'Segoe UI'
FONT_MONO = 'Consolas'

FONT_LOGO = (FONT_FAMILY, 18, 'bold')
FONT_H1 = (FONT_FAMILY, 20, 'bold')
FONT_H2 = (FONT_FAMILY, 16, 'bold')
FONT_H3 = (FONT_FAMILY, 13, 'bold')
FONT_BODY = (FONT_FAMILY, 11)
FONT_SMALL = (FONT_FAMILY, 10)
FONT_CAPTION = (FONT_FAMILY, 9)
FONT_MONO_T = (FONT_MONO, 11)
# Sidebar navigation: items are readable, section "eyebrows" are one step down
# in size but bold + muted, so the two levels never read as one run of text.
FONT_NAV_ITEM = (FONT_FAMILY, 12)
FONT_NAV_SECTION = (FONT_FAMILY, 10, 'bold')
# Runtime skin switcher: all 30 curated themes bundled with ttkbootstrap
# (15 families × light/dark). These are the upstream `CURATED_THEMES` names,
# not hand-derived, so each matches its official demo exactly.
THEMES = [
    'bootstrap-light', 'bootstrap-dark',
    'pydata-light', 'pydata-dark',
    'nord-light', 'nord-dark',
    'solarized-light', 'solarized-dark',
    'catppuccin-light', 'catppuccin-dark',
    'gruvbox-light', 'gruvbox-dark',
    'dracula-light', 'dracula-dark',
    'tokyo-night-light', 'tokyo-night-dark',
    'one-light', 'one-dark',
    'everforest-light', 'everforest-dark',
    'vapor-light', 'vapor-dark',
    'minty-light', 'minty-dark',
    'pulse-light', 'pulse-dark',
    'united-light', 'united-dark',
    'sandstone-light', 'sandstone-dark',
]
DEFAULT_THEME = 'bootstrap-light'

# matplotlib's default DejaVu Sans has no CJK glyphs, so any Chinese axis
# label (年龄/得分/… ) renders as a tofu box unless a CJK font is set. This is
# the single global entry point, so every panel inherits it.
_CJK_FONT = ['Microsoft YaHei', 'SimHei', 'STHeiti', 'Arial Unicode MS']


def available_themes():
    """The themes exposed to the runtime skin switcher."""
    return THEMES


def _pin_matplotlib_dpi():
    """Stop TkAgg from upscaling figures by the Windows DPI ratio.

    With ``tk scaling`` at 2.0 (Windows 150% DPI), matplotlib auto-detects a
    device_pixel_ratio of 1.5 and renders figures 1.5x the widget's logical
    size, overflowing the window. Pin the ratio to 1.0 so a figure matches its
    widget; ttkbootstrap's scaling already sizes the UI correctly.
    """
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    FigureCanvasTkAgg._update_device_pixel_ratio = lambda self, event=None: None


def set_theme(theme_name):
    """Switch the global Bootstrap theme, restyle widgets, and sync matplotlib."""
    _pin_matplotlib_dpi()
    style = ttk.Style()
    style.theme_use(theme_name)
    _style_fonts(style)
    matplotlib.rcParams.update(chart_palette())
    matplotlib.rcParams['font.sans-serif'] = _CJK_FONT
    matplotlib.rcParams['axes.unicode_minus'] = False


def chart_palette():
    """matplotlib rcParams derived from the active ttkbootstrap theme."""
    c = ttk.Style().colors
    return {
        'figure.facecolor': c.bg,
        'axes.facecolor': c.bg,
        'axes.edgecolor': c.border,
        'axes.labelcolor': c.fg,
        'text.color': c.fg,
        'xtick.color': c.fg,
        'ytick.color': c.fg,
        'grid.color': c.border,
        'legend.facecolor': c.bg,
        'legend.edgecolor': c.border,
        'legend.labelcolor': c.fg,
    }


def apply_mpl_theme(fig):
    """Recolor an existing figure and all its axes to the active theme."""
    c = ttk.Style().colors
    fig.patch.set_facecolor(c.bg)
    for ax in fig.axes:
        ax.set_facecolor(c.bg)
        for spine in ax.spines.values():
            spine.set_color(c.border)
        ax.tick_params(colors=c.fg)
        ax.xaxis.label.set_color(c.fg)
        ax.yaxis.label.set_color(c.fg)
        ax.title.set_color(c.fg)
        for line in ax.get_xgridlines() + ax.get_ygridlines():
            line.set_color(c.border)
        leg = ax.get_legend()
        if leg is not None:
            leg.get_frame().set_facecolor(c.bg)
            leg.get_frame().set_edgecolor(c.border)
            for text in leg.get_texts():
                text.set_color(c.fg)


def _style_fonts(style):
    """Global typography + named heading styles.

    Every plain ttk widget defaults to the body font; named ``H1/H2/H3``,
    ``Subtitle``, ``Caption``, and ``Mono`` label styles let panels express
    hierarchy without inline font tuples.
    """
    style.configure('.', font=FONT_BODY)
    style.configure('TLabel', font=FONT_BODY)
    style.configure('TButton', font=FONT_BODY)
    style.configure('TEntry', font=FONT_BODY)
    style.configure('TCombobox', font=FONT_BODY)
    style.configure('TCheckbutton', font=FONT_BODY)
    style.configure('TRadiobutton', font=FONT_BODY)
    style.configure('Treeview', font=FONT_BODY, rowheight=30)
    style.configure('Treeview.Heading', font=FONT_H3)
    # Sidebar nav tree: blend with the page background (no inputbox wash, no
    # border) and give rows enough height that section eyebrows read as separate
    # from their items instead of one run of text.
    nav_bg = style.colors.bg
    style.configure('Nav.Treeview',
                    background=nav_bg, fieldbackground=nav_bg, foreground=style.colors.fg,
                    lightcolor=nav_bg, darkcolor=nav_bg, bordercolor=nav_bg,
                    borderwidth=0, relief='flat', padding=0, rowheight=34)
    style.layout('Nav.Treeview', style.layout('Treeview'))
    style.map('Nav.Treeview',
              background=[('selected', style.colors.selectbg)],
              foreground=[('selected', style.colors.selectfg)])
    style.configure('H1.TLabel', font=FONT_H1)
    style.configure('H2.TLabel', font=FONT_H2)
    style.configure('H3.TLabel', font=FONT_H3)
    style.configure('Subtitle.TLabel', font=FONT_SMALL)
    style.configure('Caption.TLabel', font=FONT_CAPTION)
    style.configure('Mono.TLabel', font=FONT_MONO_T)


def page_header(parent, title, subtitle=None):
    """Page title (left-aligned H1) with an optional muted subtitle."""
    header = ttk.Frame(parent)
    header.pack(fill='x', pady=(0, L))
    title_label = ttk.Label(header, text=title, style='H1.TLabel')
    title_label.pack(anchor='w')
    if subtitle:
        ttk.Label(header, text=subtitle, style='Subtitle.TLabel',
                  bootstyle='secondary').pack(anchor='w')
    return header, title_label


def h2(parent, text, **pack_kwargs):
    """Section-level heading (H2)."""
    lbl = ttk.Label(parent, text=text, style='H2.TLabel')
    lbl.pack(**pack_kwargs)
    return lbl


def h3(parent, text, **pack_kwargs):
    """Group / card heading (H3)."""
    lbl = ttk.Label(parent, text=text, style='H3.TLabel')
    lbl.pack(**pack_kwargs)
    return lbl


def caption(parent, text, **pack_kwargs):
    """Muted caption / hint text."""
    lbl = ttk.Label(parent, text=text, style='Caption.TLabel', bootstyle='secondary')
    lbl.pack(**pack_kwargs)
    return lbl


def card(parent, **pack_kwargs):
    """Rounded-elevated card stand-in: a padded frame."""
    c = ttk.Frame(parent, padding=M)
    c.pack(**pack_kwargs)
    return c


def card_text(parent):
    """Read-only themed text area. Use ``set_text`` to write to it."""
    style = ttk.Style()
    box = tk.Text(parent, wrap='word', font=('Consolas', 12), height=10,
                  bg=style.colors.inputbg, fg=style.colors.inputfg,
                  insertbackground=style.colors.fg, relief='flat', borderwidth=0,
                  highlightthickness=0, padx=M, pady=M)
    box.pack(fill='both', expand=True, padx=M, pady=M)
    box.configure(state='disabled')
    return box


def set_text(box, text):
    box.configure(state='normal')
    box.delete('1.0', 'end')
    if text:
        box.insert('1.0', text)
    box.configure(state='disabled')


def tree_colors():
    """Hex foreground/muted colours for ttk tree tags."""
    style = ttk.Style()
    return style.colors.fg, style.colors.secondary
