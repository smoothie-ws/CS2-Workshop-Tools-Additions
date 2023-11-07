import os

from PIL import Image
import numpy as np


class PBRMap:
    def __init__(self, albedo_path, metallic_path):
        self.albedo_path = albedo_path
        self.metallic_path = metallic_path
        self.albedo = Image.open(albedo_path)
        self.metallic = Image.open(metallic_path)

    def range_clamp(self):
        if self.albedo.mode == 'RGBA':
            alpha = self.albedo.split()[-1]
            albedo = self.albedo.convert("RGB")
        else:
            alpha = None
            albedo = self.albedo.convert("RGB")

        metallic = self.metallic.convert("RGB")
        albedo_data = np.array(albedo)
        metallic_data = np.array(metallic)

        albedo_data[(albedo_data <= 0)] = 1
        saturation_mask = (albedo_data.max(axis=2) // albedo_data.min(axis=2) < 2) & (metallic_data >= 128).any(axis=2)
        albedo_data = np.where(saturation_mask[..., None], np.clip(albedo_data, 180, 250), albedo_data)
        metallic_mask = (metallic_data < 128).any(axis=2)
        albedo_data = np.where(metallic_mask[..., None], np.clip(albedo_data, 55, 220), np.clip(albedo_data, 90, 250))

        self.albedo = Image.fromarray(albedo_data.astype('uint8'), mode="RGB")

        if alpha:
            self.albedo.putalpha(alpha)

    def save(self):
        filename, extension = os.path.splitext(self.albedo_path)
        albedo_corrected_path = filename + "_corrected" + extension
        self.albedo.save(albedo_corrected_path)
        return albedo_corrected_path
