import os
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import numexpr as ne


def luminance(image_data):
    linear = ne.evaluate(
        'where(image_data <= 0.04045, image_data / 12.92, ((image_data + 0.055) / 1.055) ** 2.4) * 255'
    )

    luminance_image = Image.fromarray(linear.astype('uint8')).convert('L')
    return np.array(luminance_image, dtype=np.float32)


def clip_metallic(image):
    img = image.convert("HSV")
    v = img.split()[-1]

    v_data = np.array(v, dtype=np.float32)
    v_data = np.power(v_data, v_data / 70)
    v_data = np.clip(v_data, 0, 255)

    return ImageChops.multiply(image, Image.fromarray(v_data.astype('uint8')).convert('RGB'))


def verify_range(image_data):
    luminance_data = luminance(image_data / 255.0)
    image_data[(luminance_data < 7)] = [0, 0, 255]
    image_data[(luminance_data > 235)] = [255, 0, 0]

    return image_data


class RGB:
    def __init__(self, range=None):
        if range is None:
            range = [55, 220, 180, 250, 90, 250]

        self.min_nm = range[0]
        self.max_nm = range[1]
        self.min_m = range[2]
        self.max_m = range[3]
        self.min_m_hs = range[4]
        self.max_m_hs = range[5]


class PBRAlbedo:
    def __init__(self, RGB_range, albedo_path=None, metallic_path=None, ao_path=None):
        self.RGB = RGB(RGB_range)
        if albedo_path is not None:
            self.albedo_path = albedo_path
            self.albedo_image = Image.open(albedo_path)
            self.albedo_corrected = self.albedo_image.convert("RGB")
            self.albedo_validated = self.albedo_image.convert("RGB")

        if metallic_path is not None:
            self.metallic_path = metallic_path
            self.metallic_image = Image.open(metallic_path)

        if ao_path is not None:
            self.ao_path = ao_path
            self.ao_image = Image.open(ao_path).convert(self.albedo_image.mode)
            self.ao_corrected = self.ao_image

    def clamp_rgb_range(self, mode, is_compensating=False, coefficient=1.0, is_saturation=False,
                        high_saturation_definition=None):

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            self.albedo_corrected = self.albedo_image.convert("RGB")
        else:
            alpha = None
            self.albedo_corrected = self.albedo_image.convert("RGB")

        # albedo_data = np.array(self.albedo_corrected).astype(np.float32)
        #
        # if mode == "combined":
        #
        #     metallic = self.metallic_image.convert("RGB")
        #     metallic_data = np.array(metallic)
        #     metallic_mask = (metallic_data < 128).any(axis=2)
        #
        #     if is_saturation:
        #         if high_saturation_definition is not None:
        #             max_albedo_value = albedo_data.max(axis=2)
        #             saturation_mask = (
        #                     (max_albedo_value > 16) &
        #                     ((max_albedo_value - albedo_data.min(axis=2)) / max_albedo_value < high_saturation_definition)
        #             )
        #
        #             albedo_data = np.where(metallic_mask[..., None],
        #                                    np.clip(albedo_data, self.RGB.min_nm, self.RGB.max_nm),
        #                                    np.where(saturation_mask[..., None],
        #                                             np.clip(albedo_data, self.RGB.min_m, self.RGB.max_m),
        #                                             np.clip(albedo_data, self.RGB.min_m_hs, self.RGB.max_m_hs)))
        #     else:
        #         albedo_data = np.where(metallic_mask[..., None], np.clip(albedo_data, self.RGB.min_nm, self.RGB.max_nm),
        #                                np.clip(albedo_data, self.RGB.min_m, self.RGB.max_m))
        #
        # elif mode == "metallic":
        #     if is_saturation:
        #         if high_saturation_definition is not None:
        #             max_albedo_value = albedo_data.max(axis=2)
        #             saturation_mask = (
        #                     (max_albedo_value > 16) &
        #                     ((max_albedo_value - albedo_data.min(
        #                         axis=2)) / max_albedo_value < high_saturation_definition)
        #             )
        #
        #             albedo_data = np.where(saturation_mask[..., None],
        #                                    np.clip(albedo_data, self.RGB.min_m, self.RGB.max_m),
        #                                    np.clip(albedo_data, self.RGB.min_m_hs, self.RGB.max_m_hs))
        #     else:
        #         albedo_data = np.clip(albedo_data, self.RGB.min_m, self.RGB.max_m)
        #
        # elif mode == "nonmetallic":
        #     albedo_data = np.clip(albedo_data, self.RGB.min_nm, self.RGB.max_nm)

        # self.albedo_corrected = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        # self.albedo_corrected = srgb_to_linear(self.albedo_image).convert("L")

        if alpha:
            self.albedo_corrected.putalpha(alpha)

        if is_compensating:
            factor = ImageChops.subtract(self.albedo_corrected, self.albedo_image)

            enhancer = ImageEnhance.Contrast(factor)
            factor = enhancer.enhance(coefficient ** 5)

            compensation = ImageChops.subtract(self.ao_corrected, factor)
            self.ao_corrected = compensation.convert("L")

    def validate_rgb_range(self, mode):
        image_data = None
        if mode == "nonmetallic":
            image_data = np.array(self.albedo_validated, dtype=np.float32)

        if mode == "metallic":
            image_data = np.array(clip_metallic(self.albedo_validated), dtype=np.float32)

        if mode == "combined":
            image_adjusted = clip_metallic(self.albedo_validated)
            metallic_mask = self.metallic_image.split()[0]
            albedo = self.albedo_image.convert("RGB")
            albedo.paste(image_adjusted, (0, 0), metallic_mask)
            image_data = np.array(albedo, dtype=np.float32)

        if image_data is not None:
            verified_data = verify_range(image_data)
            self.albedo_validated = Image.fromarray(verified_data.astype('uint8'))

            mismatched_pixels = ((verified_data == [255, 0, 0]) | (verified_data == [0, 0, 255])).all(axis=2).sum()
            return mismatched_pixels

        else:
            return 0


    def save(self, directory):
        if self.albedo_corrected is not None:
            albedo_filename, albedo_extension = os.path.splitext(os.path.basename(self.albedo_path))
            albedo_file_path = directory + "/" + albedo_filename + "_corrected" + albedo_extension
            self.albedo_corrected.save(albedo_file_path)

        if self.ao_corrected is not None:
            ao_filename, ao_extension = os.path.splitext(os.path.basename(self.ao_path))
            ao_file_path = directory + "/" + ao_filename + "_corrected" + ao_extension
            self.ao_corrected.save(ao_file_path)

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
