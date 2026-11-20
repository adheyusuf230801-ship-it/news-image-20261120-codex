"""Draw a square newspaper front page with a hand-built bitmap alphabet."""

from math import cos, isqrt, sin
from os import environ
from pathlib import Path
from struct import pack
import zlib


PAGE = 1024
PAPER, INK, RED, TINT, RULE = range(5)
PALETTE = bytes.fromhex("faf7ef 222022 982d34 f2e6df d3c6bc")
FONT = {
    "A": (14,17,17,31,17,17,17), "B": (30,17,17,30,17,17,30),
    "C": (14,17,16,16,16,17,14), "D": (30,17,17,17,17,17,30),
    "E": (31,16,16,30,16,16,31), "F": (31,16,16,30,16,16,16),
    "G": (14,17,16,23,17,17,15), "H": (17,17,17,31,17,17,17),
    "I": (7,2,2,2,2,2,7), "J": (7,2,2,2,2,18,12),
    "K": (17,18,20,24,20,18,17), "L": (16,16,16,16,16,16,31),
    "M": (17,27,21,21,17,17,17), "N": (17,25,25,21,19,19,17),
    "O": (14,17,17,17,17,17,14), "P": (30,17,17,30,16,16,16),
    "Q": (14,17,17,17,21,18,13), "R": (30,17,17,30,20,18,17),
    "S": (15,16,16,14,1,1,30), "T": (31,4,4,4,4,4,4),
    "U": (17,17,17,17,17,17,14), "V": (17,17,17,17,10,10,4),
    "W": (17,17,17,21,21,27,17), "X": (17,17,10,4,10,17,17),
    "Y": (17,17,10,4,4,4,4), "Z": (31,1,2,4,8,16,31),
    "0": (14,17,17,17,17,17,14), "1": (4,12,4,4,4,4,14),
    "2": (14,17,1,6,8,16,31), "3": (30,1,1,14,1,1,30),
    "4": (2,6,10,18,31,2,2), "5": (31,16,16,30,1,1,30),
    "6": (14,16,16,30,17,17,14), "7": (31,1,2,4,8,8,8),
    "8": (14,17,17,14,17,17,14), "9": (14,17,17,15,1,1,14),
    " ": (0,)*7, ".": (0,0,0,0,0,0,1), ",": (0,0,0,0,0,2,4),
    "-": (0,0,0,7,0,0,0), "/": (1,1,2,4,8,16,16),
    "'": (1,1,0,0,0,0,0), ":": (0,0,1,0,0,1,0),
    "$": (4,15,20,14,5,30,4),
}
WIDTHS = {" ": 3, "I": 3, ".": 1, ",": 3, "-": 3, "'": 1, ":": 1}


def measure(label, scale):
    return scale * (sum(WIDTHS.get(letter, 5) + 1 for letter in label) - 1)


class Canvas:
    def __init__(self):
        self.pixels = bytearray(PAGE * PAGE)

    def box(self, x, y, width, height, color):
        assert 0 <= x <= x + width <= PAGE and 0 <= y <= y + height <= PAGE
        stripe = bytes([color]) * width
        for row in range(y, y + height):
            start = row * PAGE + x
            self.pixels[start:start + width] = stripe

    def disc(self, x, y, radius, color):
        for dy in range(-radius, radius + 1):
            half = isqrt(radius * radius - dy * dy)
            self.box(x - half, y + dy, 2 * half + 1, 1, color)

    def line(self, points, thickness, color):
        for (a, b), (c, d) in zip(points, points[1:]):
            steps = max(abs(c - a), abs(d - b), 1)
            for step in range(steps + 1):
                x = a + (c - a) * step // steps
                y = b + (d - b) * step // steps
                self.box(x - thickness // 2, y - thickness // 2,
                         thickness, thickness, color)

    def outline(self, x, y, w, h, stroke, color):
        self.box(x, y, w, stroke, color)
        self.box(x, y + h - stroke, w, stroke, color)
        self.box(x, y, stroke, h, color)
        self.box(x + w - stroke, y, stroke, h, color)

    def type(self, x, y, label, sx, sy, color, *, limit, bold=0):
        assert measure(label, sx) + bold <= limit, label
        for letter in label:
            width = WIDTHS.get(letter, 5)
            for row, bits in enumerate(FONT[letter]):
                for col in range(width):
                    if bits & (1 << (width - col - 1)):
                        self.box(x + col * sx, y + row * sy, sx + bold, sy, color)
            x += (width + 1) * sx

    def centered(self, y, label, sx, sy, color):
        self.type((PAGE - measure(label, sx)) // 2, y, label, sx, sy,
                  color, limit=PAGE - 64)

    def png(self):
        def chunk(name, payload):
            return (pack(">I", len(payload)) + name + payload
                    + pack(">I", zlib.crc32(name + payload)))

        rows = b"".join(b"\0" + self.pixels[i:i + PAGE]
                        for i in range(0, len(self.pixels), PAGE))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", pack(">IIBBBBB", PAGE, PAGE, 8, 3, 0, 0, 0))
                + chunk(b"PLTE", PALETTE)
                + chunk(b"IDAT", zlib.compress(rows, 9))
                + chunk(b"IEND", b""))


