import os
from PIL import Image
import numpy as np


class PBRMap:
    def __init__(self, albedo_path, metallic_path):
        self.albedo_path = albedo_path
        self.metallic_path = metallic_path
        self.albedo_image = Image.open(self.albedo_path)
        self.metallic_image = Image.open(self.metallic_path)
        self.minRGB_nm = 55
        self.maxRGB_nm = 220
        self.minRGB_m = 180
        self.maxRGB_m = 250
        self.minRGB_m_hs = 90
        self.maxRGB_m_hs = 250

    # Clamping per-pixel RGB values taking both metallic and nonmetalic parts into account.
    def full_range_clamp(self, is_saturation_considered, high_saturation_definition):

        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            albedo = self.albedo_image.convert("RGB")
        else:
            alpha = None
            albedo = self.albedo_image.convert("RGB")

        metallic = self.metallic_image.convert("RGB")

        albedo_data = np.array(albedo)
        metallic_data = np.array(metallic)

        if is_saturation_considered:
            albedo_data[(albedo_data <= 0)] = 1
            max_albedo = albedo_data.max(axis=2)
            saturation_mask = (
                    (max_albedo > 16) &
                    ((max_albedo - albedo_data.min(axis=2)) / max_albedo < high_saturation_definition) &
                    (metallic_data >= 128).any(axis=2)
            )

            albedo_data = np.where(saturation_mask[..., None], np.clip(albedo_data, self.minRGB_m, self.maxRGB_m), albedo_data)

        metallic_mask = (metallic_data < 128).any(axis=2)
        albedo_data = np.where(metallic_mask[..., None], np.clip(albedo_data, self.minRGB_nm, self.maxRGB_nm), np.clip(albedo_data, self.minRGB_m_hs, self.maxRGB_m_hs))

        self.albedo_image = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_image.putalpha(alpha)

    # Clamping per-pixel RGB values considering that the entire weapon finish is non-metallic.
    def nonmetallic_range_clamp(self):
        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            albedo = self.albedo_image.convert("RGB")
        else:
            alpha = None
            albedo = self.albedo_image.convert("RGB")

        albedo_data = np.array(albedo)
        albedo_data = np.clip(albedo_data, self.minRGB_nm, self.maxRGB_nm)
        self.albedo_image = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_image.putalpha(alpha)

    # Clamping per-pixel RGB values considering that the entire weapon finish is metallic.
    def metallic_range_clamp(self, is_saturation_considered, high_saturation_definition):
        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            albedo = self.albedo_image.convert("RGB")
        else:
            alpha = None
            albedo = self.albedo_image.convert("RGB")

        metallic = self.metallic_image.convert("RGB")

        albedo_data = np.array(albedo)
        metallic_data = np.array(metallic)

        if is_saturation_considered:
            albedo_data[(albedo_data <= 0)] = 1
            max_albedo = albedo_data.max(axis=2)
            saturation_mask = (
                    (max_albedo > 16) &
                    ((max_albedo - albedo_data.min(axis=2)) / max_albedo < high_saturation_definition)
            )

            albedo_data = np.where(saturation_mask[..., None], np.clip(albedo_data, self.minRGB_m, self.maxRGB_m),
                                   np.clip(albedo_data, self.minRGB_m_hs, self.maxRGB_m_hs))
        else:
            albedo_data = np.clip(albedo_data,self.minRGB_m, self.maxRGB_m)

        self.albedo_image = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_image.putalpha(alpha)

    # Validating if per-pixel RGB values match the correct range
    # considering that the entire weapon finish is non-metallic.
    def nonmetallic_range_validate(self):
        if self.albedo_image.mode == 'RGBA':
            alpha = self.albedo_image.split()[-1]
            albedo = self.albedo_image.convert("RGB")
        else:
            alpha = None
            albedo = self.albedo_image.convert("RGB")

        albedo_data = np.array(albedo)

        albedo_data = np.where((albedo_data > self.maxRGB_nm).all(axis=-1)[..., None], (255, 0, 0), albedo_data)
        albedo_data = np.where((albedo_data < self.minRGB_nm).all(axis=-1)[..., None], (0, 0, 255), albedo_data)

        self.albedo_image = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo_image.putalpha(alpha)

        return self.albedo_image

    # Saving the corrected albedo map to a new file.
    def save(self):
        filename, extension = os.path.splitext(self.albedo_path)
        albedo_corrected_path = filename + "_corrected" + extension
        self.albedo_image.save(albedo_corrected_path)
        return albedo_corrected_path

    def size(self):
        return self.albedo_image.width * self.albedo_image.height
