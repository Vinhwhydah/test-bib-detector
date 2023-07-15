from PIL import ImageDraw

def draw_boxes(image, bounds, color = 'green'):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)
    width, height = image.size

    for bound in bounds:
        points = sum(list(map(lambda v: [v.x, v.y], bound.vertices)), []) \
            + sum(list(map(lambda v: [v.x * width, v.y * height], bound.normalized_vertices)), [])
        
        draw.polygon(
            points,
            None,
            color,
            4
        )
    return image