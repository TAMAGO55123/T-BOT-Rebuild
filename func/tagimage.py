from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from pathlib import Path
import asyncio

def find_best_font_size(text, font_path="NotoSansJP-Regular.otf", target_height=64, start_size=10, max_size=200):
    """
    text: 描画する文字列
    font_path: フォントファイルのパス
    target_height: 収めたい縦幅（今回は64px）
    start_size: 探索開始フォントサイズ
    max_size: 探索上限フォントサイズ
    """

    for size in range(start_size, max_size + 1):
        font = ImageFont.truetype(font_path, size)

        # 仮キャンバスで文字の高さを測る
        img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(img)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)

        text_height = bottom - top

        # 64px を超えたら直前のサイズが最適
        if text_height > target_height:
            return size - 1

    return max_size  # 上限まで収まる場合

async def create_tag_image(icon: BytesIO, tag_name: str) -> BytesIO:
    module_path = Path(__file__)
    font_file = module_path.parent.parent / "font" / "M_PLUS_Rounded_1c" / "MPLUSRounded1c-Medium.ttf"
    # print(font_file)
    text_size = find_best_font_size(text=tag_name, font_path=str(font_file), target_height=64)
    
    font = ImageFont.truetype(
        str(font_file),
        size=text_size - 4
    )

    text_left, text_top, text_right, text_bottom = ImageDraw.Draw(Image.new("RGB", (1,1))).textbbox((0, 0), tag_name, font=font)
    text_width = text_right - text_left

    padding = 10

    width = padding * 3 + 64 + text_width
    height = padding * 2 + 64

    image = Image.new(mode="RGBA", size=(width, height))
    draw = ImageDraw.Draw(image, mode="RGBA")

    draw.rounded_rectangle(
        (0, 0, image.width, image.height),
        10,
        "#333338"
    )

    icon_img = Image.open(icon)
    image.paste(icon_img, (padding, padding), icon_img)
    draw.text((padding * 2 + 64, padding + 2), tag_name, fill="#ffffff", font=font, anchor="lt")

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output

async def test():
    print("testing")
    pa = Path(__file__).parent
    with open(str(pa / "test" / "test.png"), mode="rb") as f:
        icon = BytesIO(f.read())
    img = await create_tag_image(
        icon=icon,
        tag_name="d.py"
    )
    with open(str(pa / "test" / "output.png"), mode="wb") as f:
        f.write(img.read())

if __name__ == "__main__":
    print("test")
    asyncio.run(test())
