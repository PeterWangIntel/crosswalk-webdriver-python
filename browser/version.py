__all__ = ["kXwalkDriverVersion", \
           "kMinimumSupportedXwalkVersion", \
           "kMinimumSupportedXwalkBuildNo", \
           "GetMinimumSupportedXwalkVersion"]

kXwalkDriverVersion = "2.5"

kMinimumSupportedXwalkVersion = ['29', '0', '1545', '0']

kMinimumSupportedXwalkBuildNo = kMinimumSupportedXwalkVersion[2]

def GetMinimumSupportedXwalkVersion():
  return kMinimumSupportedXwalkVersion[0] + '.' \
    + kMinimumSupportedXwalkVersion[1] + '.' \
    + kMinimumSupportedXwalkVersion[2] + '.' \
    + kMinimumSupportedXwalkVersion[3]

if __name__ == "__main__":
  print GetMinimumSupportedXwalkVersion()

