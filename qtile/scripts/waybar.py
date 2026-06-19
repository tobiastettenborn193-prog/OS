import os
import dotenv

from libqtile import bar, widget
from libqtile.config import Screen

from scripts.live_theme import LIVE_WIDGETS

QTILE_DIR = os.path.expanduser("~/os/qtile")
dotenv.load_dotenv(os.path.join(QTILE_DIR, "env", "system_colors.env"))

FONT = "JetBrainsMono Nerd Font"
FSIZE = 14

def _make_bar_bg(alpha_hex: str = "CC") -> str:
    bg = os.getenv("BAR_BG", "#000000").replace("#", "")
    return f"#{bg}{alpha_hex}"

BAR_BG = _make_bar_bg("A6")

def _gap(n=8):
    return widget.Spacer(length=n)

def _pipe(key):
    w = widget.TextBox(
        text="│",
        font=FONT,
        fontsize=FSIZE,
        foreground=os.getenv("SEP_COLOR", "#888888"),
        padding=6
    )
    LIVE_WIDGETS[key] = w
    return w

def _icon(key, text, color_key, fallback_color):
    w = widget.TextBox(
        text=text,
        font=FONT,
        fontsize=FSIZE,
        foreground=os.getenv(color_key, fallback_color),
        padding=4
    )
    LIVE_WIDGETS[key] = w
    return w

def build_screens():
    accent = os.getenv("ACCENT_ACTIVE", "#005577")
    accent_inactive = os.getenv("ACCENT_INACTIVE", "#444444")
    muted = os.getenv("TEXT_MUTED", "#888888")
    fg = os.getenv("TEXT_FG", "#ffffff")
    alert = os.getenv("CPU_RAM_COLOR", "#ff0000")

    arch_logo = widget.TextBox(
        text="󰣇", font=FONT, fontsize=18, foreground=os.getenv("LOGO_COLOR", accent), padding=8,
        mouse_callbacks={"Button1": lambda: None},
    )
    LIVE_WIDGETS["arch_logo"] = arch_logo

    gbox = widget.GroupBox(
        font=FONT, fontsize=FSIZE, padding=6, borderwidth=2, highlight_method="line",
        this_current_screen_border=accent, other_current_screen_border=accent_inactive,
        this_screen_border=muted, other_screen_border=muted, highlight_color=["#00000000", "#00000000"],
        active=fg, inactive=muted, urgent_border=alert, background=None, disable_drag=True, rounded=False,
        use_mouse_wheel=False,
    )
    LIVE_WIDGETS["groupbox"] = gbox

    wname = widget.WindowName(
        font=FONT, fontsize=FSIZE, foreground=muted, max_chars=40, empty_group_string="",
    )
    LIVE_WIDGETS["windowname"] = wname

    clk_time = widget.Clock(
        format="%H:%M", font=FONT, fontsize=16, foreground=os.getenv("CLOCK_COLOR", fg), padding=0,
    )
    LIVE_WIDGETS["clock_time"] = clk_time

    clk_sep = widget.TextBox(
        text=" ", font=FONT, fontsize=FSIZE, foreground=muted, padding=0,
    )
    LIVE_WIDGETS["clock_sep"] = clk_sep

    clk_date = widget.Clock(
        format="%a %d.%m.%Y", font=FONT, fontsize=FSIZE, foreground=muted, padding=0,
    )
    LIVE_WIDGETS["clock_date"] = clk_date

    cpu = widget.CPU(
        font=FONT, fontsize=FSIZE, foreground=os.getenv("CPU_RAM_COLOR", alert), format="{load_percent:02.0f}%", update_interval=2, padding=0,
    )
    LIVE_WIDGETS["cpu"] = cpu

    mem = widget.Memory(
        font=FONT, fontsize=FSIZE, foreground=os.getenv("CPU_RAM_COLOR", alert), format="{MemPercent:02.0f}%", update_interval=2, padding=0,
    )
    LIVE_WIDGETS["mem"] = mem

    try:
        vol = widget.PulseVolume(
            font=FONT, fontsize=FSIZE, foreground=os.getenv("AUDIO_COLOR", fg), padding=0, update_interval=0.1, limit_max_volume=True,
        )
    except Exception:
        vol = widget.TextBox(
            text="vol?", font=FONT, fontsize=FSIZE, foreground=os.getenv("AUDIO_COLOR", muted), padding=0
        )
    LIVE_WIDGETS["vol"] = vol

    curr_layout = widget.CurrentLayout(
        font=FONT, fontsize=FSIZE, foreground=accent, padding=4
    )
    LIVE_WIDGETS["current_layout"] = curr_layout

    cpu_icon = _icon("cpu_icon", " ", "CPU_RAM_COLOR", alert)
    mem_icon = _icon("mem_icon", " ", "CPU_RAM_COLOR", alert)
    vol_icon = _icon("vol_icon", " ", "AUDIO_COLOR", fg)

    blocks = (
        [
            _gap(4), arch_logo, _pipe("sep_arch"), gbox, _gap(6), _pipe("sep_title"), _gap(6), wname,
        ]
        + [widget.Spacer(), clk_time, clk_sep, clk_date, widget.Spacer()]
        + [
            cpu_icon, cpu, _gap(4), mem_icon, mem, _pipe("sep_res"),
            vol_icon, vol, _pipe("sep_vol"), curr_layout, _pipe("sep_layout"),
            widget.Systray(padding=8, icon_size=18), _gap(10),
        ]
    )

    # Monitor-Zuordnung hier gefixt:
    return [
        Screen(), # Erster Monitor (ohne Bar)
        Screen(   # Zweiter Monitor (mit Bar)
            top=bar.Bar(
                blocks,
                32,
                background=BAR_BG,
                margin=[6, 10, 0, 10],
                border_width=0,
                opacity=1.0,
            ),
        ),
    ]

screens = build_screens()
