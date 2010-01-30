# coding: utf-8

"""
 twneru2
 Copyright (C) 2010 Satoshi Ueyama <gyuque@gmail.com>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import time
import calendar
import botconfig
from google.appengine.ext import db

def parse_tweet_time(s, delay_sec=0):
  import re
  tshift = calendar.timegm( time.strptime( re.sub(' ?\+0000', '', s) , '%a %b %d %H:%M:%S %Y') ) - 43200 + botconfig.BotConfig["TimeOffset"]
  return time.gmtime(tshift+delay_sec)

def parse_wake_tweet_time(s):
  import re
  tshift = calendar.timegm( time.strptime( re.sub(' ?\+0000', '', s) , '%a %b %d %H:%M:%S %Y') ) + botconfig.BotConfig["TimeOffset"]
  return time.gmtime(tshift)

def tw_day_id(ts, chk):
  if (ts.tm_hour < 1 and chk):
    return None

  return (ts.tm_year*10000) + (ts.tm_mon * 100) + ts.tm_mday

class SleepTime(db.Model):
  username = db.StringProperty(required=True)
  day_id   = db.IntegerProperty(required=True)
  hour     = db.IntegerProperty(required=True)
  min      = db.IntegerProperty(required=True)
  sec      = db.IntegerProperty(required=True)

  @classmethod
  def check_exists(klass, nick, ofs):
    import time

    a = klass.all()
    a.filter('username =', nick)
    a.order('-day_id')
    ofs_t = time.time() + botconfig.BotConfig["TimeOffset"] - (ofs-1)*86400
    a.filter('day_id <', tw_day_id(time.gmtime(ofs_t), False) )

    return a.count()>0

  @classmethod
  def gather_user(klass, nick, ofs = 0):
    import time

    a = klass.all()
    a.filter('username =', nick)
    a.order('-day_id')

    if ofs > 0:
      ofs_t = time.time() + botconfig.BotConfig["TimeOffset"] - (ofs-1)*86400
      a.filter('day_id <=', tw_day_id(time.gmtime(ofs_t), False) )

    res = {}
    rows = a.fetch(limit = 100)
    for r in rows:
       res[r.day_id] = {'hour': r.hour, 'min': r.min}
#      print >>sys.stderr, r.day_id

    return res

  @classmethod
  def gather_recents(klass):
    a = klass.all()
    a.order('-day_id').order('-hour')

    list = []
    rows = a.fetch(limit = 100)
    for s in rows:
      list.append( (s.day_id*10000+s.hour*100+s.min, s.username) )

    list.sort()
    list.reverse()

    res = []
    umap = {}
    for s in list:
      if (not s[1] in umap):
        umap[s[1]] = True
        res.append(s)

        if (len(res) > 9):
          break

    return res

  @classmethod
  def put_time(klass, nick, did, hr, min, sec):
    a = klass.all()
    a.filter('username =', nick)
    a.filter('day_id =', did)

    rcd = None
    if (a.count() < 1):
      rcd = klass(username = nick, day_id = did, hour = hr, min = min, sec = sec)
    else:
      rcd = a.fetch(limit = 1)[0]
      rcd.hour = hr
      rcd.min  = min
      rcd.sec  = sec

    rcd.put()

  @classmethod
  def put_today(klass, nick, tt, delay_m):
    ts = parse_tweet_time(tt, delay_m*60)
    klass.put_time(nick, tw_day_id(ts, False), ts.tm_hour+12, ts.tm_min, ts.tm_sec)

class WakeTime(SleepTime):
  @classmethod
  def put_today(klass, nick, tt, override_hour, override_min):
    do_override = (override_hour >= 0)
    ts = parse_wake_tweet_time(tt)
    klass.put_time(nick, tw_day_id(ts, False),
                   override_hour if do_override else ts.tm_hour,
                   override_min  if do_override else ts.tm_min,
                   0             if do_override else ts.tm_sec)

class TwitterUser(db.Model):
  username  = db.StringProperty(required=True)
  location  = db.StringProperty(required=False)
  icon      = db.StringProperty(required=False)
  bscore    = db.IntegerProperty(required=False)
  s_timestamp = db.IntegerProperty(required=False)
  client    = db.IntegerProperty(required=False)

  @classmethod
  def set_bscore(klass, nick, s, t, prefetch = None):
    u = None
    if prefetch:
      if nick in prefetch:
        u = prefetch[nick]

    if not u:
      a = TwitterUser.all()
      a.filter('username =', nick)
      if (a.count() < 1):
        u = TwitterUser(username = nick)
      else:
        u = a.fetch(limit = 1)[0]

    u.s_timestamp = int(t)
    u.bscore      = s
    u.put()

  @classmethod
  def set_icon(klass, nick, url):
    a = TwitterUser.all()
    a.filter('username =', nick)
    u = None
    if (a.count() < 1):
      u = TwitterUser(username = nick)
    else:
      u = a.fetch(limit = 1)[0]

    if not u.icon == url:
      u.icon = url
      u.put()

  @classmethod
  def set_location(klass, nick, loc):
    a = TwitterUser.all()
    a.filter('username =', nick)
    u = None
    if (a.count() < 1):
      u = TwitterUser(username = nick)
    else:
      u = a.fetch(limit = 1)[0]

    u.location = loc
    u.put()

  @classmethod
  def get_location(klass, nick):
    a = TwitterUser.all()
    a.filter('username =', nick)
    if (a.count() < 1):
      return None

    return a.fetch(limit = 1)[0].location

  @classmethod
  def get_icon(klass, nick):
    a = TwitterUser.all()
    a.filter('username =', nick)
    if (a.count() < 1):
      return None

    return a.fetch(limit = 1)[0].icon

  @classmethod
  def get_by_nick(klass, nick):
    a = TwitterUser.all()
    a.filter('username =', nick)
    if (a.count() < 1):
      return None

    return a.fetch(limit = 1)[0]

