import io
import os

from PIL import Image


def imgs2pdf(images, save_file):
    if not os.path.exists(os.path.dirname(save_file)):
        os.makedirs(os.path.dirname(save_file))

    output = Image.open(io.BytesIO(images[0]))

    add_page = []

    for x in images:
        add_page.append(Image.open(io.BytesIO(x)))

    # 删掉已经有的第一页
    add_page.pop(0)

    output.save(save_file, "pdf", resolution=100.0, save_all=True, append_images=add_page)
