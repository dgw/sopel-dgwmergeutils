"""
Utility to go with my games, in case you want to merge duplicate users
created when people play with different nicks, accidentally or otherwise.
"""
from sopel.module import commands, example, require_owner
from sopel.tools import Identifier

STRINGS = {
    'OWNER_MERGE':     "Only the bot owner can merge users.",
    'MERGE_SYNTAX':    "I want to be sure there are no mistakes here. "
                       "Please specify nicks to merge as: <duplicate> into <primary>",
    'MERGE_DONE':      "Merged %s into %s.",
    'MERGE_GROUPED':   "Nicks %s & %s are already grouped.",
    'MERGE_UNKNOWN':   "Encountered unknown nick. Aborting merge.",
    'OWNER_UNMERGE':   "Only the bot owner can unmerge nicks.",
    'UNMERGE_SYNTAX':  "I need a nickname to unmerge.",
    'NOT_GROUPED':     "Nick group %s contains only one nick; nothing to do.",
    'UNMERGE_UNKNOWN': "Encountered unknown nick. Aborting unmerge.",
    'UNMERGE_DONE':    "Removed %s from nick group %s.",
    'GLIST_SYNTAX':    "I need a nickname to look up.",
    'GLIST_BY_ID':     "Nicks in group %s: %s.",
    'GLIST_BY_NICK':   "Other nicks in %s's group: %s.",
    'GLIST_FAILED':    "Could not find nick group for %s.",
    'GLIST_EMPTY':     "No nicks grouped with %s.",
}

STATS = (
    'bomb_wrongs',
    'bomb_timeouts',
    'bomb_defuses',
    'bomb_alls',
    'bombs_planted',
    'duel_wins',
    'duel_wins_streak_record',
    'duel_losses',
    'duel_losses_streak_record',
    'rep_score',
    'roulette_games',
    'roulette_wins',
)

RATES = (
    'bomb_last_planted',
    'duel_last',
    'rep_used',
    'roulette_last',
)


@commands('nickmerge')
@example(".nickmerge newbie into old_friend")
@require_owner(STRINGS['OWNER_MERGE'])
def is_really(bot, trigger):
    """
    Merge the two nicks, keeping the stats for the second one.
    """
    duplicate = trigger.group(3) or None
    primary = trigger.group(5) or None
    if not primary or not duplicate or trigger.group(4).lower() != 'into':
        bot.reply(STRINGS['MERGE_SYNTAX'])
        return
    duplicate = Identifier(duplicate)
    primary = Identifier(primary)
    try:
        if bot.db.get_nick_id(duplicate, False) == bot.db.get_nick_id(primary, False):
            bot.reply(STRINGS['MERGE_GROUPED'] % (primary, duplicate))
            return
    except ValueError:
        bot.reply(STRINGS['MERGE_UNKNOWN'])
        return
    newstats = dict()
    for stat in STATS:
        dupval = bot.db.get_nick_value(duplicate, stat) or 0
        prival = bot.db.get_nick_value(primary, stat) or 0
        newstats[stat] = dupval + prival
    for rate in RATES:
        dupval = bot.db.get_nick_value(duplicate, rate) or 0
        prival = bot.db.get_nick_value(primary, rate) or 0
        newstats[rate] = prival if (prival > dupval) else dupval
    for stat in newstats:
        bot.db.set_nick_value(primary, stat, newstats[stat])
        bot.db.set_nick_value(duplicate, stat, 0)  # because willie < 5.4.1 doesn't merge properly
    bot.db.merge_nick_groups(primary, duplicate)
    bot.say(STRINGS['MERGE_DONE'] % (duplicate, primary))


@commands('nickunmerge')
@example(".nickunmerge DeadAlias")
@require_owner(STRINGS['OWNER_UNMERGE'])
def isnt_anymore(bot, trigger):
    """
    Remove the given nick from its nick group, allowing it to be relearned as a new user.
    """
    if not trigger.group(3):
        bot.say(STRINGS['UNMERGE_SYNTAX'])
        return
    target = Identifier(trigger.group(3))
    try:
        group = bot.db.get_nick_id(target, False)
    except ValueError:  # no ID exists for this nick; it's unknown
        bot.say(STRINGS['UNMERGE_UNKNOWN'])
        return
    try:
        bot.db.unalias_nick(target)
    except ValueError:  # the nick is in a group by itself
        bot.say(STRINGS['NOT_GROUPED'] % group)
    else:  # no exception means it's fine
        bot.say(STRINGS['UNMERGE_DONE'] % (target, group))


@commands('shownickgroup')
@example(".shownickgroup AlsoKnownAsNil")
@example(".shownickgroup 1337")
def also_known_as(bot, trigger):
    """
    Show the nicks grouped with the specified nick in the database.
    """
    if not trigger.group(3):
        bot.say(STRINGS['GLIST_SYNTAX'])
        return
    target = Identifier(trigger.group(3))
    id_lookup = False
    try:
        gid = bot.db.get_nick_id(target, create=False)
    except ValueError:
        if target.isdigit():
            gid = int(target)
            id_lookup = True
        else:
            bot.say(STRINGS['GLIST_FAILED'] % target)
            return
    res = bot.db.execute("SELECT canonical from nicknames where nick_id=%d;" % gid)
    nicks = [Identifier(row[0]) for row in res.fetchall()]

    if len(nicks):
        if id_lookup:
            bot.say(STRINGS['GLIST_BY_ID'] % (target, ', '.join(nicks)))
        else:
            try:
                nicks.remove(target)
            except ValueError:
                pass  # not a big deal if the queried nick can't be removed, really
            if len(nicks):  # second check to show different message for single-nick groups
                bot.say(STRINGS['GLIST_BY_NICK'] % (target, ', '.join(nicks)))
            else:
                bot.say(STRINGS['GLIST_EMPTY'] % target)
    else:
        bot.say(STRINGS['GLIST_FAILED'] % target)