# Headline and deck line breaks are set as they would be on a print page.
STORIES = (
    ("JUSTICE", ("MYANMAR GUILTY OF", "ROHINGYA GENOCIDE"),
     ("INTERNATIONAL COURT OF JUSTICE", "RULES ON THE 2017 CRACKDOWN."), "scales"),
    ("SPACE", ("VOYAGER 1 REACHES", "ONE LIGHT-DAY"),
     ("NASA CONFIRMS THE DISTANCE FROM", "EARTH, A RECORD FOR A HUMAN-MADE", "OBJECT."), "dish"),
    ("INDIA", ("CYCLONE AKVAN", "NEARS EAST INDIA"),
     ("ODISHA EVACUATES ABOUT 300,000.", "LANDFALL DUE TODAY. SCHOOLS SHUT.", "HUNDREDS OF RESCUE TEAMS MOBILIZE."), "storm"),
    ("GAMES", ("GTA VI OUTSELLS", "THE ODYSSEY"),
     ("GRAND THEFT AUTO VI TOPS THE", "FILM'S GLOBAL $1.80 BILLION TAKE", "A DAY AFTER RELEASE."), "pad"),
    ("EUROPE", ("EUROPE OPEN TO", "UKRAINE PEACE TALKS"),
     ("LEADERS WOULD TALK TO RUSSIA, WHOSE", "STRIKES DAMAGE AUSTRIAN AND DUTCH", "EMBASSIES IN KYIV. UKRAINE HITS THE", "CRIMEAN BRIDGE WITH RUTA MISSILES."), "bridge"),
    ("JAPAN / SPACE", ("HAYABUSA2 SCRAPS", "ASTEROID LANDING"),
     ("ENGINE TROUBLE FORCES JAPAN'S", "ASTEROID PROBE TO CHANGE COURSE."), "rock"),
    ("MIDDLE EAST", ("HOUTHIS STRIKE", "RIYADH"),
     ("THE ATTACK DAMAGES A TOWER OF", "SAUDI ARABIA'S SOVEREIGN FUND."), "tower"),
    ("BUSINESS", ("ANTHROPIC NEARS", "$1.5 TRILLION"),
     ("REPORTED VALUATION SHOWS HOW", "QUICKLY AI FIRMS ARE GROWING."), "chart"),
)


