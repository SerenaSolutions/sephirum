#!/usr/bin/env python3
"""
Renderiza o logotipo SIFR (monograma ZERUM) em PNG, local, sem créditos.

Mesma geometria do sifr_logo.svg:
- o ZERO: contorno do quadrado (presença silenciosa)
- o UM: a diagonal
- o ZED: o conjunto das três barras
- o ponto central: o Decision Kernel, onde Z colapsa em 0 ou 1

Saídas: sifr_logo_dark.png, sifr_logo_light.png, favicon.png (64px).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

NAVY = "#0A1A3C"
CYAN = "#22D3EE"
WHITE = "#F3F7FF"


def draw(ax, bg, fg):
    ax.set_xlim(0, 512)
    ax.set_ylim(0, 512)
    ax.set_aspect("equal")
    ax.axis("off")
    if bg:
        ax.add_patch(Rectangle((0, 0), 512, 512, transform=ax.transData, color=bg, zorder=-2, clip_on=False))
    # o ZERO (contorno, presença silenciosa)
    ax.add_patch(Rectangle((116, 116), 280, 280,
                           fill=False, edgecolor=fg, lw=18, alpha=0.32,
                           joinstyle="round"))
    # as três barras do ZED (a diagonal é o UM)
    for x1, y1, x2, y2 in [(124, 152, 388, 152), (388, 152, 124, 360),
                           (124, 360, 388, 360)]:
        ax.plot([x1, x2], [y1, y2], color=fg, lw=34,
                solid_capstyle="round", zorder=3)
    # ponto de colapso: o Decision Kernel
    ax.add_patch(Circle((256, 256), 10, color=fg, zorder=4))


def render(path, bg, fg, size=(8, 8)):
    fig = plt.figure(figsize=size, facecolor=bg if bg else "none")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    draw(ax, bg, fg)
    fig.savefig(path, dpi=64 if size == (2, 2) else 64,
                facecolor=bg if bg else "none", transparent=bg is None)
    plt.close(fig)


if __name__ == "__main__":
    out = "assets/logo"
    render("%s/sifr_logo_dark.png" % out, NAVY, CYAN)
    render("%s/sifr_logo_light.png" % out, WHITE, NAVY)
    render("%s/sifr_logo_transparent.png" % out, None, CYAN, size=(2, 2))
    plt.ioff()
    fig = plt.figure(figsize=(1, 1), facecolor=NAVY)
    ax = fig.add_axes([0.04, 0.04, 0.92, 0.92])
    draw(ax, NAVY, CYAN)
    fig.savefig("%s/favicon.png" % out, dpi=64, facecolor=NAVY)
    print("PNGs renderizados em", out)
