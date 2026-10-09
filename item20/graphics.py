"""Broadcast graphics for ITEM 20: Coulee Community Access, Channel 10, 1997. A public-access character
generator: the channel bug, the LIVE tag with the time, lower thirds, the show's bumper, the stand-by
slide and the community bulletin board. All drawn with PIL on the 640x480 frame."""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H = 640, 480
D = "/usr/share/fonts/truetype/dejavu/"
YELLOW, NAVY = (250, 214, 60), (14, 22, 70)


@lru_cache(None)
def F(name, size):
    return ImageFont.truetype(D + name, size)


def clock_text(secs):
    secs = int(secs)
    h, m = (secs // 3600) % 12 or 12, (secs // 60) % 60
    return f"{h}:{m:02d} AM"


def _shadow_text(d, xy, s, f, fill, anchor="la"):
    d.text((xy[0] + 2, xy[1] + 2), s, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def overlay(clock0=None, lower=None, callin=False, bug=True):
    """Graphics keyed over the live feed. lower = (title, subtitle, t_in, t_out)."""
    def post(img, t):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        if bug:   # channel bug, top right, semi-transparent
            d.rounded_rectangle([W - 104, 26, W - 36, 78], 8, outline=(255, 255, 255, 150), width=3)
            d.text((W - 70, 52), "10", font=F("DejaVuSans-Bold.ttf", 30), fill=(255, 255, 255, 160), anchor="mm")
            d.text((W - 70, 88), "CAC", font=F("DejaVuSans-Bold.ttf", 11), fill=(255, 255, 255, 150), anchor="mm")
        if clock0 is not None:   # LIVE tag + time, top left
            d.rectangle([36, 30, 96, 54], fill=(200, 20, 20, 230))
            d.text((66, 42), "LIVE", font=F("DejaVuSans-Bold.ttf", 16), fill=(255, 255, 255, 255), anchor="mm")
            _shadow_text(d, (104, 33), clock_text(clock0 + t), F("DejaVuSans-Bold.ttf", 16), (255, 255, 255, 235))
        if lower:
            title, sub, t0, t1 = lower
            if t0 <= t < t1:
                u = min(1.0, (t - t0) / 0.35, (t1 - t) / 0.35)
                x0 = int(-520 * (1 - u) + 40)
                d.rectangle([x0, 364, x0 + 520, 404], fill=(*NAVY, 225))
                d.rectangle([x0, 404, x0 + 520, 428], fill=(0, 0, 0, 200))
                d.rectangle([x0, 364, x0 + 6, 428], fill=(*YELLOW, 255))
                d.text((x0 + 18, 384), title, font=F("DejaVuSans-Bold.ttf", 20), fill=(255, 255, 255, 255), anchor="lm")
                d.text((x0 + 18, 416), sub, font=F("DejaVuSans-Bold.ttf", 13), fill=(*YELLOW, 255), anchor="lm")
        if callin and not (lower and lower[2] <= t < lower[3]):
            d.rectangle([40, 410, 238, 430], fill=(0, 0, 0, 170))
            d.text((50, 420), "CALL IN  555-0110", font=F("DejaVuSans-Bold.ttf", 13), fill=(*YELLOW, 240), anchor="lm")
        out = img.convert("RGBA")
        out.alpha_composite(ov)
        return out.convert("RGB")
    return post


def _gradient(c1, c2):
    g = Image.new("RGB", (1, H))
    for y in range(H):
        u = y / (H - 1)
        g.putpixel((0, y), tuple(int(a + (b - a) * u) for a, b in zip(c1, c2)))
    return g.resize((W, H))


def _chrome_text(s, size, w=W):
    """Text filled with a metallic gradient and a dark outline (the 90s look)."""
    f = F("DejaVuSans-Bold.ttf", size)
    mask = Image.new("L", (w, size + 20), 0)
    ImageDraw.Draw(mask).text((w // 2, size // 2 + 8), s, font=f, fill=255, anchor="mm")
    fill = Image.new("RGB", mask.size)
    for y in range(mask.size[1]):
        u = y / mask.size[1]
        c = (int(230 - 120 * abs(u - 0.45) * 2), int(225 - 130 * abs(u - 0.45) * 2), 255)
        ImageDraw.Draw(fill).line([(0, y), (w, y)], fill=c)
    outline = mask.filter(ImageFilter.MaxFilter(5))
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste((20, 0, 40, 255), (0, 0), outline)
    out.paste(fill, (0, 0), mask)
    return out


def bumper_frames():
    """COULEE / AFTER DARK over a purple night sky with stars and a moon, zooming in."""
    rnd = random.Random(4)
    stars = [(rnd.randint(0, W), rnd.randint(0, H), rnd.random()) for _ in range(140)]
    sky = _gradient((6, 0, 24), (70, 10, 90))
    t1, t2 = _chrome_text("COULEE", 64), _chrome_text("AFTER DARK", 46)

    def f(i, t):
        img = sky.copy()
        d = ImageDraw.Draw(img)
        for x, y, b in stars:
            tw = 0.5 + 0.5 * math.sin(t * 4 + x)
            c = int(120 + 135 * b * tw)
            d.point((x, y), fill=(c, c, c))
        d.ellipse([470, 60, 560, 150], fill=(235, 230, 200))
        d.ellipse([490, 52, 580, 142], fill=(28, 4, 50))          # crescent
        z = min(1.0, 0.4 + t / 1.2)
        a = int(255 * min(1.0, t / 0.6))
        for txt, cy, delay in ((t1, 200, 0.0), (t2, 270, 0.5)):
            if t < delay:
                continue
            zz = min(1.0, 0.4 + (t - delay) / 1.0)
            im = txt.resize((int(txt.width * zz), int(txt.height * zz)))
            img.paste(im, ((W - im.width) // 2, cy - im.height // 2), im)
        if t > 2.2:
            d.text((W // 2, 340), "LIVE  ·  FRIDAYS AT MIDNIGHT", font=F("DejaVuSans-Bold.ttf", 16), fill=YELLOW, anchor="mm")
        return img
    return f


def standby_frames():
    bg = _gradient((10, 20, 110), (40, 0, 80))

    def f(i, t):
        img = bg.copy()
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([W // 2 - 60, 100, W // 2 + 60, 190], 14, outline=(255, 255, 255), width=5)
        d.text((W // 2, 145), "10", font=F("DejaVuSans-Bold.ttf", 56), fill=(255, 255, 255), anchor="mm")
        d.text((W // 2, 222), "COULEE COMMUNITY ACCESS", font=F("DejaVuSans-Bold.ttf", 18), fill=(220, 220, 255), anchor="mm")
        d.text((W // 2, 300), "PLEASE STAND BY", font=F("DejaVuSans-Bold.ttf", 34), fill=YELLOW, anchor="mm")
        d.text((W // 2, 345), "WE ARE EXPERIENCING TECHNICAL DIFFICULTIES", font=F("DejaVuSans-Bold.ttf", 13),
               fill=(220, 220, 255), anchor="mm")
        return img
    return f


BBS_PAGES = [
    ["COULEE COMMUNITY ACCESS", "CHANNEL 10", "", "COMMUNITY", "BULLETIN BOARD"],
    ["HOLMEN LIONS CLUB", "PANCAKE BREAKFAST", "", "SUN. NOV. 2  ·  7 - 11 AM", "HOLMEN AREA COMMUNITY CENTER"],
    ["LOST DOG", "BROWN LAB MIX \"BUSTER\"", "LAST SEEN: GEORGE ST.", "", "CALL 555-0187"],
    ["COULEE AFTER DARK", "WILL RETURN", "NEXT FRIDAY AT MIDNIGHT", "", "THANK YOU FOR WATCHING"],
    ["OFFICE SPACE AVAILABLE", "BRENNER BUILDING", "FOUR FLOORS  ·  40,000 SQ FT", "LOTS OF POTENTIAL", "CALL GARY  555-0141"],
]


def bbs_frames(page_dur=5.0):
    bg = _gradient((0, 30, 120), (0, 10, 60))

    def f(i, t):
        k = min(int(t / page_dur), len(BBS_PAGES) - 1)
        u = t - k * page_dur
        img = bg.copy()
        d = ImageDraw.Draw(img)
        d.rectangle([30, 30, W - 30, H - 30], outline=(255, 255, 255), width=2)
        lines = BBS_PAGES[k]
        y0 = H // 2 - (len(lines) - 1) * 21
        shown = int(u * 30)    # the character generator types each page out
        n = 0
        for j, line in enumerate(lines):
            s = line[:max(0, shown - n)]
            n += len(line)
            col = YELLOW if j == 0 else (255, 255, 255)
            d.text((W // 2, y0 + j * 42), s, font=F("DejaVuSans-Bold.ttf", 26 if j == 0 else 22), fill=col, anchor="mm")
        d.text((W - 50, H - 50), "10", font=F("DejaVuSans-Bold.ttf", 16), fill=(200, 200, 255), anchor="rm")
        return img
    return f
