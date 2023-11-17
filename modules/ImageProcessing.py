from PIL import Image, ImageChops
import numpy as np
import numexpr as ne


def srgb_to_linear(image_data=None):
    if image_data is not None:
        image_data = image_data / 255
        linear_image_data = ne.evaluate(
            'where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255')

        return linear_image_data

def linear_to_srgb(image_data=None):
    if image_data is not None:
        image_data = image_data / 255
        srgb_data = ne.evaluate('where(image_data <= 0.0031308, image_data * 12.92,(image_data ** (1.0 / 2.4)) * 1.055 - 0.055) * 255')

        return srgb_data

def calculate_luminance(image_data=None):
    if image_data is not None:
        luminance_data = np.dot(image_data, [0.299, 0.587, 0.114])

        return luminance_data


def clamp_brightness(image=None, brightness_limit=52):
    if image is not None:
        img = image.convert("HSV")
        img_data = np.array(img, dtype=np.float32)
        img_data[:, :, 2] = np.clip(np.power(img_data[:, :, 2], img_data[:, :, 2] / brightness_limit), 0, 255)
        result = ImageChops.multiply(image, Image.fromarray(img_data[:, :, 2].astype('uint8')).convert('RGB'))

        return result


def unclamp_brightness(image, brightness_limit):
    img = image.convert("HSV")
    img_data = np.array(img, dtype=np.float32)
    v_data = (255 - img_data[:, :, 2]) / (255 / brightness_limit)

    return ImageChops.add(image, Image.fromarray(v_data.astype('uint8')).convert('RGB'))


def correct_range(image_data, limit_values):
    image_data = np.clip(image_data, 1, 255)
    linear_rgb = srgb_to_linear(image_data)

    luminance_data = calculate_luminance(linear_rgb)
    luminance_data_corrected = np.clip(luminance_data, limit_values[0], limit_values[1])
    luminance_lightening_factor = np.clip(luminance_data_corrected - luminance_data, 0, 255)
    luminance_darkening_factor = np.clip(luminance_data - luminance_data_corrected, 0, 255)

    color_ratios = linear_rgb / np.maximum(luminance_data[:, :, np.newaxis], 1e-12)
    linear_rgb_lightened = linear_rgb + luminance_lightening_factor[:, :, np.newaxis] * color_ratios
    linear_rgb_corrected = np.clip(linear_rgb_lightened - luminance_darkening_factor[:, :, np.newaxis], 0, 255)

    image_data = linear_to_srgb(linear_rgb_corrected)

    return image_data


def verify_range(image_data, limit_values):
    linear_rgb = srgb_to_linear(image_data)
    luminance_data = calculate_luminance(linear_rgb)

    image_data[(luminance_data < limit_values[0])] = [0, 0, 255]
    image_data[(luminance_data > limit_values[1])] = [255, 0, 0]

    return image_data
