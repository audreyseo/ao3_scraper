import argparse



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
