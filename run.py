#!/usr/bin/python
from ggbg import GGBG

if __name__ == '__main__':
    try:
        game = GGBG()
        game.main()

    except KeyboardInterrupt:
        print 'Bye'

