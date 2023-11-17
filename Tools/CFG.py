import configparser


class CFG:
    def __init__(self, file):
        self.file = file
        config = configparser.ConfigParser()

        try:
            with open(self.file, 'r') as configfile:
                config.read_file(configfile)

            self.version = config.get('APPLICATION', 'version')
            self.finish_style = config.get('DEFAULTS', 'finish_style')
            self.mode = config.get('DEFAULTS', 'mode')
            self.is_compensating = config.getboolean('DEFAULTS', 'is_compensating')
            self.compensation_coefficient = config.getfloat('DEFAULTS', 'compensation_coefficient')
            self.l_min = config.getint('DEFAULTS', 'luminance_min')
            self.l_max = config.getint('DEFAULTS', 'luminance_max')
            self.b_limit = config.getint('DEFAULTS', 'brightness_limit')

        except Exception:
            self.version = "0.0"
            self.finish_style = "Gunsmith"
            self.mode = "combined"
            self.is_compensating = True
            self.compensation_coefficient = 1.0
            self.l_min = 8
            self.l_max = 235
            self.b_limit = 70

    def write(self):
        config = configparser.ConfigParser()

        config['DEFAULTS'] = {
            'finish_style': self.finish_style,
            'mode': self.mode,
            'is_compensating': self.is_compensating,
            'compensation_coefficient': self.compensation_coefficient,
            'luminance_min': self.l_min,
            'luminance_max': self.l_max,
            'brightness_limit': self.b_limit,
        }

        config['APPLICATION'] = {
            'version': self.version
        }

        with open(self.file, 'w') as configfile:
            config.write(configfile)
