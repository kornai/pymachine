
def main(debugLevel='WARNING'):
  import sys
  from wrapper import Wrapper
  import logging
  logging.basicConfig(level=logging.__dict__[debugLevel])
  sen = sys.stdin.readline().decode('utf-8').strip()
  w = Wrapper('machine.cfg')
  m = w.run(sen)
  sys.stdout.write(m.to_dot(True).encode('utf-8'))

import optfunc
optfunc.run(main)