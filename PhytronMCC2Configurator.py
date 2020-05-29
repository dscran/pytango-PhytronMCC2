from tango import DeviceProxy

class PhytronMCC2Configurator():
    
    default_config = {
        1: 0,
        2: 1,
        3: 1,
        4: 400,
        7: 100000,
        8: 4000,
        9: 4000,
        10: 400,
        11: 0,
        12: 0,
        13: 20,
        14: 4000,
        15: 4000,
        16: 20,
        17: 0,
        19: 0,
        20: 0,
        21: 0,
        22: 0,
        23: 0,
        24: 0,
        25: 0,
        27: 0,
        34: 0,
        35: 10,
        36: 0,
        38: 0,
        39: 0,
        40: 2,
        41: 6,
        42: 10,
        43: 20,
        45: 4,
        46: 1,
        47: 1,
    }
    
    def __init__(self, device):
        self.proxy = DeviceProxy(device)
        self.current_config = {}

    def read_current_config(self):
        self.current_config = {}
        import io
        raw_conf = d.dump_config()
        buf = io.StringIO(raw_conf)
        for line in buf:
            [param, value] = line.strip().split(':')
            self.current_config[int(param.replace('P', ''))] = float(value.strip())
        
    def compare_configs(self, read_current_config=True):
        if read_current_config:
            self.read_current_config()
        print('Param. \t default \t current \t compare')
        print('===================================================')
        for param, value in self.default_config.items():
            curr_value = self.current_config[param]
            print('P{:02d}: {:10.2f} \t {:10.2f} \t {:s}'.format(param,
                                                                 value,
                                                                 curr_value,
                                                                 'same' if curr_value == value else 'changed'))
            
    def reset_to_default(self):
        for param, value in self.default_config.items():
            cmd = 'P{:02d}S{:f}'.format(param, value)
            print(cmd)
            res = self.proxy.send_cmd(cmd)
            