#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把任意图片转成 WhatsApp 贴纸。
用法: 把图片丢进「1_把表情放这里」文件夹, 然后双击「点我转换.bat」。
"""

import io
import sys
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageSequence
except ImportError:
    print("\n[X] 缺少 Pillow 库。在命令行运行:  pip install pillow\n")
    input("按回车关闭...")
    sys.exit(1)

HERE = Path(__file__).resolve().parent
IN_DIR = HERE / "1_把表情放这里"
OUT_DIR = HERE / "2_转换结果"
WEBP_DIR = OUT_DIR / "贴纸图片"

OK_SUFFIX = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".jfif", ".apng"}

STATIC_LIMIT = 100 * 1024        # WhatsApp 静态贴纸上限
ANIM_LIMIT = 500 * 1024          # WhatsApp 动态贴纸上限
PACK_SIZE = 30                   # 一个贴纸包最多 30 张

# ↓↓↓ 改成你自己想要的, 会显示在 WhatsApp 的贴纸包信息里 ↓↓↓
PACK_TITLE = "我的微信表情"
PACK_AUTHOR = "your name"


def fit(im, size=512):
    """缩放并居中放到 size x size 的透明画布上。"""
    im = im.convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
    return canvas


def convert_one(src: Path, dst: Path) -> str:
    """转成 512x512 webp 并压到 WhatsApp 的体积限制内。返回 '静图'/'动图'。"""
    im = Image.open(src)
    animated = getattr(im, "n_frames", 1) > 1

    if not animated:
        canvas = fit(im)
        for q in (90, 80, 70, 60, 50, 40, 30, 20):
            canvas.save(dst, "WEBP", quality=q, method=6)
            if dst.stat().st_size <= STATIC_LIMIT:
                break
        return "静图"

    frames, durations = [], []
    for fr in ImageSequence.Iterator(im):
        frames.append(fit(fr.copy()))
        durations.append(max(fr.info.get("duration", 100), 20))

    for size in (512, 448, 384, 320):
        for step in (1, 2, 3, 4):
            fs = frames[::step]
            ds = [sum(durations[i:i + step]) for i in range(0, len(durations), step)]
            if size != 512:
                fs = [f.resize((size, size), Image.LANCZOS) for f in fs]
            for q in (80, 65, 50, 40, 30, 20):
                fs[0].save(dst, "WEBP", save_all=True, append_images=fs[1:],
                           duration=ds, loop=0, quality=q, method=4)
                if dst.stat().st_size <= ANIM_LIMIT:
                    return "动图"
    return "动图(偏大)"


def make_tray(src: Path) -> bytes:
    """贴纸包的封面小图: 96x96 png。"""
    im = Image.open(src)
    if getattr(im, "n_frames", 1) > 1:
        im.seek(0)
    tray = fit(im.copy(), 96)
    for_bytes = io.BytesIO()
    tray.save(for_bytes, "PNG", optimize=True)
    return for_bytes.getvalue()


def build_pack(webps, out_path: Path, title: str, author: str):
    """打包成 .wastickers, 某些贴纸 App 可以一键整包导入。"""
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("title.txt", title)
        zf.writestr("author.txt", author)
        zf.writestr("tray.png", make_tray(webps[0]))
        for w in webps:
            zf.write(w, w.name)


def main():
    print("=" * 56)
    print("  微信表情 -> WhatsApp 贴纸")
    print("=" * 56)

    IN_DIR.mkdir(exist_ok=True)

    files = sorted(p for p in IN_DIR.iterdir()
                   if p.is_file() and p.suffix.lower() in OK_SUFFIX)

    if not files:
        print(f"""
「1_把表情放这里」这个文件夹是空的。

  怎么把微信表情弄出来:
    1. 电脑版微信里, 把想要的表情发给「文件传输助手」
    2. 在聊天窗口里对着表情点右键 -> 另存为
       (也可以直接用鼠标把表情拖到文件夹里)
    3. 存进「1_把表情放这里」

  放好之后再双击一次「点我转换.bat」就行。

  支持 gif / png / jpg / webp, 动图静图都可以。
""")
        input("按回车关闭...")
        return

    WEBP_DIR.mkdir(parents=True, exist_ok=True)
    for old in WEBP_DIR.glob("*.webp"):
        old.unlink()

    print(f"\n找到 {len(files)} 张图, 开始转换...\n")
    done = []
    for i, src in enumerate(files, 1):
        dst = WEBP_DIR / f"{i:02d}.webp"
        try:
            kind = convert_one(src, dst)
            done.append(dst)
            print(f"  [{i:>2}] {src.name[:32]:<34} {kind}  {dst.stat().st_size / 1024:6.1f} KB")
        except Exception as e:
            print(f"  [{i:>2}] {src.name[:32]:<34} 跳过: {e}")

    if not done:
        print("\n一张都没转成功。可能这些文件不是真正的图片。")
        input("按回车关闭...")
        return

    packs = [done[i:i + PACK_SIZE] for i in range(0, len(done), PACK_SIZE)]
    print()
    for n, group in enumerate(packs, 1):
        if len(group) < 3:
            print(f"  第 {n} 包只有 {len(group)} 张, WhatsApp 要求至少 3 张, 跳过打包")
            continue
        name = PACK_TITLE if len(packs) == 1 else f"{PACK_TITLE}{n}"
        pack_path = OUT_DIR / f"{name}.wastickers"
        try:
            build_pack(group, pack_path, name, PACK_AUTHOR)
            print(f"  已打包: {pack_path.name}  ({len(group)} 张)")
        except Exception as e:
            print(f"  打包失败: {e}")

    print(f"""
{"=" * 56}
  转好了, 结果在「2_转换结果」文件夹里。

  两种导入方式, 哪个成就用哪个:

  方式一(省事): 把 .wastickers 文件传到手机, 用
    「Sticker Maker」App 打开它, 整包一次性导入。

  方式二(稳妥): 把「贴纸图片」文件夹里的 webp 传到手机,
    在 Sticker Maker 里新建贴纸包, 批量选中它们,
    再点 Add to WhatsApp。

  一个包最多 30 张、最少 3 张, 超了会自动分成好几包。
{"=" * 56}""")
    input("\n按回车关闭...")


if __name__ == "__main__":
    main()
