from PIL import Image, ImageChops, ImageEnhance
import numpy as np
from .ImageProcessing import clamp_brightness, unclamp_brightness, correct_range, verify_range


class PBRSet:
    def __init__(self, albedo_image=None, metallic_image=None, roughness_image=None):
        self.albedo_image = None
        self.albedo_corrected = None
        self.albedo_verified = None
        self.metallic_image = None
        self.roughness_image = None
        self.roughness_corrected = None

        if albedo_image is not None:
            self.albedo_image = albedo_image

        if metallic_image is not None:
            self.metallic_image = metallic_image.resize(
                (self.albedo_image.width, self.albedo_image.height))

        if roughness_image is not None:
            self.roughness_image = roughness_image.resize(
                (self.albedo_image.width, self.albedo_image.height))

    def correct_albedo(self, mode, limit_values, is_compensating=False, coefficient=1.0):
        self.albedo_corrected = self.albedo_image.convert("RGB")
        image_data = np.array(self.albedo_corrected, dtype=np.float32)

        corrected_data = correct_range(image_data, limit_values)
        self.albedo_corrected = Image.fromarray(corrected_data.astype('uint8'))

        if mode == "metallic":
            self.albedo_corrected = unclamp_brightness(self.albedo_corrected, limit_values[2])

        if mode == "combined":
            albedo_metallic_corrected = unclamp_brightness(self.albedo_corrected, limit_values[2])

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

            roughness_compensated = ImageChops.subtract(self.roughness_image, lightening_factor.convert("RGB"))
            roughness_compensated = ImageChops.add(roughness_compensated, darkening_factor.convert("RGB"))

            self.roughness_corrected = roughness_compensated

    def verify_albedo(self, limit_values, mode):
        self.albedo_verified = self.albedo_image.convert("RGB")
        image_data = None

        if mode == "nonmetallic":
            image_data = np.array(self.albedo_verified, dtype=np.float32)

        if mode == "metallic":
            image_data = np.array(clamp_brightness(self.albedo_verified, limit_values[2]), dtype=np.float32)

        if mode == "combined":
            image_adjusted = clamp_brightness(self.albedo_verified, limit_values[2])

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

    def save(self, path, albedo_filename, roughness_filename):
        if self.albedo_corrected is not None:
            albedo_file_path = path + "/" + albedo_filename + "_corrected" + ".tga"
            self.albedo_corrected.save(albedo_file_path)

        if self.roughness_corrected is not None:
            roughness_file_path = path + "/" + roughness_filename + "_corrected" + ".tga"
            self.roughness_corrected.save(roughness_file_path)

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
