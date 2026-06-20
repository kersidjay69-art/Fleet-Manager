"""Генератор анимированного GIF со змеёй для полоски флота.

Рисуем кадры змеи (Pillow), собираем прозрачный зацикленный GIF. imageio
используется для валидации результата. Запуск из корня проекта:

    python tools/make_snake.py

Результат: ui/snake.gif  — змея «слизывает» волной (seamless loop), прозрачный
фон, края подложены под цвет зелёной заливки (Uroborus accent), чтобы на ней
смотреться без ореола.
"""
import math
import os

from PIL import Image, ImageDraw
import imageio.v3 as iio

# Геометрия кадра
W, H = 104, 18
N = 20                      # кадров в цикле
MID = H / 2.0
AMP = 2.3                   # амплитуда волны
LAM = 56.0                  # длина волны (px)
K = 2 * math.pi / LAM

X_TAIL = 5
X_NECK = 80
HX, RX, RY = 86.0, 8.0, 6.5  # голова

# Цвета. Змея ползёт по ТЁМНОЙ полоске, поэтому края матируем под тёмный фон.
FILL_MATTE = (6, 12, 18)         # = styles.BG_DEEP, под него матируем края
BODY = (172, 202, 72)
BODY_DK = (104, 130, 38)
BODY_HI = (208, 226, 112)
EYE_WHITE = (235, 240, 220)
RUBY = (224, 17, 95)
PUPIL = (24, 22, 28)
TONGUE = (212, 44, 44)


def thickness(x: float) -> float:
    """Профиль толщины тела: тонкий хвост → толстое тело → шея."""
    if x < X_TAIL + 14:
        return 1.2 + (6.0 - 1.2) * (x - X_TAIL) / 14.0
    if x > X_NECK - 10:
        return 6.0 - (6.0 - 4.6) * (x - (X_NECK - 10)) / 10.0
    return 6.0


def centerline(x: float, phase: float) -> float:
    return MID + AMP * math.sin(K * x - phase)


def draw_frame(phase: float, tongue_out: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    xs = [x for x in range(X_TAIL, X_NECK + 1)]
    top, bot = [], []
    for x in xs:
        cy = centerline(x, phase)
        t = thickness(x) / 2.0
        top.append((x, cy - t))
        bot.append((x, cy + t))

    # Тело (полигон) + тёмная окантовка.
    poly = top + bot[::-1]
    d.polygon(poly, fill=BODY, outline=BODY_DK)

    # Верхний блик.
    hi = [(x, centerline(x, phase) - thickness(x) / 2.0 + 1.0) for x in xs[::2]]
    if len(hi) > 1:
        d.line(hi, fill=BODY_HI, width=1)

    # Чешуйки: короткие тёмные дуги в шахматном порядке по задним 60% тела.
    x_scale_end = X_TAIL + int(0.62 * (X_NECK - X_TAIL))
    for i, x in enumerate(range(X_TAIL + 6, x_scale_end, 4)):
        cy = centerline(x, phase)
        for row in (-1.4, 1.4):
            off = 2 if (i % 2) else 0
            bbox = [x - 2 + off, cy + row - 2, x + 2 + off, cy + row + 2]
            d.arc(bbox, start=200, end=340, fill=BODY_DK)

    # Голова.
    hy = centerline(X_NECK, phase)
    d.ellipse([HX - RX, hy - RY, HX + RX, hy + RY], fill=BODY, outline=BODY_DK)
    # Глаз с рубиновой радужкой.
    ex, ey = HX + 1.0, hy - 2.2
    d.ellipse([ex - 2.0, ey - 2.0, ex + 2.0, ey + 2.0], fill=EYE_WHITE)
    d.ellipse([ex - 1.6, ey - 1.6, ex + 1.6, ey + 1.6], fill=RUBY)
    d.ellipse([ex - 0.7, ey - 0.7, ex + 0.7, ey + 0.7], fill=PUPIL)
    # Рот.
    d.line([HX + RX - 1, hy + 1.5, HX + RX + 1, hy + 2.2], fill=BODY_DK, width=1)
    # Раздвоенный язык (выдвигается).
    if tongue_out > 0.05:
        tx0 = HX + RX
        tlen = 5.0 * tongue_out
        tipx = tx0 + tlen
        d.line([tx0, hy + 1.8, tipx, hy + 2.2], fill=TONGUE, width=1)
        d.line([tipx, hy + 2.2, tipx + 2, hy + 1.0], fill=TONGUE, width=1)
        d.line([tipx, hy + 2.2, tipx + 2, hy + 3.4], fill=TONGUE, width=1)

    return img


def to_transparent_p(rgba: Image.Image) -> Image.Image:
    """RGBA → палитровый кадр с прозрачностью (края матируем под заливку)."""
    matte = Image.new("RGBA", rgba.size, FILL_MATTE + (255,))
    comp = Image.alpha_composite(matte, rgba).convert("RGB")
    p = comp.convert("P", palette=Image.ADAPTIVE, colors=255)
    alpha = rgba.split()[3]
    transparent_mask = alpha.point(lambda v: 255 if v < 8 else 0)
    p.paste(255, (0, 0), transparent_mask)          # индекс 255 = прозрачный
    p.info["transparency"] = 255
    return p


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "ui", "snake.gif")
    frames = []
    for f in range(N):
        phase = 2 * math.pi * f / N                  # seamless: f=N == f=0
        # Язык мелькает дважды за цикл.
        cyc = (f % (N // 2)) / (N // 2)
        tongue = max(0.0, math.sin(math.pi * cyc * 2)) if cyc < 0.5 else 0.0
        frames.append(to_transparent_p(draw_frame(phase, tongue)))

    frames[0].save(
        out, save_all=True, append_images=frames[1:],
        duration=60, loop=0, disposal=2, transparency=255, optimize=False,
    )
    # Валидация через imageio (первый кадр; кадры GIF оптимизированы по размеру).
    arr = iio.imread(out, index=0)
    print(f"saved {out}: {len(frames)} frames, frame0 shape {getattr(arr, 'shape', '?')}, size {W}x{H}")


if __name__ == "__main__":
    main()
