import os
from PIL import Image
import numpy as np


class RGB:
    min_nm = 55
    max_nm = 220
    min_m = 180
    max_m = 250
    min_m_hs = 90
    max_m_hs = 250


class PBRAlbedo:
    def __init__(self, albedo_path, metallic_path):
        self.albedo_path = albedo_path
        self.metallic_path = metallic_path
        self.albedo_image = Image.open(albedo_path)
        self.metallic_image = Image.open(metallic_path)
        self.albedo_corrected = self.albedo_image
        self.albedo_validated = self.albedo_image

    def clamp_rgb_range(self, mode, is_saturation=False, high_saturation_definition=None):

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            self.albedo_corrected = self.albedo_image.convert("RGB")
        else:
            alpha = None
            self.albedo_corrected = self.albedo_image.convert("RGB")

        albedo_data = np.array(self.albedo_corrected).astype(np.float32)

        if mode == "combined":

            metallic = self.metallic_image.convert("RGB")
            metallic_data = np.array(metallic)
            metallic_mask = (metallic_data < 128).any(axis=2)

            if is_saturation:
                if high_saturation_definition is not None:
                    max_albedo_value = albedo_data.max(axis=2)
                    saturation_mask = (
                            (max_albedo_value > 16) &
                            ((max_albedo_value - albedo_data.min(
                                axis=2)) / max_albedo_value < high_saturation_definition)
                    )

                    albedo_data = np.where(metallic_mask[..., None],
                                                np.clip(albedo_data, RGB.min_nm, RGB.max_nm),
                                                np.where(saturation_mask[..., None],
                                                         np.clip(albedo_data, RGB.min_m, RGB.max_m),
                                                         np.clip(albedo_data, RGB.min_m_hs, RGB.max_m_hs)))
            else:
                albedo_data = np.where(metallic_mask[..., None], np.clip(albedo_data, RGB.min_nm, RGB.max_nm),
                                            np.clip(albedo_data, RGB.min_m, RGB.max_m))

        elif mode == "metallic":
            if is_saturation:
                if high_saturation_definition is not None:
                    max_albedo_value = albedo_data.max(axis=2)
                    saturation_mask = (
                            (max_albedo_value > 16) &
                            ((max_albedo_value - albedo_data.min(
                                axis=2)) / max_albedo_value < high_saturation_definition)
                    )

                    albedo_data = np.where(saturation_mask[..., None],
                                                np.clip(albedo_data, RGB.min_m, RGB.max_m),
                                                np.clip(albedo_data, RGB.min_m_hs, RGB.max_m_hs))
            else:
                albedo_data = np.clip(albedo_data, RGB.min_m, RGB.max_m)

        elif mode == "nonmetallic":
            albedo_data = np.clip(albedo_data, RGB.min_nm, RGB.max_nm)

        self.albedo_corrected = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_corrected.putalpha(alpha)

    def validate_rgb_range(self, mode, is_saturation=False, high_saturation_definition=None):

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            self.albedo_validated = self.albedo_image.convert("RGB")
        else:
            alpha = None
            self.albedo_validated = self.albedo_image.convert("RGB")

        albedo_data = np.array(self.albedo_validated).astype(np.float32)

        if mode == "combined":

            metallic = self.metallic_image.convert("RGB")
            metallic_data = np.array(metallic)
            metallic_mask = (metallic_data < 128).any(axis=2)

            if is_saturation:
                if high_saturation_definition is not None:
                    max_albedo_value = albedo_data.max(axis=2)
                    saturation_mask = (
                            (max_albedo_value > 16) &
                            ((max_albedo_value - albedo_data.min(
                                axis=2)) / max_albedo_value < high_saturation_definition)
                    )

                    albedo_data = np.where((saturation_mask[..., None] & metallic_mask[..., None]) & (albedo_data > RGB.max_nm).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                    albedo_data = np.where((saturation_mask[..., None] & metallic_mask[..., None]) & (albedo_data < RGB.min_nm).all(axis=-1)[..., None],(0, 0, 255), albedo_data)
                    albedo_data = np.where(saturation_mask[..., None] & ~(metallic_mask[..., None]) & (albedo_data > RGB.max_m).all(axis=-1)[..., None],(255, 0, 0), albedo_data)
                    albedo_data = np.where(saturation_mask[..., None] & ~(metallic_mask[..., None]) & (albedo_data < RGB.min_m).all(axis=-1)[..., None],(0, 0, 255), albedo_data)
                    albedo_data = np.where((~saturation_mask[..., None] & metallic_mask[..., None]) & (albedo_data > RGB.max_nm).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                    albedo_data = np.where((~saturation_mask[..., None] & metallic_mask[..., None]) & (albedo_data < RGB.min_nm).all(axis=-1)[..., None], (0, 0, 255), albedo_data)
                    albedo_data = np.where(~saturation_mask[..., None] & ~(metallic_mask[..., None]) & (albedo_data > RGB.max_m_hs).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                    albedo_data = np.where(~saturation_mask[..., None] & ~(metallic_mask[..., None]) & (albedo_data < RGB.min_m_hs).all(axis=-1)[..., None], (0, 0, 255), albedo_data)
            else:
                albedo_data = np.where((metallic_mask[..., None]) & (albedo_data > RGB.max_nm).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                albedo_data = np.where((metallic_mask[..., None]) & (albedo_data < RGB.min_nm).all(axis=-1)[..., None], (0, 0, 255), albedo_data)
                albedo_data = np.where(~(metallic_mask[..., None]) & (albedo_data > RGB.max_m).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                albedo_data = np.where(~(metallic_mask[..., None]) & (albedo_data < RGB.min_m).all(axis=-1)[..., None], (0, 0, 255), albedo_data)

        elif mode == "metallic":
            if is_saturation:
                if high_saturation_definition is not None:
                    max_albedo_value = albedo_data.max(axis=2)
                    saturation_mask = (
                            (max_albedo_value > 16) &
                            ((max_albedo_value - albedo_data.min(
                                axis=2)) / max_albedo_value < high_saturation_definition)
                    )

                    albedo_data = np.where(saturation_mask[..., None] & (albedo_data > RGB.max_m).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                    albedo_data = np.where(saturation_mask[..., None] & (albedo_data < RGB.min_m).all(axis=-1)[..., None], (0, 0, 255), albedo_data)
                    albedo_data = np.where(~(saturation_mask[..., None]) & (albedo_data > RGB.max_m_hs).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                    albedo_data = np.where(~(saturation_mask[..., None]) & (albedo_data < RGB.min_m_hs).all(axis=-1)[..., None], (0, 0, 255), albedo_data)
            else:
                albedo_data = np.where((albedo_data > RGB.max_m).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
                albedo_data = np.where((albedo_data < RGB.min_m).all(axis=-1)[..., None], (0, 0, 255), albedo_data)

        elif mode == "nonmetallic":
            albedo_data = np.where((albedo_data > RGB.max_nm).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
            albedo_data = np.where((albedo_data < RGB.min_nm).all(axis=-1)[..., None], (0, 0, 255), albedo_data)

        mismatched_pixels = ((albedo_data == [255, 0, 0]) | (albedo_data == [0, 0, 255])).all(axis=2).sum()

        self.albedo_validated = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_validated.putalpha(alpha)

        return mismatched_pixels

    def save(self, map_type):
        filename, extension = os.path.splitext(self.albedo_path)

        if map_type == "corrected":
            file_path = filename + "_corrected" + extension
            self.albedo_corrected.save(file_path)
        if map_type == "validated":
            file_path = filename + "_validated" + extension
            self.albedo_validated.save(file_path)

        return file_path

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
