#!/usr/bin/env python3
"""Front page for Thursday 26 November 2026.

A deterministic, standard-library-only Python program. It rasterises a
one-page newspaper front page into an RGB buffer and encodes it as a PNG
with zlib, writing /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

The page sums up the day's world news as reported on 26 November 2026:
Hong Kong marks one year since the Tai Po fire, with the inquiry's final
report handed in and new victim aid announced; the Shenzhou-24 crew spends
its first full day aboard Tiangong, carrying Pakistan's first astronaut;
Thanksgiving in the United States is battered by a nor'easter; plus the
day in brief. No network, no fonts on disk, no files read: lettering comes
from a small 5x7 bitmap font defined below, where '#' is a set pixel.
"""

import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# --- palette ----------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (24, 24, 24)
NAVY = (18, 36, 72)
NAVY_DEEP = (9, 18, 40)
DUSK = (52, 48, 96)
EMBER = (214, 96, 32)
RED = (178, 38, 30)
GOLD = (216, 166, 34)
FLAME = (246, 186, 30)
PALE = (255, 232, 150)
SMOKE = (126, 126, 122)
GREY = (96, 96, 94)
FAINT = (206, 204, 194)
STEEL = (148, 156, 166)
SKYBLUE = (52, 96, 160)
TEAL = (26, 122, 112)
WHITE = (255, 255, 255)
CREAM = (233, 229, 219)
CANDLE = (255, 214, 110)

# --- 5x7 bitmap font: '#' is a set pixel, '.' is empty ----------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", "#..##", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}


