# -*- coding: utf-8 -*-

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
import topia
import twnmodels
import twncalendar
import handler_base as hbase
import twitterclient
from google.appengine.api import memcache

MODE_SLEEP = True
MODE_WAKE  = False

REPLY_STD_SLEEP = 1
REPLY_STD_WAKE  = 2
REPLY_MOD_SLEEP = 3
REPLY_MOD_WAKE  = 4
REPLY_ERR_DATE  = 5
REPLY_ERR_TIME  = 6
REPLY_FWD_TIME  = 8
REPLY_SET_LOCATION = 7

def register_custom_servlets(list):
  list.append( ('/',              TopPage) )
  list.append( ('/statuses',      StatusPage) )
  list.append( ('/get_gadget',    GetGadgetPage) )
  list.append( ('/google-gadget', GoogleGadgetPage) )
  list.append( ('/gadget',        GadgetPage) )
  list.append( ('/dashboard',     DashboardPage) )
  list.append( ('/users',         UserListPage) )

def process_icon_map(imap):
  from google.appengine.ext import db

  names = imap.keys()
  if len(names) < 1:
    return

  found = db.GqlQuery("SELECT * FROM TwitterUser WHERE username IN :list",list = names)
  users = found.fetch(limit = 100)

  print >>sys.stderr, "  ".join(names)
  foundmap = {}

  # existing users
  for u in users:
    foundmap[u.username] = True
    if imap[u.username] != u.icon:
      u.icon = imap[u.username]
      u.put()
      print >>sys.stderr, "updated icon for %s" % u.username

  # new users
  for i in imap:
    if not i in foundmap:
      u = twnmodels.TwitterUser(username = i, icon = imap[i])
      u.put()
      print >>sys.stderr, "created user and set icon for %s" % u.username

def jst_datetime():
  import time
  import botconfig
  t  = time.time() + botconfig.BotConfig["TimeOffset"]

  return time.strftime('%Y-%m-%d %H:%M', time.gmtime(t))

class TwitterBotImpl(object):
  max_id = 0

  def max_processed_id(self):
    return self.max_id

  def process_replies(self, tweets, service):
    new_tweets = tweets.newer()
    flist = FilteredTweetList()
    for t in new_tweets:
      flist.check(t)
      if int(t.id) > self.max_id:
        self.max_id = int(t.id)

    self.process_calls(self.remove_same_user(flist.ls_sleeps), service, MODE_SLEEP)
    self.process_calls(self.remove_same_user(flist.ls_wakes),  service, MODE_WAKE)
    self.process_commands(service, flist.ls_commands)

    print >>sys.stderr, "  %d new tweets" % len(new_tweets)
    print >>sys.stderr, flist.dump()

    service.append_update_icon_task()
    service.append_call_task("update_b_ranking")
    return

  def remove_same_user(self, tweets):
    newlist = []

    umap = {}
    for t in tweets:
      if t.nick in umap and (not t.user_data['specified_time'] or not t.user_data['specified_time'][0] >= 0):
        if umap[t.nick] > t.id: # 同じユーザの古い発言を無視
          continue

      umap[t.nick] = t.id
      newlist.append(t)

    return newlist

  def process_calls(self, tweets, service, mode):
    if not tweets:
      return 0

    if len(tweets) < 1:
      return 0

    # clear dashboard cache
    if mode == MODE_SLEEP:
      DashboardPage.invalidate_recent_sleeps()
    else:
      DashboardPage.invalidate_recent_wakes()

    for t in tweets:
      self.record_time(mode, t)

    self.make_replies(service, tweets)
    return len(tweets)

  def process_commands(self, service, tweets):
    for t in tweets:
      if 'specified_location' in t.user_data:
        t.user_data['reply_type'] = REPLY_SET_LOCATION

    self.make_replies(service, tweets)

  def make_replies(self, service, tweets):
    names_sleep  = None
    names_wake   = None

    for t in tweets:
      if not 'reply_type' in t.user_data:
        continue

      reply_type = t.user_data['reply_type']
      if reply_type == REPLY_STD_SLEEP:
        if not names_sleep:
          names_sleep = []
        names_sleep.append("@"+t.nick)
      elif reply_type == REPLY_STD_WAKE:
        if not names_wake:
          names_wake = []
        names_wake.append("@"+t.nick)
      elif reply_type == REPLY_MOD_SLEEP:
        service.append_tweet(u"@%s 睡眠時間を記録しました (%s)" % (t.nick, TwitterBotImpl.modday_text(t)))
      elif reply_type == REPLY_MOD_WAKE:
        service.append_tweet(u"@%s 起床時間を記録しました (%s)" % (t.nick, TwitterBotImpl.modday_text(t)))
      elif reply_type == REPLY_ERR_DATE:
        service.append_tweet(u"@%s 日付指定がおかしいです" % t.nick)
      elif reply_type == REPLY_ERR_TIME:
        service.append_tweet(u"@%s 時刻指定がおかしいです" % t.nick)
      elif reply_type == REPLY_FWD_TIME:
        service.append_tweet(u"@%s 時刻指定がおかしいです(未来の時刻を指定していませんか?)" % t.nick)
      elif reply_type == REPLY_SET_LOCATION:
        lid = twncalendar.get_location_id(t.user_data['specified_location'])
        twnmodels.TwitterUser.set_location(t.nick, lid)
        service.append_tweet(u"@%s 地域を%sに設定しました" % (t.nick, t.user_data['specified_location']))

    if names_sleep:
      use_dot = '.' if (len(names_sleep) > 1) else ''
      service.append_tweet( "%s%s %s" % (use_dot, " ".join(names_sleep), TwitterBotImpl.random_message(MODE_SLEEP)) )

    if names_wake:
      use_dot = '.' if (len(names_wake) > 1) else ''
      service.append_tweet( "%s%s %s" % (use_dot, " ".join(names_wake), TwitterBotImpl.random_message(MODE_WAKE)) )

  def record_time(self, mode, t):
    spec_date = t.user_data['specified_date']
    spec_time = t.user_data['specified_time']
