"""Make monitor/TV screen textures from the raw CCTV renders (grayscale + burnt-in timestamp)."""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST, TEX = os.path.join(ROOT, "out", "stills"), os.path.join(ROOT, "out", "tex")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def cctv_look(img, label, stamp, size=None):
    g = ImageOps.grayscale(img).filter(ImageFilter.GaussianBlur(0.8))
    g = ImageEnhance.Contrast(g).enhance(1.4)
    g = ImageEnhance.Brightness(g).enhance(0.8)
    if size:
        g = g.resize(size)
    im = Image.merge("RGB", (g, g, g))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, max(10, im.height // 18))
    d.text((8, 6), label, font=f, fill=(235, 235, 235))
    d.text((8, im.height - im.height // 12 - 8), stamp, font=f, fill=(235, 235, 235))
    for y in range(0, im.height, 2):
        d.line([(0, y), (im.width, y)], fill=(0, 0, 0), width=1) if y % 4 == 0 else None
    return im


def static(w=384, h=288, seed=1):
    random.seed(seed)
    im = Image.effect_noise((w, h), 90).convert("RGB")
    return ImageEnhance.Brightness(im).enhance(1.1)


if __name__ == "__main__":
    os.makedirs(TEX, exist_ok=True)
    jobs = {
        "cctv_N": ("cctv_N", "CAM 02  3F CORR N", "11-09-94 01:58:40"),
        "cctv_N_open": ("cctv_N_open", "CAM 02  3F CORR N", "11-09-94 02:03:12"),
        "cctv_S": ("cctv_S", "CAM 03  3F CORR S", "11-09-94 01:58:40"),
        "cctv_E": ("cctv_E", "CAM 01  3F ELEV", "11-09-94 01:58:40"),
        "tv_feed": ("tv_feed_raw", "CAM 05  3F CORR N", "11-09-94 02:31:07"),
    }
    for out, (src, label, stamp) in jobs.items():
        cctv_look(Image.open(os.path.join(ST, src + ".png")), label, stamp).save(os.path.join(TEX, out + ".png"))
    static().save(os.path.join(TEX, "tv_static.png"))
    print("ok")
