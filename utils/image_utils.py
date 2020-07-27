import os
import sys
import base64
from io import BytesIO

from PIL import Image


def open_image_from_base64(img_str: str, save_path: str = None):
    """
    通过图片的 Base64 打开图片
    :param img_str: base64
    :param save_path: 保存的路径
    """
    byte_data = base64.b64decode(img_str)
    image_data = BytesIO(byte_data)
    img = Image.open(image_data)
    if save_path is not None:
        if img.mode == "P":
            img = img.convert("RGB")
        img.save(save_path)
    img.show()
    img.close()


def image_base64_to_pillow(img_str: str) -> Image:
    """
    通过图片的 Base64 返回 Pillow.Image 对象
    :param img_str: base64
    :return: 图片
    """
    byte_data = base64.b64decode(img_str)
    image_data = BytesIO(byte_data)
    img = Image.open(image_data)
    return img


def close_image_window():
    """
    关闭图片展示窗口
    """
    if sys.platform.find("darwin") >= 0:
        os.system("osascript -e 'quit app \"Preview\"'")
