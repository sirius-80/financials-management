import os


class Configuration:
    def __init__(self):
        self.data_directory = os.environ.get("DATA_DIRECTORY", "data")

    def get_file(self, filename):
        return os.path.join(self.data_directory, filename)