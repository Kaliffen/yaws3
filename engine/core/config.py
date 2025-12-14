class Config:
    def __init__(self, settings=None):
        self.settings = settings or {}

    def get(self, key, default=None):
        return self.settings.get(key, default)
