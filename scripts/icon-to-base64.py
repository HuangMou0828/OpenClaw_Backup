#!/usr/bin/env python3
"""
将 iconfont 渲染为 base64 PNG，供 Dot. icon 字段使用。

用法：
    python3 icon-to-base64.py xuanzhong11
    python3 icon-to-base64.py --list

icon 文件位于 /Users/hm/openclaw-config/asset/font/icons/
"""
import base64, json, sys
from pathlib import Path

GLYPHS_FILE = Path("/Users/hm/openclaw-config/asset/font/iconfont.json")

def load_glyphs():
    with open(GLYPHS_FILE) as f:
        return {g["font_class"]: g for g in json.load(f)["glyphs"]}

def render_icon(font_class: str) -> str:
    """用 PIL 将 iconfont 字符渲染为 PNG，返回 base64 字符串。"""
    from PIL import Image, ImageDraw, ImageFont

    glyphs = load_glyphs()
    if font_class not in glyphs:
        raise ValueError(f"未知的 icon: {font_class}，可用 --list 查看")
    glyph = glyphs[font_class]
    unicode_char = chr(glyph["unicode_decimal"])

    font = ImageFont.truetype("/Users/hm/openclaw-config/asset/font/iconfont.ttf", 80)
    size = 100
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), unicode_char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    draw.text((x, y), unicode_char, font=font, fill=(0, 0, 0, 255))

    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

if __name__ == "__main__":
    if "--list" in sys.argv or len(sys.argv) < 2:
        glyphs = load_glyphs()
        print("可用 icon：")
        for fc, g in glyphs.items():
            print(f"  {fc:20s}  {g['name']}")
        sys.exit(0)

    fc = sys.argv[1]
    b64 = render_icon(fc)
    print(b64)
