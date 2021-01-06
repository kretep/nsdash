from PIL import Image

def draw_sunspots(context, x, y, w, h, data):
    img = Image.fromarray(data)
    region = (x, y, x + w, y + h)
    context.image.paste(img, region)