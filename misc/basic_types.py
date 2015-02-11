__all__ = ["WebPoint", "WebSize", "WebRect"]

class WebPoint(object):

  def __init__(self, x=0, y=0):
    self.x = x
    self.y = y

  def Offset(self, x, y):
    self.x = self.x + x
    self.y = self.y + y
    return
    
  def Update(self, other):
    self.x = other.x
    self.y = other.y
    return

class WebSize(object):

  def __init__(self, width=0, height=0):
    self.width = width
    self.height = height

class WebRect(object):

  def __init__(self, *args):
    if len(args) == 2:
      self.__initFromTwoParams(*args)
    elif len(args) == 4:
      self.__initFromFourParams(*args)
    else:
      self.origin = WebPoint(0, 0)
      self.size = WebSize(0, 0)

  def __initFromFourParams(self, x, y, width, height):
    self.origin = WebPoint(x, y)
    self.size = WebSize(width, height)

  def __initFromTwoParams(self, origin, size):
    self.origin = origin
    self.size = size

  def X(self):
    return self.origin.x

  def Y(self):
    return self.origin.y

  def Width(self):
    return self.size.width

  def Height(self):
    return self.size.height

if __name__ == "__main__":
  test = WebPoint(34, 65)
  print "%d, %d" % (test.x, test.y)
  test = WebSize(143, 14)
  print "%d, %d" % (test.width, test.height)
  test = WebRect()
  print "%d, %d, %d, %d" % (test.origin.x, test.origin.y, test.size.width, test.size.height)
  test = WebRect(3, 5, 34, 34)
  print "%d, %d, %d, %d" % (test.origin.x, test.origin.y, test.size.width, test.size.height)
  test = WebRect(WebPoint(34, 55), WebSize(34, 141))
  print "%d, %d, %d, %d" % (test.origin.x, test.origin.y, test.size.width, test.size.height)
  
