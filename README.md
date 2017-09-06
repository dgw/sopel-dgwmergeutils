# sopel-dgwmergeutils

This module provides a command for bot owners to merge nicks into groups, as supported
by `bot.db` in willie/sopel, and combine their stats for dgw's custom game modules at
the same time. Originally it was a command built into BombBot.py, and only merged that
module's stats, but as more games were added it became clear that it wasn't practical
to give them all their own merge commands because of how willie/sopel's DB works.

## Currently supported games:

* duel.py
* BombBot.py
* roulette.py
* rep.py

### Future support planned:

* UnoBot.py

