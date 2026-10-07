#!/usr/bin/env python3
"""
Kit de marca ZEPHIRUM — gera todos os PNGs a partir da mesma geometria dos SVGs.

Marcas oficiais (2026-10-06):
- zephirum_bloch_z   — ZEPHIRUM (linguagem): o vetor no equador, nem |0⟩ nem |1⟩ = Z
- zca_escada     — ZCA (algoritmo comercial): para no primeiro degrau que decide
- kernel_caroco  — Decision Kernel (produto): só o caroço sobrevive

Cada marca sai em: dark, light, transparent, favicon (64px, sem texto).
O monograma Z v1 (assets/logo/) é preservado como história, não é apagado.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, PathPatch, RegularPolygon
from matplotlib.path import Path

DARK = dict(bg="#0A1A3C", dim="#7FA8D9", ghost="#33517E",
            accent="#22D3EE", bright="#E8F6FF")
LIGHT = dict(bg="#FFFFFF", dim="#5A75A8", ghost="#C6D4EC",
             accent="#0891B2", bright="#0A1A3C")


# ── ZEPHIRUM: Bloch-Z ──────────────────────────────────────────────────
def draw_zephirum(ax, p, simple=False):
    ax.set_xlim(0, 512); ax.set_ylim(0, 512); ax.set_aspect("equal"); ax.axis("off")
    C, R, SQ = 256, 170, 47.6
    ax.add_patch(Circle((C, C), R, fill=False, ec=p["dim"], lw=1.6, alpha=.75))
    ax.add_patch(Ellipse((C, C), 2 * R, 2 * SQ, fill=False, ec=p["accent"], lw=1.8, alpha=.55))
    ax.add_patch(Ellipse((C, C), 2 * SQ, 2 * R, fill=False, ec=p["dim"], lw=.8, alpha=.35))
    ax.plot([C, C], [C - R, C + R], color=p["dim"], lw=.9, ls=(0, (2, 4)), alpha=.5)
    a = math.radians(34)
    tip = (C + R * math.cos(a), C + R * math.sin(a) * SQ / R)
    for ctrl1, ctrl2, pole in [((426, 376), (290, 376), (256, 426)), ((441, 156), (293, 156), (256, 86))]:
        ax.add_patch(PathPatch(Path([tip, ctrl1, ctrl2, pole],
                                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]),
                               fill=False, ec=p["accent"], lw=1.6, ls=(0, (5, 5)), alpha=.5))
    ax.add_patch(FancyArrowPatch((C, C), tip, arrowstyle="-|>", mutation_scale=24,
                                 color=p["accent"], lw=3.4, zorder=6))
    for ang, ln in [(0, 34), (90, 34), (45, 18), (135, 18)]:
        t = math.radians(ang)
        ax.plot([tip[0] - ln * math.cos(t), tip[0] + ln * math.cos(t)],
                [tip[1] - ln * math.sin(t), tip[1] + ln * math.sin(t)],
                color=p["bright"], lw=2.6, zorder=7, solid_capstyle="round")
    if not simple:
        ax.text(C, 452, "|0\u27E9", ha="center", fontsize=17, color=p["bright"])
        ax.text(C, 52, "|1\u27E9", ha="center", fontsize=17, color=p["bright"])
        ax.text(tip[0] + 52, tip[1] + 9, "Z", fontsize=25, color=p["accent"],
                fontweight="bold", ha="center", va="center", zorder=8)


# ── ZCA: Escada Certificada ────────────────────────────────────────
def draw_zca(ax, p, simple=False):
    ax.set_xlim(0, 512); ax.set_ylim(0, 512); ax.set_aspect("equal"); ax.axis("off")
    if not simple:
        ax.annotate("", xy=(488, 500), xytext=(488, 12),
                    arrowprops=dict(arrowstyle="-|>", color=p["dim"], lw=1.6, alpha=.7))
        ax.text(474, 486, "caro", fontsize=10, color=p["dim"], ha="right", va="top")
        ax.text(474, 20, "barato", fontsize=10, color=p["dim"], ha="right", va="bottom")
    x0, dx, dy, ln = 21, 62, 66, 54
    for i in range(7):
        x, y = x0 + i * dx, 496 - i * dy
        if i < 3:
            ax.plot([x, x + ln], [y, y], color=p["dim"], lw=6, solid_capstyle="round", alpha=.45)
        elif i == 3:
            ax.plot([x, x + ln], [y, y], color=p["accent"], lw=9, solid_capstyle="round", zorder=5)
            cx, cy = x + 27, y
            for ang, L in [(0, 34), (90, 34), (45, 14), (135, 14)]:
                t = math.radians(ang)
                ax.plot([cx - L * math.cos(t), cx + L * math.cos(t)],
                        [cy - L * math.sin(t), cy + L * math.sin(t)],
                        color=p["bright"], lw=2.6, zorder=6, solid_capstyle="round")
            if not simple:
                ax.text(cx, y + 48, "decide aqui · certificado", fontsize=11,
                        color=p["accent"], ha="center")
        else:
            ax.plot([x, x + ln], [y, y], color=p["ghost"], lw=5, ls=(0, (3, 7)),
                    solid_capstyle="round", alpha=.8)


# ── Decision Kernel: o Caroço ──────────────────────────────────────
def draw_kernel(ax, p, simple=False):
    ax.set_xlim(0, 512); ax.set_ylim(0, 512); ax.set_aspect("equal"); ax.axis("off")
    C = 256
    for r, a, lw in [(176, .22, 3), (150, .85, 7)]:
        ax.add_patch(RegularPolygon((C, C), 6, radius=r, orientation=math.pi / 6,
                                   fill=False, ec=p["accent"], lw=lw, alpha=a))
    ax.plot([C, C], [C - 90, C + 90], color=p["accent"], lw=3, alpha=.25)
    for ang, L in [(0, 40), (90, 40), (45, 22), (135, 22)]:
        t = math.radians(ang)
        ax.plot([C - L * math.cos(t), C + L * math.cos(t)],
                [C - L * math.sin(t), C + L * math.sin(t)],
                color=p["bright"], lw=3.2, solid_capstyle="round", zorder=6)
    ax.add_patch(Circle((C, C), 7, color=p["bright"], zorder=7))
    if not simple:
        ax.text(60, 470, "a computação inteira entra", fontsize=10, color=p["dim"], va="top")
        ax.text(452, 70, "só o kernel sai", fontsize=10.5, color=p["accent"], ha="right")


MARKS = [("zephirum_bloch_z", draw_zephirum), ("zca_escada", draw_zca), ("kernel_caroco", draw_kernel)]


def render(draw, pal, path, size=(8, 8), dpi=64, transparent=False):
    bg = "none" if transparent else pal["bg"]
    fig = plt.figure(figsize=size, facecolor=bg)
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.92])
    ax.set_facecolor(bg)
    draw(ax, pal, simple=(size == (1, 1)))
    fig.savefig(path, dpi=dpi, transparent=transparent, facecolor=bg)
    plt.close(fig)


if __name__ == "__main__":
    out = "assets/brand"
    for name, fn in MARKS:
        render(fn, DARK, "%s/%s_dark.png" % (out, name))
        render(fn, LIGHT, "%s/%s_light.png" % (out, name))
        render(fn, DARK, "%s/%s_transparent.png" % (out, name), transparent=True)
        render(fn, DARK, "%s/%s_favicon.png" % (out, name), size=(1, 1))
    print("kit de marca gerado em", out)
