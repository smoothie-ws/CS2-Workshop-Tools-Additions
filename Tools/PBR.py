import os
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import numexpr as ne


def calculate_luminance(image_data):
    image_data = image_data / 255
    linear_rgb = ne.evaluate('where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255')

    return np.dot(linear_rgb, [0.299, 0.587, 0.114])


def clamp_metallic(image, brightness_limit):
    img = image.convert("HSV")

    img_data = np.array(img, dtype=np.float32)

    img_data[:, :, 2] = np.clip(np.power(img_data[:, :, 2], img_data[:, :, 2] / brightness_limit), 0, 255)

    return ImageChops.multiply(image, Image.fromarray(img_data[:, :, 2].astype('uint8')).convert('RGB'))


def unclamp_metallic(image, brightness_limit):
    img = image.convert("HSV")
    img_data = np.array(img, dtype=np.float32)
    v_data = (255 - img_data[:, :, 2]) / (255 / brightness_limit)

    return ImageChops.add(image, Image.fromarray(v_data.astype('uint8')).convert('RGB'))


def correct_range(image_data, limit_values):
    image_data = np.clip(image_data, 1, 255) / 255
    linear_rgb = ne.evaluate(
        'where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255')

    luminance_data = np.dot(linear_rgb, [0.299, 0.587, 0.114])
    luminance_data_corrected = np.clip(luminance_data, limit_values[0], limit_values[1])
    luminance_lightening_factor = np.clip(luminance_data_corrected - luminance_data, 0, 255)
    luminance_darkening_factor = np.clip(luminance_data - luminance_data_corrected, 0, 255)

    color_ratios = linear_rgb / np.maximum(luminance_data[:, :, np.newaxis], 1e-12)

    linear_rgb_lightened = linear_rgb + luminance_lightening_factor[:, :, np.newaxis] * color_ratios

    linear_rgb_corrected = np.clip(linear_rgb_lightened - luminance_darkening_factor[:, :, np.newaxis], 0, 255)

    linear_rgb_corrected /= 255
    image_data = np.where(linear_rgb_corrected <= 0.0031308, linear_rgb_corrected * 12.92,
                          (linear_rgb_corrected ** (1.0 / 2.4)) * 1.055 - 0.055) * 255

    return image_data


def verify_range(image_data, limit_values):
    luminance_data = calculate_luminance(image_data)

    image_data[(luminance_data < limit_values[0])] = [0, 0, 255]
    image_data[(luminance_data > limit_values[1])] = [255, 0, 0]

    return image_data


class PBRSet:
    def __init__(self, albedo_image=None, metallic_image=None):
        if albedo_image is not None:
            self.albedo_image = albedo_image
            self.albedo_corrected = None
            self.albedo_verified = None

        if metallic_image is not None:
            self.metallic_image = metallic_image.resize(
                (self.albedo_image.width, self.albedo_image.height))

    def correct_albedo(self, mode, limit_values, is_compensating=False, coefficient=1.0):
        metallic_mask = None

        self.albedo_corrected = self.albedo_image.convert("RGB")
        image_data = np.array(self.albedo_corrected, dtype=np.float32)

        corrected_data = correct_range(image_data, limit_values)
        self.albedo_corrected = Image.fromarray(corrected_data.astype('uint8'))

        if mode == "metallic":
            self.albedo_corrected = unclamp_metallic(self.albedo_corrected, limit_values[2])

        if mode == "combined":
            albedo_metallic_corrected = unclamp_metallic(self.albedo_corrected, limit_values[2])

            if self.metallic_image.mode != 'P':
                metallic_mask = self.metallic_image.split()[0]
            else:
                metallic_mask = self.metallic_image

            metallic_mask = metallic_mask.convert('L')

            self.albedo_corrected.paste(albedo_metallic_corrected, mask=metallic_mask)

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
        else:
            alpha = None

        if alpha:
            self.albedo_corrected.putalpha(alpha)

        if is_compensating and mode in ["metallic", "combined"]:
            lightening_factor = ImageChops.subtract(self.albedo_corrected, self.albedo_image).convert("L")
            enhancer = ImageEnhance.Contrast(lightening_factor)
            lightening_factor = enhancer.enhance(coefficient ** 3.14)

            darkening_factor = ImageChops.subtract(self.albedo_image, self.albedo_corrected).convert("L")
            enhancer = ImageEnhance.Contrast(darkening_factor)
            darkening_factor = enhancer.enhance(coefficient ** 3.14)

            if not alpha:
                alpha = Image.new('L', self.albedo_corrected.size, color=127)

            alpha_compensated = ImageChops.add(alpha, lightening_factor)
            alpha_compensated = ImageChops.subtract(alpha_compensated, darkening_factor)

            if mode == "metallic":
                self.albedo_corrected.putalpha(alpha_compensated)

            if mode == "combined":
                alpha.paste(alpha_compensated, (0, 0), metallic_mask)
                self.albedo_corrected.putalpha(alpha)

    def verify_albedo(self, limit_values, mode):
        self.albedo_verified = self.albedo_image.convert("RGB")
        image_data = None

        if mode == "nonmetallic":
            image_data = np.array(self.albedo_verified, dtype=np.float32)

        if mode == "metallic":
            image_data = np.array(clamp_metallic(self.albedo_verified, limit_values[2]), dtype=np.float32)

        if mode == "combined":
            image_adjusted = clamp_metallic(self.albedo_verified, limit_values[2])

            if self.metallic_image.mode != 'P':
                metallic_mask = self.metallic_image.split()[0]
            else:
                metallic_mask = self.metallic_image

            metallic_mask = metallic_mask.convert('L')

            albedo = self.albedo_image.convert("RGB")
            albedo.paste(image_adjusted, mask=metallic_mask)
            image_data = np.array(albedo, dtype=np.float32)

        if image_data is not None:
            verified_data = verify_range(image_data, limit_values)
            self.albedo_verified = Image.fromarray(verified_data.astype('uint8'))

            mismatched_pixels = ((verified_data == [255, 0, 0]) | (verified_data == [0, 0, 255])).all(axis=2).sum()
            return mismatched_pixels
        else:
            return 0

    def save(self, path, filename):
        if self.albedo_corrected is not None:
            albedo_file_path = path + "/" + filename + "_corrected" + ".tga"
            self.albedo_corrected.save(albedo_file_path)

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
