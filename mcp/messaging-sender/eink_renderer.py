"""eink_renderer.py — 模板化墨水屏渲染器

输入：JSON 模板 (dict) + 数据 (dict)
输出：PIL.Image（默认 1-bit, 296×152，匹配 Dot. 2.66" 设备）

支持的元素类型：
- text       文字（含 ${var} 变量插值、自动换行、对齐、字体 fallback）
- icon       iconfont 字符（按 font_class 名查 iconfont.json） 或 BMP 图标
- image      任意图片（自动 dither 到 1-bit）
- line       直线
- rect       矩形（实心/描边）
- qrcode     动态生成的二维码
- container  容器（layout: vbox / hbox / absolute，支持 padding/gap/align）

模板示例见 templates/ 目录。
"""

from __future__ import annotations

import base64
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


# ─── Constants ───────────────────────────────────────────────────────────────

DEFAULT_WIDTH = 296
DEFAULT_HEIGHT = 152

_BASE_DIR = Path(__file__).parent

# 字体搜索路径（按优先级）
DEFAULT_FONT_PATHS: list[Path] = [
    _BASE_DIR / "fonts",
    Path("/Users/hm/openclaw-config/asset/font"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]

# 复用 openclaw-config 已有的 iconfont
ICONFONT_PATH = Path("/Users/hm/openclaw-config/asset/font/iconfont.ttf")
ICONFONT_JSON = Path("/Users/hm/openclaw-config/asset/font/iconfont.json")


# ─── Font registry ───────────────────────────────────────────────────────────

class FontRegistry:
    """加载字体并缓存，提供 fallback 链。"""

    # 常用名 → 候选文件名（同名优先匹配 ttf > otf）
    _ALIASES: dict[str, list[str]] = {
        "unifont": ["unifont.ttf", "unifont.otf"],
        "ark-pixel-12": [
            "ark-pixel-12px-monospaced-zh_cn.ttf",
            "ark-pixel-12px-monospaced-zh_cn.otf",
            "ark-pixel-12px.ttf",
        ],
        "ark-pixel-16": [
            "ark-pixel-16px-monospaced-zh_cn.ttf",
            "ark-pixel-16px-monospaced-zh_cn.otf",
            "ark-pixel-16px.ttf",
        ],
        "ark-pixel-10": [
            "ark-pixel-10px-monospaced-zh_cn.ttf",
            "ark-pixel-10px-monospaced-zh_cn.otf",
        ],
        "source-han-bold": [
            "SourceHanSansSC-Bold.otf", "SourceHanSansCN-Bold.otf",
            "SourceHanSansSC-Bold.ttf",
        ],
        "source-han": [
            "SourceHanSansSC-Regular.otf", "SourceHanSansCN-Regular.otf",
            "SourceHanSansSC-Regular.ttf",
        ],
        "system": ["PingFang.ttc", "Hiragino Sans GB.ttc", "Helvetica.ttc", "Arial.ttf"],
    }

    def __init__(self, font_paths: list[Path] | None = None):
        self.paths = font_paths or DEFAULT_FONT_PATHS
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def get(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        """按名加载字体，命中缓存则复用。"""
        key = (name, size)
        if key in self._cache:
            return self._cache[key]
        path = self._resolve(name)
        font = ImageFont.truetype(str(path), size)
        self._cache[key] = font
        return font

    def get_chain(self, names: list[str], size: int) -> list[ImageFont.FreeTypeFont]:
        """按 names 顺序加载字体作为 fallback 链；缺失字体被静默跳过。
        始终在末尾追加 system 字体 + Arial Unicode 作为终极 CJK 兜底。
        """
        chain: list[ImageFont.FreeTypeFont] = []
        seen: set[str] = set()
        ordered = list(names) + ["system", "Arial Unicode.ttf"]
        for n in ordered:
            if n in seen:
                continue
            seen.add(n)
            try:
                chain.append(self.get(n, size))
            except (FileNotFoundError, OSError):
                continue
        if not chain:
            chain.append(ImageFont.load_default())
        return chain

    def _resolve(self, name: str) -> Path:
        # 直接路径
        p = Path(name)
        if p.is_absolute() and p.exists():
            return p
        # 别名 + 自身名 + 常见扩展名
        candidates = self._ALIASES.get(name, []) + [name, f"{name}.otf", f"{name}.ttf", f"{name}.ttc"]
        for c in candidates:
            for d in self.paths:
                fp = d / c
                if fp.exists():
                    return fp
        raise FileNotFoundError(f"Font not found: {name} (searched {[str(p) for p in self.paths]})")


# ─── Glyph & text helpers ────────────────────────────────────────────────────

def _has_glyph(font: ImageFont.FreeTypeFont, ch: str) -> bool:
    """检测字体是否包含 ch 字符。空白字符也算"包含"。"""
    if ch.isspace():
        return True
    try:
        mask = font.getmask(ch)
        return mask.getbbox() is not None
    except Exception:
        return False


def _pick_font(fonts: list[ImageFont.FreeTypeFont], ch: str) -> ImageFont.FreeTypeFont:
    """从 fallback 链选第一个能渲染 ch 的字体。"""
    for f in fonts:
        if _has_glyph(f, ch):
            return f
    return fonts[-1]


def measure_text(text: str, fonts: list[ImageFont.FreeTypeFont]) -> int:
    """逐字符按 fallback 链累加宽度。"""
    width = 0
    for ch in text:
        f = _pick_font(fonts, ch)
        try:
            width += int(round(f.getlength(ch)))
        except AttributeError:
            width += f.getbbox(ch)[2]
    return width


def draw_text_fallback(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fonts: list[ImageFont.FreeTypeFont],
    fill: int = 0,
) -> int:
    """逐字符绘制，自动按 fallback 链选字体。返回总宽度。"""
    x, y = xy
    start_x = x
    for ch in text:
        f = _pick_font(fonts, ch)
        draw.text((x, y), ch, font=f, fill=fill)
        try:
            x += int(round(f.getlength(ch)))
        except AttributeError:
            x += f.getbbox(ch)[2]
    return x - start_x


def wrap_text(text: str, fonts: list[ImageFont.FreeTypeFont], max_width: int) -> list[str]:
    """中英文混排的简单按字宽换行。保留显式 \\n。"""
    lines: list[str] = []
    current = ""
    current_w = 0
    for ch in text:
        if ch == "\n":
            lines.append(current)
            current = ""
            current_w = 0
            continue
        f = _pick_font(fonts, ch)
        try:
            w = int(round(f.getlength(ch)))
        except AttributeError:
            w = f.getbbox(ch)[2]
        if current and current_w + w > max_width:
            lines.append(current)
            current = ch
            current_w = w
        else:
            current += ch
            current_w += w
    if current:
        lines.append(current)
    return lines


# ─── Variable interpolation ──────────────────────────────────────────────────

_VAR_RE = re.compile(r"\$\{([\w.]+)\}")


def interpolate(value: Any, data: dict) -> Any:
    """递归替换 ${path.to.var} 占位符。支持点路径访问 dict。"""
    if isinstance(value, str):
        def repl(m: re.Match) -> str:
            keys = m.group(1).split(".")
            v: Any = data
            for k in keys:
                if isinstance(v, dict):
                    v = v.get(k, "")
                else:
                    return ""
            return "" if v is None else str(v)
        return _VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: interpolate(v, data) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate(item, data) for item in value]
    return value


# ─── Iconfont support ────────────────────────────────────────────────────────

_iconfont_cache: dict[str, str] = {}


def get_iconfont_char(name: str) -> str | None:
    """根据 iconfont.json 的 font_class 取出对应 unicode 字符。"""
    global _iconfont_cache
    if not _iconfont_cache and ICONFONT_JSON.exists():
        data = json.loads(ICONFONT_JSON.read_text())
        _iconfont_cache = {
            g["font_class"]: chr(g["unicode_decimal"])
            for g in data.get("glyphs", [])
        }
    return _iconfont_cache.get(name)


# ─── Color helpers ───────────────────────────────────────────────────────────

def _color_to_int(c: Any, default: int = 0) -> int:
    """black→0, white→255, 其他→default。1-bit 屏只有黑白。"""
    if isinstance(c, int):
        return 0 if c == 0 else 255
    if c == "black":
        return 0
    if c == "white":
        return 255
    return default


# ─── Element renderers ───────────────────────────────────────────────────────

def render_text(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    text = str(interpolate(el.get("content", ""), ctx["data"]))
    if not text:
        return 0, 0
    size = int(el.get("size", 12))
    font_names = el.get("fonts") or el.get("font") or ctx["default_fonts"]
    if isinstance(font_names, str):
        font_names = [font_names]
    # 永远把 unifont 放在 fallback 末位以兜底
    if "unifont" not in font_names:
        font_names = list(font_names) + ["unifont"]
    fonts = ctx["registry"].get_chain(font_names, size)
    fill = _color_to_int(el.get("color", "black"))
    line_height = int(el.get("line_height", round(size * 1.4)))
    max_width = el.get("max_width")

    if max_width:
        lines = wrap_text(text, fonts, int(max_width))
    else:
        lines = text.split("\n")

    align = el.get("align", "left")
    if max_width:
        box_w = int(max_width)
    else:
        box_w = max((measure_text(l, fonts) for l in lines), default=0)

    used_h = 0
    for i, line in enumerate(lines):
        line_w = measure_text(line, fonts)
        if align == "center":
            lx = x + (box_w - line_w) // 2
        elif align == "right":
            lx = x + box_w - line_w
        else:
            lx = x
        ly = y + i * line_height
        draw_text_fallback(draw, (lx, ly), line, fonts, fill=fill)
        used_h = (i + 1) * line_height
    return box_w, used_h


def render_icon(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    name = str(interpolate(el.get("name", ""), ctx["data"]))
    size = int(el.get("size", 16))
    fill = _color_to_int(el.get("color", "black"))

    char = get_iconfont_char(name)
    if char and ICONFONT_PATH.exists():
        font = ImageFont.truetype(str(ICONFONT_PATH), size)
        # iconfont 字符的 bbox 通常带 offset，做归零绘制
        bbox = font.getbbox(char)
        ox = -bbox[0] if bbox else 0
        oy = -bbox[1] if bbox else 0
        draw.text((x + ox, y + oy), char, font=font, fill=fill)
        return size, size

    bmp_path = _BASE_DIR / "icons" / str(size) / f"{name}.bmp"
    if bmp_path.exists():
        icon_img = Image.open(bmp_path).convert("1")
        ctx["canvas"].paste(icon_img, (x, y))
        return icon_img.width, icon_img.height

    # 找不到也占位（避免后续布局错位）
    return size, size


def render_image(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    src = str(interpolate(el.get("src", ""), ctx["data"]))
    if not src:
        return 0, 0
    if src.startswith("data:"):
        b64 = src.split(",", 1)[-1]
        img = Image.open(BytesIO(base64.b64decode(b64)))
    elif Path(src).exists():
        img = Image.open(src)
    else:
        return 0, 0

    w = int(el.get("width", img.width))
    h = int(el.get("height", img.height))
    if (w, h) != img.size:
        img = img.resize((w, h), Image.LANCZOS)

    dither_mode = el.get("dither", "floyd")
    img = img.convert("L")
    if dither_mode == "none":
        img = img.point(lambda v: 0 if v < 128 else 255).convert("1")
    else:
        img = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    ctx["canvas"].paste(img, (x, y))
    return w, h


def render_line(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    x1 = int(el.get("x1", x))
    y1 = int(el.get("y1", y))
    x2 = int(el.get("x2", x1 + 100))
    y2 = int(el.get("y2", y1))
    width = int(el.get("width", 1))
    fill = _color_to_int(el.get("color", "black"))
    draw.line([x1, y1, x2, y2], fill=fill, width=width)
    return abs(x2 - x1) + 1, abs(y2 - y1) + width


def render_rect(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    w = int(el.get("width", 0))
    h = int(el.get("height", 0))
    fill_val = _color_to_int(el["fill"], default=255) if "fill" in el else None
    stroke = el.get("stroke")
    stroke_val = _color_to_int(stroke, default=0) if stroke else None
    stroke_width = int(el.get("stroke_width", 1))
    draw.rectangle(
        [x, y, x + w, y + h],
        fill=fill_val,
        outline=stroke_val,
        width=stroke_width,
    )
    return w, h


def render_qrcode(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    try:
        import qrcode
    except ImportError:
        return 0, 0
    content = str(interpolate(el.get("content", ""), ctx["data"]))
    if not content:
        return 0, 0
    size = int(el.get("size", 80))
    qr = qrcode.QRCode(border=el.get("border", 1), box_size=2)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("1")
    img = img.resize((size, size), Image.NEAREST)
    ctx["canvas"].paste(img, (x, y))
    return size, size


def render_container(draw: ImageDraw.ImageDraw, el: dict, ctx: dict, x: int, y: int) -> tuple[int, int]:
    layout = el.get("layout", "vbox")
    gap = int(el.get("gap", 0))
    padding = el.get("padding", 0)
    if isinstance(padding, int):
        pt = pr = pb = pl = padding
    else:
        pt, pr, pb, pl = padding

    children = el.get("children", [])
    inner_x = x + pl
    inner_y = y + pt
    cursor_x = inner_x
    cursor_y = inner_y
    total_w = 0
    total_h = 0

    for child in children:
        if layout == "absolute":
            cx = inner_x + int(child.get("x", 0))
            cy = inner_y + int(child.get("y", 0))
            w, h = render_element(draw, child, ctx, cx, cy)
            total_w = max(total_w, int(child.get("x", 0)) + w)
            total_h = max(total_h, int(child.get("y", 0)) + h)
        elif layout == "hbox":
            cx = cursor_x + int(child.get("x", 0))
            cy = inner_y + int(child.get("y", 0))
            w, h = render_element(draw, child, ctx, cx, cy)
            cursor_x += w + gap
            total_w = cursor_x - inner_x - gap
            total_h = max(total_h, h + int(child.get("y", 0)))
        else:  # vbox
            cx = inner_x + int(child.get("x", 0))
            cy = cursor_y + int(child.get("y", 0))
            w, h = render_element(draw, child, ctx, cx, cy)
            cursor_y += h + gap
            total_w = max(total_w, w + int(child.get("x", 0)))
            total_h = cursor_y - inner_y - gap

    return total_w + pl + pr, total_h + pt + pb


_RENDERERS = {
    "text": render_text,
    "icon": render_icon,
    "image": render_image,
    "line": render_line,
    "rect": render_rect,
    "qrcode": render_qrcode,
    "container": render_container,
}


def render_element(
    draw: ImageDraw.ImageDraw,
    el: dict,
    ctx: dict,
    x: int | None = None,
    y: int | None = None,
) -> tuple[int, int]:
    if x is None:
        x = int(el.get("x", 0))
    if y is None:
        y = int(el.get("y", 0))
    fn = _RENDERERS.get(el.get("type", ""))
    if fn is None:
        return 0, 0
    return fn(draw, el, ctx, x, y)


# ─── Main entry ──────────────────────────────────────────────────────────────

def render(
    template: dict,
    data: dict | None = None,
    font_paths: list[Path] | None = None,
) -> Image.Image:
    """渲染模板，返回 1-bit PIL.Image。"""
    data = data or {}
    template = interpolate(template, data)  # 全树插值，简化下游
    meta = template.get("meta", {})
    width = int(meta.get("width", DEFAULT_WIDTH))
    height = int(meta.get("height", DEFAULT_HEIGHT))
    bg = _color_to_int(meta.get("background", "white"), default=255)

    canvas = Image.new("1", (width, height), bg)
    draw = ImageDraw.Draw(canvas)

    ctx = {
        "data": data,
        "canvas": canvas,
        "registry": FontRegistry(font_paths),
        "default_fonts": meta.get("default_fonts", ["unifont"]),
    }

    for el in template.get("elements", []):
        render_element(draw, el, ctx)

    return canvas


def render_to_base64(
    template: dict,
    data: dict | None = None,
    font_paths: list[Path] | None = None,
    fmt: str = "PNG",
) -> str:
    """渲染模板并返回 base64 编码字符串。"""
    img = render(template, data, font_paths)
    buf = BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()


def load_template(template: dict | str) -> dict:
    """支持传入 dict、JSON 字符串或文件路径。"""
    if isinstance(template, dict):
        return template
    if isinstance(template, str):
        # 优先尝试当作路径
        candidates = [Path(template), _BASE_DIR / "templates" / template,
                      _BASE_DIR / "templates" / f"{template}.json"]
        for p in candidates:
            if p.exists():
                return json.loads(p.read_text())
        # 当作 JSON 字符串
        return json.loads(template)
    raise TypeError(f"Unsupported template type: {type(template)}")