#    if spec_time and spec_time[0] >= 0:
#      self.modify_time(t.nick, spec_date, spec_time[0], spec_time[1])
#      return

    if mode == MODE_SLEEP:
      if spec_date:
        t.user_data['reply_type'] = self.modify_sleep_time(t.nick, spec_date, spec_time[0], spec_time[1], t.user_data)
        return

      delay = 0
      if spec_time and spec_time[0] == -1:
        delay = spec_time[1]

      t.user_data['reply_type'] = REPLY_STD_SLEEP
      twnmodels.SleepTime.put_today(t.nick, t.timestamp, delay)
    else: # wake up
      if spec_date:
        t.user_data['reply_type'] = self.modify_wake_time(t.nick, spec_date, spec_time[0], spec_time[1], t.user_data)
        return

      override_h = -1
      override_m = 0

      if spec_time and spec_time[0] != None:
        override_h = spec_time[0]
        override_m = spec_time[1]

      if override_h >= 0 and (not self.is_valid_wake_time(override_h, override_m)):
        print >>sys.stderr, '%s <- command error: invalid time (wkup)' % t.nick
        t.user_data['reply_type'] = REPLY_ERR_TIME
        return

      t.user_data['reply_type'] = REPLY_STD_WAKE
      twnmodels.WakeTime.put_today(t.nick, t.timestamp, override_h, override_m)

    return

  def modify_wake_time(self, nick, day, hr, mn, user_data):
    import time
    import botconfig

    day = int(day)
    hr = int(hr)
    mn = int(mn)

    if (day < 1 or day > 31):
      print >>sys.stderr, '%s <- command error: invalid date(1)' % nick
      return REPLY_ERR_DATE

    today_t = time.time() - 43200 + botconfig.BotConfig["TimeOffset"]
    found_day = self.check_prev_day(day, today_t)
    if not found_day:
      print >>sys.stderr, '%s <- command error: invalid date(2)' % nick
      return REPLY_ERR_DATE

    if (hr < 0 or hr > 23 or mn < 0 or mn > 59):
      print >>sys.stderr, '%s <- command error: invalid time' % nick
      return REPLY_ERR_TIME

    user_data['mod_mon']  = found_day.tm_mon
    user_data['mod_mday'] = found_day.tm_mday
    twnmodels.WakeTime.put_time(nick, twnmodels.tw_day_id(found_day, False), hr, mn, 0)
    return REPLY_MOD_WAKE

  def modify_sleep_time(self, nick, day, hr, mn, user_data):
    import time
    import botconfig

    day = int(day)
    hr = int(hr)
    mn = int(mn)

    if day < 1 or day > 31:
      print >>sys.stderr, '%s <- command error: invalid date(1)' % nick
      return REPLY_ERR_DATE

    now_t = time.time() + botconfig.BotConfig["TimeOffset"]
    today_t = now_t - 43200
    found_day = TwitterBotImpl.check_prev_day(day, today_t)
    if not found_day:
      print >>sys.stderr, '%s <- command error: invalid date(2)' % nick
      return REPLY_ERR_DATE

    if (hr >= 0 and hr < 3):
      hr += 24

    if (hr < 13 or hr > 36 or mn < 0 or mn > 59):
      print >>sys.stderr, '%s <- command error: invalid time' % nick
      return REPLY_ERR_TIME

    spec_t = time.mktime((found_day.tm_year, found_day.tm_mon, found_day.tm_mday, hr, mn, 0, 0, 0, -1))
    if (spec_t-now_t) > 600:
      print >>sys.stderr, '%s <- command error: invalid time(3)' % nick
      return REPLY_FWD_TIME

    user_data['mod_mon']  = found_day.tm_mon
    user_data['mod_mday'] = found_day.tm_mday
    twnmodels.SleepTime.put_time(nick, twnmodels.tw_day_id(found_day, False), hr, mn, 0)

    return REPLY_MOD_SLEEP

  def is_valid_wake_time(self, h, m):
    return h >= 0 and h < 24 and m >= 0 and m < 60

  @classmethod
  def check_prev_day(cls, day, org):
    import time

    for i in range(20):
      t = org - i*86400
      gt = time.gmtime(t)
      if (day == gt.tm_mday):
        return gt

    return None

  @classmethod
  def modday_text(cls, t):
    d = t.user_data
    mm = str(d['specified_time'][1])
    if len(mm) == 1:
      mm = "0"+mm

    return u"%d月%d日 %d:%s" % (d['mod_mon'], d['mod_mday'], d['specified_time'][0], mm)

  @classmethod
  def random_message(cls, mode):
    import random
    import botconfig

    ls = None
    if mode == MODE_WAKE:
      ls = botconfig.BotConfig["WakeMessages"]
    else:
      ls = botconfig.BotConfig["SleepMessages"]

    return ls[random.randint(0, len(ls)-1)]

