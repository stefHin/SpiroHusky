import logging

class YmlReader:
  def __init__(self, file_path):
    self.file_path = file_path

  def read(self):
    import yaml
    with open(self.file_path, 'r') as file:
      return yaml.safe_load(file)
        
  def read_section(self, section):
    config = self.read()
    return config.get(section, None)