def pictogram(page, kind, x, y):
    page.disc(x + 30, y + 30, 29, TINT)

    def stroke(*points, color=RED):
        page.line([(x + a, y + b) for a, b in points], 3, color)

    def dot(a, b, radius, color=RED):
        page.disc(x + a, y + b, radius, color)

    if kind == "scales":
        stroke((30, 12), (30, 48))
        stroke((20, 48), (40, 48))
        stroke((14, 21), (46, 21))
        for center in (15, 45):
            stroke((center, 21), (center - 7, 37), (center + 7, 37), (center, 21))
        dot(30, 13, 3)
    elif kind == "dish":
        stroke((13, 25), (16, 36), (24, 44), (35, 47), (13, 25))
        stroke((23, 35), (37, 21))
        stroke((25, 45), (21, 51), (39, 51))
        stroke((36, 13), (43, 16), (48, 22), (50, 28))
        stroke((39, 7), (48, 11), (54, 20))
    elif kind == "storm":
        for phase in (0, 3.14159265):
            points = []
            for i in range(28):
                angle = phase + i * 0.13
                radius = 5 + i * 0.68
                points.append((30 + round(radius * cos(angle)), 30 + round(radius * sin(angle))))
            stroke(*points)
        dot(30, 30, 2)
    elif kind == "pad":
        stroke((14, 22), (46, 22), (53, 39), (48, 44), (37, 37),
               (23, 37), (12, 44), (7, 39), (14, 22))
        stroke((15, 30), (25, 30))
        stroke((20, 25), (20, 35))
        dot(40, 28, 2)
        dot(45, 33, 2)
    elif kind == "bridge":
        stroke((7, 40), (53, 40))
        for post in (17, 43):
            stroke((post, 18), (post, 49))
        stroke((7, 36), (17, 20), (23, 30), (30, 33), (37, 30), (43, 20), (53, 36))
    elif kind == "rock":
        stroke((9, 38), (13, 22), (26, 29), (34, 44), (25, 51), (11, 48), (9, 38))
        dot(18, 38, 3)
        stroke((35, 18), (46, 29), (52, 23), (41, 12), (35, 18))
        stroke((36, 18), (30, 12), (34, 8))
        stroke((47, 28), (53, 34), (57, 30))
    elif kind == "tower":
        stroke((9, 49), (51, 49))
        stroke((16, 48), (16, 20), (28, 12), (40, 20), (40, 48))
        for row in (24, 32, 40):
            stroke((22, row), (32, row))
        stroke((46, 12), (49, 7))
        stroke((47, 22), (54, 19))
    elif kind == "chart":
        stroke((12, 12), (12, 48), (50, 48))
        stroke((18, 40), (27, 31), (34, 34), (49, 17))
        stroke((39, 17), (49, 17), (49, 27))


def front_page():
    page = Canvas()
    page.box(32, 22, 960, 3, RED)
    page.centered(36, "THE WORLD IN ONE DAY", 7, 7, INK)
    page.centered(99, "FRIDAY 20 NOVEMBER 2026", 4, 4, RED)
    page.box(32, 140, 960, 2, RED)

    page.box(32, 154, 960, 237, TINT)
    page.box(32, 154, 6, 237, RED)
    page.type(52, 170, "THE LEAD / IRAN", 2, 2, RED, limit=660, bold=1)
    for i, label in enumerate(("TRUMP PUTS OFF", "IRAN WAR DECISION")):
        page.type(52, 195 + 57 * i, label, 7, 7, INK, limit=690, bold=1)
    for i, label in enumerate(("TRUMP SAYS THERE IS NO HURRY TO DECIDE ON WAR.",
                               "HE'LL WAIT AND SEE AFTER JAN. 1, 2027.")):
        page.type(52, 321 + 21 * i, label, 2, 2, INK, limit=680)

    page.disc(856, 274, 99, PAPER)
    page.box(777, 222, 158, 103, PAPER)
    page.outline(777, 222, 158, 103, 4, RED)
    page.box(777, 222, 158, 24, RED)
    for x in (806, 902):
        page.box(x, 210, 6, 21, INK)
    page.type(795, 258, "2027", 5, 6, INK, limit=125)
    page.line(((801, 310), (906, 310), (899, 303)), 3, RED)
    page.line(((906, 310), (899, 317)), 3, RED)

    page.box(511, 408, 2, 575, RULE)
    row_starts = (407, 552, 697, 853, 992)
    for i, (beat, headline, deck, icon) in enumerate(STORIES):
        x = 32 + (i % 2) * 494
        row = i // 2
        y = row_starts[row]
        assert y + 88 + 15 * (len(deck) - 1) + 14 <= row_starts[row + 1] - 8
        page.box(x, y, 466, 2, RED if i < 2 else RULE)
        page.type(x, y + 7, beat, 2, 2, RED, limit=385, bold=1)
        pictogram(page, icon, x + 403, y + 10)
        for j, label in enumerate(headline):
            page.type(x, y + 25 + 30 * j, label, 3, 4, INK, limit=390, bold=1)
        for j, label in enumerate(deck):
            page.type(x, y + 88 + 15 * j, label, 2, 2, INK, limit=466)

    page.box(32, 992, 960, 2, RED)
    page.centered(1001, "20 NOVEMBER 2026 / THE WORLD IN ONE IMAGE", 2, 2, INK)
    return page


if __name__ == "__main__":
    output = Path(environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    (output / "entry.png").write_bytes(front_page().png())