class FilteredTweetList(object):
  def __init__(self):
    self.ls_wakes    = []
    self.ls_sleeps   = []
    self.ls_commands = []
    self.n_ignored   = 0

  def dump(self):
    return "  sleeps: %d\n  wakes: %d\n  commands: %d\n  ignored: %d" % (len(self.ls_sleeps), len(self.ls_wakes), len(self.ls_commands), self.n_ignored)

  def add_location_command(self, t, locname):
    t.user_data['specified_location'] = locname
    self.ls_commands.append(t)

  def check(self, t):
    import re
    loc_cmd_re = re.compile(u'^ *@[_a-z]+ +[地域場所]+[をは](さいたま|[埼玉関西東京大阪長野名古屋福岡中部愛知松江島根札幌北海道九州]+)')

    try:
      # 寝た or 起きた
      # todo: a,b,c = fun()
      # todo: use topia dict
      tres = topia.ParseTwneruText.parse(t.text)

      t.user_data['specified_date'] = tres[0]
      t.user_data['specified_time'] = tres[1]
      if tres[2] == 'sleep':
        self.ls_sleeps.append(t)
      else:
        self.ls_wakes.append(t)

    except ValueError, e:
      # 地域設定 or 無効発言
      rxr = loc_cmd_re.search(t.text)

      if rxr:
        self.add_location_command(t, rxr.group(1))
      else:
        self.n_ignored += 1

# ---- ranking ----

def update_b_ranking():
  BScoreUpdater.calc()

