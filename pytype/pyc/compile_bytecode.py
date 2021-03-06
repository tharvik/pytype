"""Compiles a single .py to a .pyc and writes it to stdout."""

# These are C modules built into Python. Don't add any modules that are
# implemented in a .py:
import imp
import marshal
import sys


MAGIC = imp.get_magic()


def _write32(f, w):
  f.write(bytearray([
      (w >> 0) & 0xff,
      (w >> 8) & 0xff,
      (w >> 16) & 0xff,
      (w >> 24) & 0xff]))


def write_pyc(f, codeobject, source_size=0, timestamp=0):
  f.write(MAGIC)
  _write32(f, timestamp)
  if tuple(sys.version_info[:2]) >= (3, 3):
    _write32(f, source_size)
  f.write(marshal.dumps(codeobject))


def compile_to_pyc(data_file, filename, output):
  with open(data_file, "r") as fi:
    src = fi.read()
  try:
    codeobject = compile(src, filename, "exec")
  except Exception as err:  # pylint: disable=broad-except
    output.write(b"\1")
    output.write(str(err))
  else:
    output.write(b"\0")
    write_pyc(output, codeobject)


def main():
  if len(sys.argv) != 3:
    sys.exit(1)
  output = sys.stdout.buffer if hasattr(sys.stdout, "buffer") else sys.stdout
  compile_to_pyc(data_file=sys.argv[1], filename=sys.argv[2], output=output)


if __name__ == "__main__":
  main()
