#!/usr/bin/env python3
"""news-image-20261124: draw a newspaper front page summing up the world
news of Tuesday 24 November 2026 as one 1024x1024 PNG.

Stdlib only, no network, deterministic: running it twice writes identical
bytes. Writes $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (17, 17, 17)
RED = (178, 34, 34)
NAVY = (27, 58, 88)
GREY = (90, 86, 76)
LIGHT = (233, 227, 210)

# 5x7 bitmap font, one row per string, '#' = pixel on. Written for this entry.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}


def text_w(s, scale):
    return len(s) * 6 * scale


def wrap(text, max_w, scale):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER * W * H)

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=2):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=False):
        if fill:
            for yy in range(cy - r, cy + r + 1):
                half = int((r * r - (yy - cy) ** 2) ** 0.5)
                for xx in range(cx - half, cx + half + 1):
                    self.set(xx, yy, c)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                           (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def glyph(self, x, y, ch, scale, c):
        rows = FONT.get(ch.upper(), FONT[" "])
        for r, row in enumerate(rows):
            for col, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + col * scale, y + r * scale, scale, scale, c)

    def text(self, x, y, s, scale, c):
        for ch in s:
            self.glyph(x, y, ch, scale, c)
            x += 6 * scale
        return x

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, c)

    def para(self, x, y, s, max_w, scale, c, lh=None):
        lh = lh or (7 * scale + 4)
        for ln in wrap(s, max_w, scale):
            self.text(x, y, ln, scale, c)
            y += lh
        return y

    def png_bytes(self):
        raw = bytearray()
        for yy in range(H):
            raw.append(0)
            raw += self.px[yy * W * 3:(yy + 1) * W * 3]

        def chunk(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return out

        ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


def scales(cv, cx, top, s):
    """Simple scales of justice, drawn with lines and circles."""
    cv.vline(cx, top, 150 * s // 10, INK, 4)
    cv.hline(cx - 62, top + 12, 124, INK, 4)
    cv.rect(cx - 26, top + 148, 52, 8, INK)
    for side in (-1, 1):
        px = cx + side * 62
        cv.line(px, top + 12, px - 26, top + 62, INK)
        cv.line(px, top + 12, px + 26, top + 62, INK)
        cv.line(px - 26, top + 62, px + 26, top + 62, INK)
        for dx in range(-24, 25, 4):
            cv.line(px + dx, top + 62, px, top + 86, INK)
        cv.line(px - 26, top + 62, px - 26, top + 66, INK)
    cv.circle(cx, top - 6, 8, INK)


def panel(cv, x, y, w, h, kicker, head_lines, body, icon=None):
    cv.frame(x, y, w, h, INK, 2)
    cv.rect(x + 2, y + 2, w - 4, 26, NAVY)
    cv.text(x + 12, y + 9, kicker, 2, (255, 255, 255))
    ty = y + 40
    for ln in head_lines:
        cv.text(x + 12, ty, ln, 3, INK)
        ty += 24
    ty += 6
    ty = cv.para(x + 12, ty, body, w - 24, 2, INK)
    if icon == "wave":
        for k in range(3):
            yy = y + h - 34 + k * 9
            for xx in range(x + 12, x + w - 12):
                if ((xx // 8) + k) % 2 == 0:
                    cv.set(xx, yy, NAVY)
    elif icon == "sun":
        cx, cy = x + w // 2, y + h - 42
        cv.circle(cx, cy, 16, RED, fill=True)
        for a in range(8):
            dx = int(26 * [1, 0.7, 0, -0.7, -1, -0.7, 0, 0.7][a])
            dy = int(26 * [0, 0.7, 1, 0.7, 0, -0.7, -1, -0.7][a])
            cv.line(cx, cy, cx + dx, cy + dy, RED)
    elif icon == "orbit":
        cx, cy = x + w // 2, y + h - 40
        cv.circle(cx, cy, 12, NAVY, fill=True)
        cv.circle(cx, cy, 26, NAVY)
        cv.circle(cx + 24, cy - 10, 5, RED, fill=True)
    elif icon == "badge":
        cx, cy = x + w // 2, y + h - 42
        cv.circle(cx, cy, 24, RED)
        cv.text_c(cx, cy - 7, "9-6", 2, RED)
    elif icon == "rule":
        cv.hline(x + w // 2 - 40, y + h - 22, 80, GREY, 2)
    return ty


def main():
    cv = Canvas()
    # Masthead
    cv.text_c(W // 2, 26, "THE WORLD TODAY", 7, INK)
    cv.hline(24, 92, W - 48, INK, 4)
    cv.text_c(W // 2, 106, "TUESDAY, 24 NOVEMBER 2026  -  WORLD NEWS IN ONE PAGE", 2, RED)
    cv.hline(24, 136, W - 48, INK, 2)

    # Lead story: ICJ verdict on Myanmar / Rohingya
    ly = 152
    cv.frame(24, ly, W - 48, 316, INK, 3)
    cv.rect(26, ly + 2, W - 52, 30, RED)
    cv.text(40, ly + 10, "LEAD  -  THE HAGUE", 2, (255, 255, 255))
    cv.text(40, ly + 48, "ICJ FINDS MYANMAR", 5, INK)
    cv.text(40, ly + 92, "GUILTY OF GENOCIDE", 5, INK)
    cv.hline(40, ly + 142, 600, INK, 2)
    cv.para(40, ly + 156, "The International Court of Justice ruled 9-6 that "
            "Myanmar committed genocide against the Rohingya, the first "
            "time the court has found a state guilty of genocide.",
            600, 2, INK)
    cv.para(40, ly + 232, "The landmark verdict sets a precedent for the Gaza "
            "case now before the court.", 600, 2, GREY)
    scales(cv, 830, ly + 90, 10)
    cv.text_c(830, ly + 268, "FIRST STATE VERDICT", 2, RED)
    cv.text_c(830, ly + 288, "VOTE 9-6", 2, INK)

    # Middle row: three panels
    my, mh, pw, gap = 488, 252, 312, 20
    panel(cv, 24, my, pw, mh, "UKRAINE - LIBYA",
          ["SEA DRONES SINK", "RUSSIAN CORVETTE"],
          "Ukraine says its sea drones sank the Russian corvette "
          "Merkury off Benghazi, Libya. Tripoli asked Kyiv to explain.", icon="wave")
    panel(cv, 24 + pw + gap, my, pw, mh, "CLIMATE - COP31",
          ["COP31 COLLAPSES", "IN ANTALYA"],
          "Talks broke down after 90+ nations rejected a final draft "
          "that never mentioned fossil fuels. Talks ran 50 hours "
          "into overtime.", icon="sun")
    panel(cv, 24 + 2 * (pw + gap), my, pw, mh, "NATO - SPACE",
          ["NATO VOWS TO", "DEFEND SPACE"],
          "NATO pledged to defend orbit after reports Russia could "
          "launch a nuclear-armed satellite within 60 days.", icon="orbit")

    # Bottom row: three panels
    by, bh = 760, 216
    panel(cv, 24, by, pw, bh, "MEXICO - CARTELS",
          ["EL CHAPO ISIDRO", "CAPTURED"],
          "US drones helped Mexico capture drug lord Fausto Isidro "
          "Meza Flores. Mexico will prosecute him.",
          icon="rule")
    panel(cv, 24 + pw + gap, by, pw, bh, "MARKETS - TECH",
          ["HUANG RETURNS", "TO NVIDIA"],
          "Nvidia brought back Jensen Huang as CEO after Trump stepped "
          "in. Markets rallied: Nikkei +3.91%, Kospi up 6%+.", icon="rule")
    panel(cv, 24 + 2 * (pw + gap), by, pw, bh, "IN BRIEF",
          ["QUAKE AND", "EXECUTION"],
          "NEPAL: a 5.6 earthquake struck near the China border. "
          "CHINA: an official was executed for espionage.", icon="rule")

    cv.hline(24, 992, W - 48, INK, 2)
    cv.text_c(W // 2, 1000, "THE WORLD TODAY  -  24 NOVEMBER 2026", 2, GREY)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(cv.png_bytes())
    print("wrote", path)


if __name__ == "__main__":
    main()