class BScoreUpdater(object):
  @classmethod
  def calc(cls):
    import time
    if memcache.get('bscore_cache_valid'):
      print >>sys.stderr, "BScoreUpdater aborted"
      return
    memcache.set('bscore_cache_valid', True, 900)

    sa = twnmodels.SleepTime.all()
    wa = twnmodels.WakeTime.all()

    t = time.time() +32400 - (86400*7)
    dayid = twnmodels.tw_day_id(time.gmtime(t), False)

    # make a table for 'next' day ids
    next_did = {}
    for dt in range(8):
      next_did[ twnmodels.tw_day_id(time.gmtime(t+dt*86400), False) ] = twnmodels.tw_day_id(time.gmtime(t+(dt+1)*86400), False)

    sa.order('-day_id').filter('day_id >=', dayid)
    wa.order('-day_id').filter('day_id >=', dayid)

    slist = sa.fetch(limit = 500)
    wlist = wa.fetch(limit = 500)

    umap = {}

    st_dmap = {}
    wk_dmap = {}
    #make dayid+username map
    for st in slist:
      st_dmap[cls.make_day_and_user_key(next_did[st.day_id], st.username)] = True

    for wt in wlist:
      if wt.day_id and not (cls.make_day_and_user_key(wt.day_id, wt.username) in st_dmap): # Sleep time is missing. Assume 6 hours sleep
        print >>sys.stderr, str(wt.day_id)
        dmy_h = wt.hour + 18
        slist.append(DummyTime(wt.username, dmy_h))

      wk_dmap[cls.make_day_and_user_key(wt.day_id, wt.username)] = True


    for st in slist:
      if not st.username in umap:
        umap[st.username] = 0

      if st.day_id:
        next_wake_id = cls.make_day_and_user_key(next_did[st.day_id], st.username)
        if not (next_wake_id in wk_dmap): # Wake time is missing. Assume 6 hours sleep
          dmy_h = st.hour + 6
          if (dmy_h > 23):
            dmy_h -= 24
          else:
            dmy_h = 0
          wlist.append(DummyTime(st.username, dmy_h))

      umap[st.username] += cls.calc_st_score( st.hour )

    for wt in wlist:
      if not wt.username in umap:
        umap[wt.username] = 0

      umap[wt.username] += cls.calc_wt_score( wt.hour )

    for score in umap:
      twnmodels.TwitterUser.set_bscore(score, umap[score], t)

    memcache.set("rank_timestamp", value=int(t))

  @classmethod
  def make_day_and_user_key(klass, did, username):
    return "<%s>%s" % (did, username)

  @classmethod
  def calc_st_score(klass, h):
    if h >= 18 and h < 25:
      return 0

    return (h-24) if h > 24 else 18 - h

  @classmethod
  def calc_wt_score(klass, h):
    if h >= 3 and h < 10:
      return 0

    return (h-9) if h > 9 else 3 - h

class DummyTime:
  def __init__(self, u, h):
    self.username = u
    self.hour     = h
    self.day_id   = None


class UserListPage(hbase.PageBase):
  @classmethod
  def make_activity_bar(klass, a):
    if a>6:
      a = 6

    return "<span class=\"activity lv-%d\"><img src=\"/images/dmy.gif\" alt=\"%d\" /></span>" % (a,a)

  @classmethod
  def make_bscore_list(klass):
    pairs = memcache.get('bscore_pairs')
    if not pairs:
      ts = memcache.get("rank_timestamp")
      if not ts:
        return None

      q = twnmodels.TwitterUser.all().order("-bscore").filter("s_timestamp =", int(ts))
      qlist = q.fetch(limit = 50)
      pairs = map(lambda u: (u.username, int(u.bscore/10.0)) , qlist)
      memcache.set('bscore_pairs', pairs, 200)

    return pairs

  @classmethod
  def make_user_list(cls):
    q_susers = twnmodels.SleepTime.all()
    q_susers.order('-day_id')

    q_wusers = twnmodels.WakeTime.all()
    q_wusers.order('-day_id')

    susers = q_susers.fetch(limit = 280)
    wusers = q_wusers.fetch(limit = 280)

    umap = {}
    for u in susers:
      if not u.username in umap:
        umap[u.username] = 1
      else:
        umap[u.username] += 1

    for u in wusers:
      if not u.username in umap:
        umap[u.username] = 1
      else:
        umap[u.username] += 1

    rlist = []
    for k,v in umap.iteritems():
      rlist.append((k,v))

    rlist.sort(lambda a, b: b[1]-a[1])
    return rlist

  def get(self):
    stype = self.request.get('sort')
    list = None
    tsitems = ''
    addclass = ''
    if stype.upper() == 'B':
      addclass = ' bsort'
      tsitems = "<li><a href=\"/users\">よく利用している</a></li><li><em>廃人</em></li>"
      list = UserListPage.make_bscore_list()
    else:
      tsitems = "<li><em>よく利用している</em></li><li><a href=\"/users?sort=b\">廃人</a></li>"
      list = UserListPage.make_user_list()

    ualist = []
    if list:
      for a in list:
        ualist.append( "<li>%s <a href=\"/statuses?nick=%s\">%s</a></li>" % (UserListPage.make_activity_bar(a[1]),a[0],a[0]) )
    else:
      ualist.append("<li>データが作成されていません</li>")

    render_params = {'ualist': "\n".join(ualist), 'typesel':tsitems, 'addclass': addclass}
    self.write_page("templates/userlist.html", render_params)




