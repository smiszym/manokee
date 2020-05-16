class Meter:
    def __init__(self, channels=1):
        self.current_rms_dB = [-200] * channels
        self.current_peak_dB = [-200] * channels
