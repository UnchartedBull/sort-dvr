from tqdm import tqdm
import io
import logging


class TqdmUpTo(tqdm):
  def update_to(self, frames=1):
    return self.update(frames - self.n)


class TqdmToLogger(io.StringIO):
  logger = None
  level = None
  first = True
  buf = ''

  def __init__(self, logger, level=None):
    super(TqdmToLogger, self).__init__()

    self.logger = logger
    self.level = level or logging.INFO

  def write(self, buf):
    self.buf = buf.strip('\r\n\t ')

  def flush(self):
    if not self.first:
      print("\x1b[1A\x1b[0J", end="\r")
    else:
      self.first = False

    self.logger.log(self.level, self.buf)