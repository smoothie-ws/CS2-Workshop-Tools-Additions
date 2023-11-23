import numpy as np
from PIL import Image


class TextureData(np.ndarray):
    def __new__(cls, input_image_data):
        image_data = np.asarray(input_image_data).view(cls)
        return image_data

    @property
    def srgb_to_linear(self) -> np.array:
        return ((self + 14.025) / 269.025) ** 2.4 * 255

    @property
    def linear_to_srgb(self) -> np.array:
        return ((self / 255) ** 0.4167) * 269.025 - 14.025

    @property
    def intensity_data(self) -> np.array:
        return np.max(self, axis=2)

    @property
    def luminance_data(self) -> np.array:
        return np.dot(self.srgb_to_linear, [0.299, 0.587, 0.114])

    def scale_intensity(self, intensity_limit=None) -> np.array:
        if intensity_limit is None:
            intensity_limit = 70
        intensity_data_scaled = np.interp(self.intensity_data, (intensity_limit * 0.9, intensity_limit * 1.1),
                                          (0, 255)) / 255

        return self.__image_data[:, :, :3] * intensity_data_scaled[:, :, np.newaxis]

    def counter_scale_intensity(self, intensity_limit=None) -> np.array:
        if intensity_limit is None:
            intensity_limit = 70

        intensity_data_counter_scaled = intensity_limit * (255 - self.intensity_data) / 255

        return np.clip(self.__image_data + intensity_data_counter_scaled[:, :, np.newaxis], 0, 255)

    def correct_range(self, limit_values=None) -> np.array:
        if limit_values is None:
            limit_values = [8, 235]

        luminance_data = self.luminance_data
        luminance_data_corrected = np.clip(luminance_data, limit_values[0], limit_values[1])
        luminance_lightening_factor = np.clip(luminance_data_corrected - luminance_data, 0, 255)
        luminance_darkening_factor = np.clip(luminance_data - luminance_data_corrected, 0, 255)

        linear_data = self.srgb_to_linear
        color_ratios = linear_data / np.maximum(luminance_data[:, :, np.newaxis], 1e-12)
        linear_rgb_lightened = linear_data + luminance_lightening_factor[:, :, np.newaxis] * color_ratios
        linear_rgb_corrected = np.clip(linear_rgb_lightened - luminance_darkening_factor[:, :, np.newaxis], 0, 255)

        self.__image_data = linear_rgb_corrected

        return self.linear_to_srgb

    def verify_range(self, limit_values=None) -> np.array:
        if limit_values is None:
            limit_values = [8, 235]

        luminance_data = self.luminance_data

        self.__image_data[(luminance_data < limit_values[0])] = [0, 0, 255]
        self.__image_data[(luminance_data > limit_values[1])] = [255, 0, 0]

        return self.__image_data


albedo = Image.open("test.tga")
albedo_data = TextureData(albedo)
print(albedo_data.correct_range())