class DashboardPage(hbase.PageBase):
  def get(self):
    import twitterbot
    recents    = self.recents_html_or_cache()
    short_list = self.short_userlist_html_or_cache()

    stat = twitterbot.ObserveService.last_status()
    params = {
      'sleeps_html': " ".join(recents[0]),
      'wakes_html': " ".join(recents[1]),
      'short_list': short_list,
      'error_class': "",
      'error_message': None,
      'error_label': "成功"
    }

    if stat:
      params['stat_rel_time'] = str(stat.rel_time/10)
      params['stat_elapsed_time'] = "%.1f" % float((stat.elapsed_time or 0)/10.0)

      if stat.api_error:
        params['error_class']   = " warn"
        params['error_label']   = " 失敗"
        if stat.api_error < 0:
          params['error_message'] = "APIエラー (タイムアウト?)"
        else:
          params['error_message'] = "APIエラー (ステータス: %d)" % stat.api_error
      elif stat.internal_error:
        params['error_class']   = " warn"
        params['error_label']   = " 失敗"
        params['error_message'] = "内部エラー"

    self.write_page("templates/dashboard.html", params)
    return

  def short_userlist_html_or_cache(self):
    html = memcache.get('userlist_short_html')
    if not html:
      ls = UserListPage.make_user_list()[0:20]
      html = "\n".join(map(lambda u:"<li>%s<br />%s</li>" % (DashboardPage.make_statpage_link(u[0]), UserListPage.make_activity_bar(u[1])) , ls))
      memcache.set('userlist_short_html', html, 300)

    return html

  def recents_html_or_cache(self):
    s_html = memcache.get('recents_sleeps_html')
    w_html = memcache.get('recents_wakes_html')

    if not s_html:
      s_html = self.make_recents_html(twnmodels.SleepTime)
      print >>sys.stderr, "  memcache expired: dashboard, recent sleeps"
      memcache.set('recents_sleeps_html', s_html, 120)

    if not w_html:
      w_html = self.make_recents_html(twnmodels.WakeTime)
      print >>sys.stderr, "  memcache expired: dashboard, recent wakes"
      memcache.set('recents_wakes_html', w_html, 120)

    return s_html, w_html

  def make_recents_html(self, model_class):
    import time
    import botconfig

    now_t = time.time() + botconfig.BotConfig["TimeOffset"]

    list = model_class.gather_recents()
    htmls = []
    prev_badge = None
    for s in list:
      tyear = int(s[0]/100000000)
      tmon = int(s[0]/1000000)%100
      td = int(s[0]/10000)%100
      th = int(s[0]/100)%100
      tm = s[0]%100

      tt = time.mktime((tyear, tmon, td, th, tm, 0, 0, 0, -1))
      bg = DashboardPage.reltime_badge(int(now_t - tt))
      add_cls = ''
      if not bg == prev_badge:
        prev_badge = bg
        add_cls = ' class="with-badge"'
      else:
        bg = ''

      htmls.append(u'<li%s>%s<span class="date">%02d日</span> %02d:%02d<br />%s</li>' % (add_cls, bg, td, th, tm, DashboardPage.make_statpage_link(s[1])) )

    return htmls

  @classmethod
  def reltime_badge(cls, d):
    if d <= 1800:
      return u'<span class="interval">30分以内</span>'

    if d <= 3600:
      return u'<span class="interval">1時間以内</span>'

    if d <= 10800:
      return u'<span class="interval">3時間以内</span>'

    if d <= 86400:
      return u'<span class="interval">24時間以内</span>'

    return u'<span class="interval">1日以上前</span>'

  @classmethod
  def invalidate_recent_sleeps(cls):
    memcache.set('recents_sleeps_html', None)

  @classmethod
  def invalidate_recent_wakes(cls):
    memcache.set('recents_wakes_html', None)

  @classmethod
  def make_statpage_link(cls, nick):
    import cgi
    nick = cgi.escape(nick)
    return "<em><a href=\"/statuses?nick=%s\">%s</a></em>" % (nick, nick)

