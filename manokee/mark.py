class Mark:
    def __init__(self, *, beat: int):
        self.beat: int = beat

    @classmethod
    def from_str(cls, s):
        if s.startswith("beat "):
            return cls(beat=int(s[5:]))
        else:
            raise ValueError

    def __str__(self):
        return f"beat {self.beat}"
