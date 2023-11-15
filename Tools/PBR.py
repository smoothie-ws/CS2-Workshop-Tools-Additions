import os
from PIL import Image, ImageChops
import numpy as np
import numexpr as ne


def calculate_luminance(image_data):
    image_data = image_data / 255
    linear_rgb = ne.evaluate(
        'where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255')

    return np.dot(linear_rgb, [0.299, 0.587, 0.114])


def clamp_metallic(image):
    img = image.convert("HSV")

    img_data = np.array(img, dtype=np.float32)

    img_data[:, :, 2] = np.clip(np.power(img_data[:, :, 2], img_data[:, :, 2] / 70), 0, 255)

    return ImageChops.multiply(image, Image.fromarray(img_data[:, :, 2].astype('uint8')).convert('RGB'))


def unclamp_metallic(image):
    img = image.convert("HSV")
    img_data = np.array(img, dtype=np.float32)
    v_data = (255 - img_data[:, :, 2]) / 3

    return ImageChops.add(image, Image.fromarray(v_data.astype('uint8')).convert('RGB'))


def correct_range(image_data):
    image_data = np.clip(image_data, 1, 255) / 255
    linear_rgb = ne.evaluate(
        'where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255')

    luminance_data = np.dot(linear_rgb, [0.299, 0.587, 0.114])
    luminance_data_corrected = np.clip(luminance_data, 9.2, 225)
    luminance_lightening_factor = np.clip(luminance_data_corrected - luminance_data, 0, 255)
    luminance_darkening_factor = np.clip(luminance_data - luminance_data_corrected, 0, 255)

    color_ratios = linear_rgb / np.maximum(luminance_data[:, :, np.newaxis], 1e-12)

    linear_rgb_lightened = linear_rgb + luminance_lightening_factor[:, :, np.newaxis] * color_ratios

    linear_rgb_corrected = np.clip(linear_rgb_lightened - luminance_darkening_factor[:, :, np.newaxis], 0, 255)

    linear_rgb_corrected /= 255
    image_data = np.where(linear_rgb_corrected <= 0.0031308, linear_rgb_corrected * 12.92,
                          (linear_rgb_corrected ** (1.0 / 2.4)) * 1.055 - 0.055) * 255

    return image_data


def verify_range(image_data):
    luminance_data = calculate_luminance(image_data)

    image_data[(luminance_data < 8)] = [0, 0, 255]
    image_data[(luminance_data > 235)] = [255, 0, 0]

    return image_data


class PBRSet:
    def __init__(self, albedo_path=None, metallic_path=None):
        if albedo_path is not None:
            self.albedo_image = Image.open(albedo_path)
            self.albedo_corrected = None
            self.albedo_verified = None

        if metallic_path is not None:
            self.metallic_image = (Image.open(metallic_path)).resize(
                (self.albedo_image.width, self.albedo_image.height))
            self.metallic_corrected = None

    def correct_albedo(self, mode, is_compensating=False):
        self.albedo_corrected = self.albedo_image.convert("RGB")
        image_data = np.array(self.albedo_corrected, dtype=np.float32)

        corrected_data = correct_range(image_data)
        self.albedo_corrected = Image.fromarray(corrected_data.astype('uint8'))

        if mode == "metallic":
            self.albedo_corrected = unclamp_metallic(self.albedo_corrected)

        if mode == "combined":
            albedo_metallic_corrected = unclamp_metallic(self.albedo_corrected)
            metallic_mask = self.metallic_image.split()[0]
            self.albedo_corrected.paste(albedo_metallic_corrected, (0, 0), metallic_mask)

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
        else:
            alpha = None

        if is_compensating and alpha:
            pass
            # factor = ImageChops.subtract(self.albedo_corrected, self.albedo_image)
            #
            # enhancer = ImageEnhance.Contrast(factor)
            # factor = enhancer.enhance(coefficient ** 5)
            #
            # compensation = ImageChops.subtract(self.ao_corrected, factor)
            # self.ao_corrected = compensation.convert("L")

        if alpha:
            self.albedo_corrected.putalpha(alpha)

    def verify_albedo(self, mode):
        self.albedo_verified = self.albedo_image.convert("RGB")
        image_data = None

        if mode == "nonmetallic":
            image_data = np.array(self.albedo_verified, dtype=np.float32)

        if mode == "metallic":
            image_data = np.array(clamp_metallic(self.albedo_verified), dtype=np.float32)

        if mode == "combined":
            image_adjusted = clamp_metallic(self.albedo_verified)
            metallic_mask = self.metallic_image.split()[0]
            albedo = self.albedo_image.convert("RGB")
            albedo.paste(image_adjusted, (0, 0), metallic_mask)
            image_data = np.array(albedo, dtype=np.float32)

        if image_data is not None:
            verified_data = verify_range(image_data)
            self.albedo_verified = Image.fromarray(verified_data.astype('uint8'))

            mismatched_pixels = ((verified_data == [255, 0, 0]) | (verified_data == [0, 0, 255])).all(axis=2).sum()
            return mismatched_pixels
        else:
            return 0

    def save(self, directory):
        folder = os.path.splitext(os.path.basename(directory))
        if self.albedo_corrected is not None:
            albedo_file_path = directory + "/" + folder[0] + "_corrected" + ".tga"
            self.albedo_corrected.save(albedo_file_path)
        if self.metallic_corrected is not None:
            metallic_file_path = directory + "/" + folder[0] + "_corrected" + ".tga"
            self.metallic_corrected.save(metallic_file_path)

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
