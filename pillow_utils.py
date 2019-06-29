from io import BytesIO


def convert_to_buffer(image, image_format='png', **kwargs):
    out = BytesIO()
    image.save(out, image_format, **kwargs)
    out.seek(0)
    return out
