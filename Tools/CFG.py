import configparser


class CFG:
    def __init__(self, file):
        self.file = file
        config = configparser.ConfigParser()
        with open(self.file, 'r') as configfile:
            config.read_file(configfile)

        self.version = config.get('APPLICATION', 'version')

        self.finish_style = config.get('DEFAULTS', 'finish_style')
        self.mode = config.get('DEFAULTS', 'mode')
        self.is_saturation_considered = config.getboolean('DEFAULTS', 'is_saturation_considered')
        self.saturation_value = config.getfloat('DEFAULTS', 'saturation_value')
        self.is_compensating = config.getboolean('DEFAULTS', 'is_compensating')
        self.compensation_coefficient = config.getfloat('DEFAULTS', 'compensation_coefficient')
        self.nm_min = config.getint('DEFAULTS', 'nm_min')
        self.nm_max = config.getint('DEFAULTS', 'nm_max')
        self.m_min = config.getint('DEFAULTS', 'm_min')
        self.m_max = config.getint('DEFAULTS', 'm_max')
        self.mhs_min = config.getint('DEFAULTS', 'mhs_min')
        self.mhs_max = config.getint('DEFAULTS', 'mhs_max')

    def write(self):
        config = configparser.ConfigParser()

        config['DEFAULTS'] = {
            'finish_style': self.finish_style,
            'mode': self.mode,
            'is_saturation_considered': self.is_saturation_considered,
            'saturation_value': self.saturation_value,
            'is_compensating': self.is_compensating,
            'compensation_coefficient': self.compensation_coefficient,
            'nm_min': self.nm_min,
            'nm_max': self.nm_max,
            'm_min': self.m_min,
            'm_max': self.m_max,
            'mhs_min': self.mhs_min,
            'mhs_max': self.mhs_max
        }

        config['APPLICATION'] = {
            'version': self.version
        }

        with open(self.file, 'w') as configfile:
            config.write(configfile)