class Canvas:
    """A flat RGB buffer with tiny drawing primitives."""

    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.pixels = bytearray(width * height * 3)
        self.clip = None
        self.fill(0, 0, width, height, colour)

    def set_clip(self, x0, y0, x1, y1):
        self.clip = (x0, y0, x1, y1)

    def clear_clip(self):
        self.clip = None

    def dot(self, x, y, colour):
        if self.clip is not None:
            if not (self.clip[0] <= x <= self.clip[2]
                    and self.clip[1] <= y <= self.clip[3]):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pixels[i], self.pixels[i + 1], self.pixels[i + 2] = colour

    def fill(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            for xx in range(w):
                i = base + xx * 3
                self.pixels[i], self.pixels[i + 1], self.pixels[i + 2] = colour

    def hspan(self, x0, x1, y, colour):
        for x in range(x0, x1 + 1):
            self.dot(x, y, colour)

    def vspan(self, x, y0, y1, colour):
        for y in range(y0, y1 + 1):
            self.dot(x, y, colour)

    def seg(self, x0, y0, x1, y1, colour):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.dot(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def ball(self, cx, cy, r, colour):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.dot(x, y, colour)

    def halo(self, cx, cy, r, colour, thick=3):
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if r - thick <= d <= r:
                    self.dot(x, y, colour)

    def wedge(self, x0, y0, x1, y1, x2, y2, colour):
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        for y in range(ay, cy + 1):
            if y < by:
                t1 = (y - ay) / max(1, by - ay)
                xa = ax + (bx - ax) * t1
            else:
                xa = bx
            t2 = (y - ay) / max(1, cy - ay)
            xb = ax + (cx - ax) * t2
            for x in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
                self.dot(x, y, colour)

    def draw_text(self, s, x, y, scale, colour):
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for r in range(7):
                row = glyph[r]
                for col in range(5):
                    if row[col] == "#":
                        self.fill(cx + col * scale, y + r * scale,
                                  scale, scale, colour)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def draw_centred(self, s, y, scale, colour, x0=0, x1=PAGE_W):
        w = self.text_width(s, scale)
        self.draw_text(s, x0 + (x1 - x0 - w) // 2, y, scale, colour)

    def wrap_text(self, s, scale, max_w):
        words, lines, cur = s.split(" "), [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def block(self, lines, x, y, scale, colour, gap=6):
        for ln in lines:
            self.draw_text(ln, x, y, scale, colour)
            y += 7 * scale + gap
        return y


# --- the page -----------------------------------------------------------------

def masthead(cv):
    cv.fill(0, 0, PAGE_W, 88, NAVY)
    cv.fill(0, 88, PAGE_W, 5, RED)
    cv.draw_centred("THE WORLD IN ONE PICTURE", 20, 6, WHITE)
    cv.draw_centred("THURSDAY, 26 NOVEMBER 2026", 106, 4, INK)
    cv.hspan(32, 991, 142, INK)
    cv.hspan(32, 991, 146, INK)


def candle(cv, x, y):
    """One small memorial candle with a flame, base at (x, y)."""
    cv.fill(x - 3, y - 16, 6, 16, WHITE)
    cv.fill(x - 4, y - 17, 8, 2, GOLD)
    cv.wedge(x - 4, y - 18, x, y - 34, x + 4, y - 18, EMBER)
    cv.wedge(x - 2, y - 18, x, y - 28, x + 2, y - 18, PALE)


def skyline(cv, x0, y_base, x1):
    """Dark tower silhouettes with lit windows, deterministic pattern."""
    heights = [150, 210, 120, 190, 240, 140, 175, 205, 130, 165]
    widths = [86, 64, 96, 72, 58, 92, 70, 60, 88, 66]
    x = x0
    for i, (hgt, wdt) in enumerate(zip(heights, widths)):
        if x + wdt > x1:
            break
        cv.fill(x, y_base - hgt, wdt, hgt, (16, 16, 24))
        rows = hgt // 26
        cols = wdt // 18
        for r in range(rows):
            for c in range(cols):
                if (i * 7 + r * 3 + c * 5) % 4 == 0:
                    cv.fill(x + 6 + c * 18, y_base - hgt + 10 + r * 26,
                            7, 9, CANDLE)
        x += wdt + 6


def hero_memorial(cv):
    x0, y0, x1, y1 = 32, 158, 992, 452
    # dusk bands: deep blue down to a warm horizon glow
    for yy in range(y0, y1):
        t = (yy - y0) / (y1 - y0)
        if t < 0.45:
            col = NAVY_DEEP
        elif t < 0.7:
            col = DUSK
        else:
            col = (96, 62, 66)
        cv.hspan(x0, x1 - 1, yy, col)
    # early stars
    for (sx, sy) in [(90, 180), (220, 196), (430, 176), (700, 186),
                     (880, 178), (950, 210), (560, 200), (330, 208),
                     (150, 230), (790, 220)]:
        cv.dot(sx, sy, WHITE)
        cv.dot(sx + 1, sy, WHITE)
    cv.set_clip(x0, y0, x1 - 1, y1 - 1)
    cv.clear_clip()
    skyline(cv, x0 + 8, y1 - 52, x1 - 8)
    # ground line and a row of memorial candles
    cv.fill(x0, y1 - 52, x1 - x0, 4, (8, 8, 12))
    for i, cx in enumerate(range(90, 960, 78)):
        if i % 3 == 1:
            continue
        candle(cv, cx, y1 - 56)
    # caption bar
    cv.fill(x0, y1 - 34, x1 - x0, 34, (12, 12, 14))
    cv.draw_text("WANG FUK COURT, TAI PO - ONE YEAR AFTER THE FIRE",
                 x0 + 14, y1 - 26, 2, WHITE)


def hero_headline(cv):
    cv.draw_text("ONE YEAR ON:", 32, 470, 7, INK)
    cv.draw_text("HONG KONG REMEMBERS", 32, 536, 7, RED)
    cv.block(cv.wrap_text(
        "TAI PO INQUIRY REPORT HANDED IN - HK$630M NEW AID FOR VICTIMS",
        3, 928), 32, 610, 3, INK)
    cv.draw_text("168 LIVES LOST IN THE WANG FUK COURT FIRE, 26 NOV 2025",
                 32, 664, 3, GREY)


def panel_space(cv):
    x0, y0, x1, y1 = 32, 706, 496, 884
    cv.fill(x0, y0, x1 - x0, y1 - y0, CREAM)
    cv.fill(x0, y0, x1 - x0, 6, TEAL)
    # starfield, a rising rocket at top right, and Tiangong below it
    for (sx, sy) in [(60, 740), (140, 780), (420, 730), (460, 800),
                     (90, 850), (380, 860), (250, 720)]:
        cv.dot(sx, sy, INK)
        cv.dot(sx + 1, sy, INK)
    cv.fill(424, 730, 22, 42, WHITE)
    cv.wedge(424, 730, 446, 730, 435, 708, RED)
    cv.fill(419, 758, 7, 14, RED)
    cv.fill(444, 758, 7, 14, RED)
    cv.wedge(430, 772, 440, 772, 435, 800, EMBER)
    cv.wedge(432, 772, 438, 772, 435, 792, FLAME)
    # Tiangong: core module with solar wings
    cv.fill(300, 810, 110, 20, STEEL)
    cv.fill(284, 815, 16, 11, NAVY)
    cv.fill(410, 815, 16, 11, NAVY)
    cv.fill(246, 817, 38, 7, SKYBLUE)
    cv.fill(426, 817, 38, 7, SKYBLUE)
    cv.ball(355, 820, 6, GOLD)
    cv.draw_text("FIRST DAY IN ORBIT", x0 + 12, y0 + 12, 3, INK)
    cv.draw_text("PAKISTAN'S FIRST", x0 + 12, y0 + 44, 3, INK)
    cv.draw_text("ASTRONAUT", x0 + 12, y0 + 76, 3, INK)
    cv.block(cv.wrap_text(
        "SHENZHOU-24 CREW ABOARD TIANGONG - LAUNCHED 25 NOV",
        2, x1 - x0 - 24), x0 + 12, y1 - 44, 2, INK)


def panel_storm(cv):
    x0, y0, x1, y1 = 528, 706, 992, 884
    cv.fill(x0, y0, x1 - x0, y1 - y0, CREAM)
    cv.fill(x0, y0, x1 - x0, 6, RED)
    # storm clouds kept to the right so the headline stays clear
    for (cx, cy, r) in [(880, 790, 26), (940, 768, 22), (960, 730, 16)]:
        cv.ball(cx, cy, r, (120, 126, 134))
    for i in range(14):
        rx = 560 + i * 30
        cv.seg(rx, 800, rx - 12, 836, STEEL)
    # a parade balloon, straining against the wind
    cv.ball(760, 800, 34, RED)
    cv.ball(748, 792, 12, (255, 120, 110))
    cv.fill(752, 834, 16, 12, GOLD)
    cv.seg(756, 834, 748, 820, INK)
    cv.seg(764, 834, 772, 820, INK)
    cv.draw_text("THANKSGIVING IN", x0 + 12, y0 + 12, 4, INK)
    cv.draw_text("THE STORM", x0 + 12, y0 + 46, 4, INK)
    cv.block(cv.wrap_text(
        "100TH MACY'S PARADE FACES NOR'EASTER WINDS - 81.5M TRAVELLING",
        2, x1 - x0 - 24), x0 + 12, y1 - 44, 2, INK)


def in_brief(cv):
    y0 = 896
    cv.draw_text("IN BRIEF", 32, y0, 4, RED)
    cv.hspan(32, 991, y0 + 36, INK)
    items = [
        ("TASMANIA -", "BUSHFIRE BURNS 13,000 HA"),
        ("IOWA -", "ARMY DETONATES LEAD BLAST"),
        ("OIL $91 -", "HOUTHI STRIKE HITS REFINERY"),
        ("USA -", "GDP UP 4.3% IN Q3"),
    ]
    for i, (kicker, body) in enumerate(items):
        x = 32 + (i % 2) * 480
        y = y0 + 46 + (i // 2) * 28
        cv.draw_text(kicker, x, y, 2, RED)
        cv.draw_text(body, x + cv.text_width(kicker + " ", 2), y, 2, INK)
    cv.hspan(32, 991, 1006, INK)


# --- PNG encoding -------------------------------------------------------------

def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(PAGE_H):
        raw.append(0)  # filter: none
        raw += cv.pixels[y * PAGE_W * 3:(y + 1) * PAGE_W * 3]
    ihdr = struct.pack(">IIBBBBB", PAGE_W, PAGE_H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    cv = Canvas(PAGE_W, PAGE_H, PAPER)
    masthead(cv)
    hero_memorial(cv)
    hero_headline(cv)
    panel_space(cv)
    panel_storm(cv)
    in_brief(cv)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    size = write_png(cv, os.path.join(out, "entry.png"))
    print(f"wrote {os.path.join(out, 'entry.png')} "
          f"({PAGE_W}x{PAGE_H}, {size} bytes)")


if __name__ == "__main__":
    main()
