from PIL import Image

def limit_rgb(image_path, mask_path):
    image = Image.open(image_path)
    mask = Image.open(mask_path)

    pixels = image.load()
    mask_pixels = mask.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            if mask_pixels[x, y] == 255:
                min_val = min(r, g, b)
                max_val = max(r, g, b)

                if max_val - min_val >= 128:
                    r = max(min(r, 250), 90)
                    g = max(min(g, 250), 90)
                    b = max(min(b, 250), 90)
                else:
                    r = max(min(r, 250), 180)
                    g = max(min(g, 250), 180)
                    b = max(min(b, 250), 180)
            else:
                r = max(min(r, 220), 55)
                g = max(min(g, 220), 55)
                b = max(min(b, 220), 55)

            pixels[x, y] = (r, g, b)
            print(x,y, ' corrected')
    image.save("test_corrected.tga")
    image.show()

image_path = "test.tga"
mask_path = "testmask.tga"
limit_rgb(image_path, mask_path)