class TopPage(hbase.PageBase):
  def get(self):
    self.write_page("templates/index.html", {})
    return

class StatusPage(hbase.PageBase):
  def get(self):
    import botconfig
    import daychart
    import time
#    twnmodels.WakeTime.put_today('gyuque', "Sun Mar 4 23:00:00 +0000 2009")

    start_time = time.time()

    # get current page
    cur_ofs = self.request.get('ofs')
    if not cur_ofs:
      cur_ofs = 0
    else:
      cur_ofs = int(cur_ofs)

    demo = False
    nick = self.request.get('nick')
    res = self.response
    if (not nick):
      demo = True
      nick = botconfig.BotConfig["DemoNick"]

    record = twnmodels.SleepTime.gather_user(nick, cur_ofs)
    wk_record = twnmodels.WakeTime.gather_user(nick, cur_ofs)

    stats = self.make_stats(record, wk_record)

    b_ts = memcache.get("rank_timestamp")

    tuser =  twnmodels.TwitterUser.get_by_nick(nick)

    # Has this user replied?
    if not tuser and len(record) < 1 and len(wk_record) < 1:
      self.invite_page(nick)
      return

    loc    = tuser.location if tuser else None
    icon   = tuser.icon     if tuser else None
    bsc    = tuser.bscore   if tuser else None

    if bsc:
      if (not b_ts) or (not tuser.s_timestamp == b_ts):
        bsc = None

    if not loc: # if not set, default 'tokyo'
      loc = 'tokyo'

    ch = daychart.DayChart(loc, time.time() -1000 + 32400 - cur_ofs*86400, 30)
    table_parts = ch.generate_table(record, wk_record)
    table_parts['user_icon'] = icon if icon else '/images/naimage.png'
    table_parts['nick']      = nick
    table_parts['demo']      = demo
    table_parts['gendate']   = jst_datetime()
    table_parts['loc_label'] = twncalendar.LOCATION_DISP_NAMES[loc]
    table_parts['stat_org']  = "%d/%d" % (stats['org_mon'], stats['org_day'])
    table_parts['stat_avails']  = stats['avail_count']
    table_parts['stat_avr']   = ('%.3g' % stats['average']) if (stats['average']>=0) else '-'
    table_parts['stat_sdist'] = ('%.3g' % stats['sdist'])   if (stats['sdist']>=0) else '-'

    table_parts['stat_bscore'] = str(bsc) if bsc else '-'
    table_parts['pager_html']  = StatusPage.make_pager(cur_ofs, nick)

    self.write_page("templates/statuses.html", table_parts)

  def make_stats(self, slps, wks):
    import time
    import math

    t = time.time() + 32400 - 604800
    gt = time.gmtime(t)

    stimes = []
    ssum   = 0
    avr    = -1

    for i in range(7):
      gt2 = time.gmtime(t)
      t += 3600*24
      gt3 = time.gmtime(t)

      did  = twnmodels.tw_day_id(gt2, False)
      did2 = twnmodels.tw_day_id(gt3, False)

      if (did in slps) and (did2 in wks):
        st = slps[did]
        wt = wks[did2]

        sleep_etime = wt['hour']*60 + wt['min'] + 60*24
        sleep_etime -= st['hour']*60 + st['min']

        ssum += sleep_etime
        stimes.append(sleep_etime)

    sdist = -1
    alen = len(stimes)
    if len(stimes)>0:
      avr = ssum / alen
      dsum = 0
      for s in stimes:
        dsum += ((s - avr)/60.0)*((s - avr)/60.0)

      sdist = math.sqrt(dsum / alen)

    return {'org_mon': gt.tm_mon, 'org_day': gt.tm_mday, 'avail_count': alen, 'average': avr/60.0, 'sdist': sdist}

  def invite_page(self, nick):
    parts = {}
    parts['nick'] = nick
    self.response.set_status(404)
    self.write_page("templates/invite.html", parts)

  @classmethod
  def make_pager(cls, cur, nick):
    import cgi

    has_record = twnmodels.SleepTime.check_exists(nick, cur+30)
    if not has_record:
      has_record = twnmodels.WakeTime.check_exists(nick, cur+30)

    ret_link = " - <a href=\"/statuses?nick=%s\">最新 &#9654;|</a>" % cgi.escape(str(nick)) if cur>0 else ''

    if not has_record:
      return "これより古いデータはありません%s" % ret_link

    return "<a href=\"/statuses?nick=%s&amp;ofs=%d\">&#9664; さらに30日前</a>%s" % (cgi.escape(str(nick)), cur+30, ret_link)

