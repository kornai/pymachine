import sys
from wrapper import Wrapper
sen = sys.stdin.readline().decode('utf-8').strip()
w = Wrapper('machine.cfg')
m = w.run(sen)
sys.stdout.write(m.to_dot(True).encode('utf-8'))