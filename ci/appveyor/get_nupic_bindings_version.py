import os

NUPIC = os.environ["NUPIC"]


def extractNupicBindingsVersion(requirementsFile):
  with open(requirementsFile, "r") as f:
    for line in f.readlines():
      if line.startswith("nupic.bindings"):
        return line.split("==").pop()


if __name__ == "__main__":
  requirementsFile = os.path.join(NUPIC, "external/common/requirements.txt")
  nupicBindingsVersion = extractNupicBindingsVersion(requirementsFile)
  print nupicBindingsVersion
