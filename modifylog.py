import re
import sys

with open(sys.argv[1]) as f, open(sys.argv[2], 'w') as output:
    output.write(re.sub(r'\[\d+,\d+T\d+,0,@,@,,,Combat.*\r?\n', '', f.read()))