class GetGadgetPage(hbase.PageBase):
  def get(self):
    import time
    nick = self.request.get('nick')
    res = self.response

    if not nick:
      self.error(400)
      res.out.write('specify nick')
      return

    self.write_page("templates/get_gadget.html", {'nick': nick})

class GoogleGadgetPage(hbase.PageBase):
  def get(self):
    import time
    nick = self.request.get('nick')
    res = self.response

    if not nick:
       self.error(400)

    self.write_page("templates/ggadget-base.xml", {'nick': nick}, 'text/xml;charset=UTF-8')

class GadgetPage(hbase.PageBase):
  def get(self):
      import time
      nick = self.request.get('nick')
      res = self.response

      if not nick:
        self.error(400)
        res.out.write('specify nick')
        return

 #     twnmodels.SleepTime.put_time('gyuque', 20090320, 26, 51, 20)

      org_sec = time.time() -97200 + 32400
      t = time.gmtime(org_sec)
      full_day_id = int( '%4d%02d%02d' % (t.tm_year, t.tm_mon, t.tm_mday))

      t = time.gmtime(org_sec + 86400)
      wk_full_day_id = int( '%4d%02d%02d' % (t.tm_year, t.tm_mon, t.tm_mday))

      record = twnmodels.SleepTime.gather_user(nick)
      wk_record = twnmodels.WakeTime.gather_user(nick)


      sleep_rec = record[full_day_id]       if full_day_id    in record    else None
      wake_rec  = wk_record[wk_full_day_id] if wk_full_day_id in wk_record else None

      render_params = {
                        'nick': nick,
                        'day10': int(t.tm_mday/10),
                        'day1':  t.tm_mday%10,
                        'slp1000': 'n', 'slp100': 'n', 'slp10': 'n', 'slp1': 'n',
                        'wk1000': 'n', 'wk100': 'n', 'wk10': 'n', 'wk1': 'n',
                        'et100': 0, 'et10': 'n', 'et1': 'n'
                      }

      h = 0
      wh = 0
      if sleep_rec: # has sleep time
        h = sleep_rec['hour']
        if (h>=24):
          h -= 24

        render_params['slp1000'] = int(h/10)
        render_params['slp100' ] = h%10
        render_params['slp10'  ] = int(sleep_rec['min']/10)
        render_params['slp1'   ] = sleep_rec['min']%10

      if wake_rec: # has wake time
        wh = wake_rec['hour']
        render_params['wk1000'] = int(wh/10)
        render_params['wk100' ] = wh%10
        render_params['wk10'  ] = int(wake_rec['min']/10)
        render_params['wk1'   ] = wake_rec['min']%10

      if (sleep_rec and wake_rec): # has both
        if (h>wh):
          wh += 24
        et = (wake_rec['min'] + wh*60) - (sleep_rec['min'] + h*60)
        et_d = int(et*10.0/60.0)
        print >>sys.stderr, str( et_d )

        if (et_d<200):
          render_params['et100' ] = 0 if (et_d<100) else 1
          render_params['et10'  ] = int(et_d/10)%10
          render_params['et1'   ] = et_d%10

      self.write_page("templates/gadget.html", render_params)
