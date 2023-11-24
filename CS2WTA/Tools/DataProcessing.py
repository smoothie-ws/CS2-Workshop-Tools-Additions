import numpy as np
from PIL import Image


class TextureData:
    def __init__(self, image):
        self.__data = np.array(image, dtype=np.float32)

    @property
    def linear(self):
        return ((self.__data + 14.025) / 269.025) ** 2.4 * 255

    @property
    def srgb(self):
        return ((self.__data / 255) ** 0.4167) * 269.025 - 14.025

    @property
    def intensity(self):
        return np.max(self.__data, axis=2)

    @property
    def luminance(self):
        return np.dot(self.linear, [0.299, 0.587, 0.114])


class TextureDataProcessing:
    @staticmethod
    def scale_intensity(image, intensity_limit=None):
        if intensity_limit is None:
            intensity_limit = 70
        texture_data = TextureData(image)
        intensity_data_scaled = np.interp(texture_data.intensity, (intensity_limit * 0.9, intensity_limit * 1.1),
                                          (0, 255)) / 255

        self.image_data = self.image_data[:, :, :3] * intensity_data_scaled[:, :, np.newaxis]


albedo = Image.open("test.tga").convert('RGB')
Image.fromarray(TextureData(albedo).luminance.astype('uint8')).show()
