import argparse
import sys
from colors import color

# Largely taken from https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
# Though I added the colorization
def eprint(*args, **kwargs):
  args = [(color(arg, fg="red") if isinstance(arg, str) else arg) for arg in args]
  print(*args, file=sys.stderr, **kwargs)


class VerifyPositiveIntAction(argparse.Action):
  def __init__(self, option_strings, dest, nargs=None, default=-1, **kwargs):
    if nargs is not None:
      raise ValueError("nargs should not apply to arguments using VerifyPositiveIntAction actions")
    super(VerifyPositiveIntAction, self).__init__(option_strings, dest, nargs=nargs, default=default, **kwargs)
    pass
  def __call__(self, parser, namespace, values, option_string=None):
    #print("Values, default: {}, {}".format(values, self.default))
    if isinstance(values, int):
      if values > 0 or values == self.default:
        setattr(namespace, self.dest, values)
        pass
      else:
        otherwise = " or the default ({})".format(self.default) if self.default <= 0 else ""
        raise ValueError("value {} invalid, must be a positive integer{}".format(values, otherwise))
      pass
    else:
      raise ValueError("value {} invalid, expected an int, but found {}".format(values, type(values)))


class VerifyPositiveIntListAction(argparse.Action):
  def __init__(self, option_strings, dest, nargs="*", default=[], **kwargs):
    if nargs is None:
      raise ValueError("nargs should be * for arguments using VerifyPositiveIntListAction actions")
    super(VerifyPositiveIntListAction, self).__init__(option_strings, dest, nargs=nargs, default=default, **kwargs)
    pass
  def __call__(self, parser, namespace, values, option_string=None):
    if isinstance(values, list):
      if any(not isinstance(v, str) and not isinstance(v, int) for v in values):
        raise ValueError("some of the values are invalid, expected positive integers but found: {}".format(values))
      else:
        try:
          values = [int(v) for v in values]
          pass
        except ValueError as e:
          raise ValueError("Expected a list of positive integers, but found: {}".format(values))
        else:
          if any(v <= 0 for v in values):
            raise ValueError("Expected a list of positive integers, but found zeros and/or negative integers: {}".format(values))
          setattr(namespace, self.dest, sorted(values))
          pass
        pass
      pass
    else:
      raise ValueError("Expected a list, but found {}".format(values))
    pass
  pass
