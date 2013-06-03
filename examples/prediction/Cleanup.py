from optparse import OptionParser
import os
import sys
import shutil
from nupic.frameworks.prediction import utils

def cleanup(experiments=[], types=[]):
  """Remove items listed in types from the specified experiments."""

  if len(experiments)==0:
    experiments = ['experiments']
  else:
    for experiment in experiments[:]:
      if not os.path.exists(experiment):
        print "Experiment or directory \"%s\" was not found." % experiment
        experiments.remove(experiment)

  counts = {}
  for item in types:
    counts[item] = 0

  for experiment in experiments:

    for dirpath, dirnames, filenames in os.walk(experiment):
      for d in dirnames[:]:
        if d.startswith('.'):
          # Don't enter directories that begin with '.' example .svn
          dirnames.remove(d)
        elif d in types:
          # Remove this directory
          counts[d] += 1
          shutil.rmtree(os.path.join(dirpath, d))
          dirnames.remove(d)
      for f in filenames:
        if f in types:
          counts[f] += 1
          os.remove(os.path.join(dirpath, f))

  if sum(counts.values()) == 0:
    print "Found nothing to clean up."
    return

  for item in counts:
    if counts[item] == 1:
      if os.path.splitext(item)[1]:
        print "Removed 1 \"%s\" file." % item
      else:
        print "Removed 1 \"%s\" directory." % item
    elif counts[item] > 1:
      if os.path.splitext(item)[1]:
        print "Removed %d \"%s\" files." % (counts[item], item)
      else:
        print "Removed %d \"%s\" directories." % (counts[item], item)

if __name__ == '__main__':

  usage = "%prog [experiment] [experiment] [...] [options]"
  description = \
  "Clean up the specified experiments. \
  You may also specify directories containing multiple experiments. \
  If no experiments are specified, cleans up all experiments."

  parser = OptionParser(usage=usage, description=description)
  parser.set_defaults(types=[])
  parser.add_option("-i","--inference", action="append_const", const="inference",
                    dest="types", help='Remove "inference" directories.')
  parser.add_option("-n","--networks", action="append_const", const="networks",
                    dest="types", help='Remove "networks" directories.')
  parser.add_option("-r","--report.txt", action="append_const", const="report.txt",
                    dest="types", help='Remove "report.txt" files.')
  parser.add_option("-p","--results.pkl", action="append_const", const="results.pkl",
                    dest="types", help='Remove "results.pkl" files.')
  parser.add_option("-e","--permutations", action="append_const", const="exp",
                    dest="types", help='Remove "exp" directories containing permuted experiments')

  def remove_all_directories(option, opt_str, value, parser):
      parser.values.ensure_value('types',[]).extend(["inference", "networks",
                                                     "description.pyc", "exp"])

  def remove_all(option, opt_str, value, parser):
      parser.values.ensure_value('types',[]).extend(["inference", "networks",
                                                     "description.pyc","report.txt",
                                                     "results.pkl", "exp"])

  parser.add_option("-d", "--directories", action="callback",
                    callback=remove_all_directories,
                    help='Leave only "description.py", "report.txt" and "results.pkl".')

  parser.add_option("-a", "--all", action="callback",
                    callback=remove_all,
                    help='Leave only "description.py".')

  (options, args) = parser.parse_args()

  if len(options.types)==0:
    print "No file/directory type selected for cleaning"
    print "Please run with option -h/--help for help"
    sys.exit()

  experiments = [utils.fixExperimentPath(a) for a in args]
  cleanup(experiments=experiments, types=options.types)
