__all__ = ["Geoposition"]

class Geoposition(object):

  def __init__(self, latitude=0, longitude=0, accuracy=0):
    self.latitude = latitude
    self.longitude = longitude
    self.accuracy = accuracy

