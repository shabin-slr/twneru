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

import os
import sys
import wsgiref.handlers
from google.appengine.ext             import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp      import template
from google.appengine.api             import memcache
from google.appengine.ext             import db
from google.appengine.api.labs        import taskqueue

import botconfig
import twitterclient
import oauth
import handler_base as hbase


TEST_DATA = '[{"in_reply_to_screen_name":"mayuki_bot","source":"web","geo":null,"truncated":false,"user":{"verified":false,"description":"","geo_enabled":false,"profile_text_color":"4c4943","profile_background_image_url":"http://a3.twimg.com/profile_background_images/61352263/tototaruaruakagakgiaanorliagunn.png","profile_image_url":"http://a1.twimg.com/profile_images/602929754/twitterProfilePhoto_normal.jpg","statuses_count":6951,"following":false,"profile_link_color":"334c2a","profile_background_tile":true,"followers_count":785,"screen_name":"gyuque","profile_background_color":"e9e7e2","friends_count":183,"protected":false,"url":"http://d.hatena.ne.jp/gyuque/","profile_sidebar_fill_color":"cfccbe","location":"Nagareyama Chiba, JAPAN","name":"Ueyama Satoshi","notifications":false,"favourites_count":2864,"id":3608191,"time_zone":"Tokyo","utc_offset":32400,"created_at":"Fri Apr 06 10:16:40 +0000 2007","profile_sidebar_border_color":"ffffff"},"favorited":false,"id":7360023538,"in_reply_to_user_id":27902776,"in_reply_to_status_id":null,"text":"@mayuki_bot \\u5730\\u57df\\u3092\\u5927\\u962a\\u306b\\u8a2d\\u5b9a","created_at":"Mon Jan 04 07:26:53 +0000 2010"},{"in_reply_to_screen_name":"mayuki_bot","source":"web","geo":null,"truncated":false,"user":{"verified":false,"description":null,"geo_enabled":false,"profile_text_color":"000000","profile_background_image_url":"http://s.twimg.com/a/1262113883/images/themes/theme1/bg.png","profile_image_url":"http://a1.twimg.com/profile_images/31917712/bot_normal.png","statuses_count":54,"following":false,"profile_link_color":"555555","profile_background_tile":false,"followers_count":5,"screen_name":"gyuquebot","profile_background_color":"eeeeee","friends_count":1,"protected":false,"url":null,"profile_sidebar_fill_color":"ffffff","location":null,"name":"gyuquebot","notifications":false,"favourites_count":0,"id":9160172,"time_zone":"Hawaii","utc_offset":-36000,"created_at":"Sat Sep 29 16:12:55 +0000 2007","profile_sidebar_border_color":"444444"},"favorited":false,"id":7354505304,"in_reply_to_user_id":27902776,"in_reply_to_status_id":null,"text":"@mayuki_bot 7:77 \\u306b\\u304a\\u304d\\u305f","created_at":"Mon Jan 0403:40:45 +0000 2010"},{"in_reply_to_screen_name":"mayuki_bot","source":"web","geo":null,"truncated":false,"user":{"friends_count":183,"description":"","geo_enabled":false,"notifications":null,"favourites_count":2858,"profile_text_color":"4c4943","profile_background_image_url":"http://a3.twimg.com/profile_background_images/61352263/tototaruaruakagakgiaanorliagunn.png","profile_image_url":"http://a1.twimg.com/profile_images/602929754/twitterProfilePhoto_normal.jpg","following":null,"verified":false,"profile_link_color":"334c2a","profile_background_tile":true,"screen_name":"gyuque","profile_background_color":"e9e7e2","protected":false,"url":"http://d.hatena.ne.jp/gyuque/","profile_sidebar_fill_color":"cfccbe","location":"Nagareyama Chiba, JAPAN","name":"Ueyama Satoshi","followers_count":783,"id":3608191,"statuses_count":6940,"time_zone":"Tokyo","utc_offset":32400,"created_at":"Fri Apr 06 10:16:40 +0000 2007","profile_sidebar_border_color":"ffffff"},"favorited":false,"id":7340643219,"in_reply_to_user_id":27902776,"in_reply_to_status_id":null,"text":"@mayuki_bot 33\\u65e5\\u306f3:33\\u306b\\u306d\\u305f","created_at":"Sun Jan 03 19:40:53 +0000 2010"},{"in_reply_to_screen_name":"mayuki_bot","source":"web","geo":null,"truncated":false,"user":{"description":"","geo_enabled":false,"statuses_count":6930,"profile_text_color":"4c4943","profile_background_image_url":"http://a3.twimg.com/profile_background_images/61352263/tototaruaruakagakgiaanorliagunn.png","followers_count":782,"profile_image_url":"http://a1.twimg.com/profile_images/602929754/twitterProfilePhoto_normal.jpg","following":false,"profile_link_color":"334c2a","profile_background_tile":true,"friends_count":183,"screen_name":"gyuque","profile_background_color":"e9e7e2","notifications":false,"favourites_count":2852,"protected":false,"url":"http://d.hatena.ne.jp/gyuque/","profile_sidebar_fill_color":"cfccbe","location":"Nagareyama Chiba, JAPAN","name":"Ueyama Satoshi","verified":false,"id":3608191,"time_zone":"Tokyo","utc_offset":32400,"created_at":"Fri Apr 06 10:16:40 +0000 2007","profile_sidebar_border_color":"ffffff"},"favorited":false,"id":7337871394,"in_reply_to_user_id":27902776,"in_reply_to_status_id":null,"text":"@mayuki_bot 3\\u65e5\\u306f11:40\\u306b\\u304a\\u304d\\u305f &lt;test&gt;","created_at":"Sun Jan 03 17:52:31 +0000 2010"},{"in_reply_to_screen_name":"mayuki_bot","source":"web","geo":null,"truncated":false,"user":{"friends_count":183,"description":"","geo_enabled":false,"notifications":null,"favourites_count":2858,"profile_text_color":"4c4943","profile_background_image_url":"http://a3.twimg.com/profile_background_images/61352263/tototaruaruakagakgiaanorliagunn.png","profile_image_url":"http://a1.twimg.com/profile_images/602929754/twitterProfilePhoto_normal.jpg","following":null,"verified":false,"profile_link_color":"334c2a","profile_background_tile":true,"screen_name":"gyuque","profile_background_color":"e9e7e2","protected":false,"url":"http://d.hatena.ne.jp/gyuque/","profile_sidebar_fill_color":"cfccbe","location":"Nagareyama Chiba, JAPAN","name":"Ueyama Satoshi","followers_count":783,"id":3608191,"statuses_count":6940,"time_zone":"Tokyo","utc_offset":32400,"created_at":"Fri Apr 06 10:16:40 +0000 2007","profile_sidebar_border_color":"ffffff"},"favorited":false,"id":7268847874,"in_reply_to_user_id":27902776,"in_reply_to_status_id":null,"text":"@mayuki_bot 31\\u65e5\\u306f25:30\\u306b\\u306d\\u305f","created_at":"Fri Jan 01 13:12:23 +0000 2010"}]'

# -- OAuth セットアップページ --
class OAuthSetupPage(hbase.PageBase):
  def get(self):
    from google.appengine.api import users
    if not users.is_current_user_admin():
      res = self.response
      res.clear()
      res.set_status(403)
      res.out.write("<body>please <a href=\"%s\">login</a></body>" % users.create_login_url("/auth"))  
      return

    c = twitterclient.TwitterClient(botconfig.BotConfig["ConsumerKey"], botconfig.BotConfig["ConsumerSecret"])
    toks = c.fetch_request_token()

    self.write_page("templates/auth.html", {'logout_url': users.create_logout_url("/"), 'require_vkey': True, 'vkey_url': toks[0], 'key': toks[1].key, 'secret': toks[1].secret})
    return

  def post(self):
    from google.appengine.api import users
    if not users.is_current_user_admin():
      res = self.response
      res.clear()
      res.set_status(403)
      res.out.write("forbidden")  
      return

    vkey   = self.request.get('vkey')
    key    = self.request.get('key')
    secret = self.request.get('secret')

    c = twitterclient.TwitterClient(botconfig.BotConfig["ConsumerKey"], botconfig.BotConfig["ConsumerSecret"])
    res = c.fetch_access_token(key, secret, vkey)
    nick = None
    if res:
      nick = res.screen_name

    self.write_page("templates/auth.html", {'require_vkey': False, 'access_ok': None != res, 'nick': nick, 'key': res.key, 'secret': res.secret})

# -- タイムライン監視 --
class ObserveService(hbase.ServiceBase):
  def __init__(self):
    self.botm = __import__(botconfig.BotConfig["BotModule"])
    hbase.ServiceBase.__init__(self)

  def get(self):
    import time
    log("Start ObserveService")
    memcache.set('observeservice_last_complete_time', None, 0, 0, 'gq.twitterbot')
    memcache.set('observeservice_last_api_error', -1, 0, 0, 'gq.twitterbot')
    memcache.set('observeservice_last_time', int(time.time()*10.0), 0, 0, 'gq.twitterbot')

    # ban external requests
    if botconfig.BotConfig["Production"]:
      if not self.request.get('_pass') == botconfig.BotConfig["InternalPass"]:
        self.forbidden()
        return

    count = 0
    count_prm = self.request.get('count')
    if count_prm and int(count_prm) > 0:
      count = int(count_prm)

    tlist = None

    if True:
      c = twitterclient.TwitterClient(botconfig.BotConfig["ConsumerKey"], botconfig.BotConfig["ConsumerSecret"])
      c.set_access_key(botconfig.BotConfig["AccessKey"], botconfig.BotConfig["AccessSecret"])

      r = c.fetch_replies(count)
      if int(r.status_code) >= 400:
        memcache.set('observeservice_last_api_error', r.status_code, 0, 0, 'gq.twitterbot')
        self.remote_error(r.status_code, r.content)
        return

      tlist = twitterclient.parse_tweets_json(r.content)
#      log(r.content)
    else:
      tlist = twitterclient.parse_tweets_json(TEST_DATA)

    # API success
    memcache.set('observeservice_last_api_error', None, 0, 0, 'gq.twitterbot')
    memcache.set('observeservice_last_internal_error', 1, 0, 0, 'gq.twitterbot')

    tlist.save_icons_to_memcache()
    tlist.last_id = ManagementData.get_last_reply_id()
    log("  fetched %d tweets" % tlist.length())

    bot = self.botm.TwitterBotImpl()
    bot.process_replies(tlist, self)

    maxid = bot.max_processed_id()
    if tlist.last_id < maxid:
      ManagementData.update_last_reply_id(maxid)

    self.response.out.write("OK")

    memcache.set('observeservice_last_internal_error', None, 0, 0, 'gq.twitterbot')
    memcache.set('observeservice_last_complete_time', int(time.time()*10.0), 0, 0, 'gq.twitterbot')
    return hbase.ServiceBase.get(self)

  @classmethod
  def last_status(cls):
    import time
    lt = memcache.get('observeservice_last_time', 'gq.twitterbot')
    ct = memcache.get('observeservice_last_complete_time', 'gq.twitterbot')
    if not lt:
      return None

    now = int(time.time()*10.0)
    stat = LastServiceStatus()
    stat.rel_time  = now - lt
    stat.api_error = memcache.get('observeservice_last_api_error', 'gq.twitterbot')
    stat.internal_error = memcache.get('observeservice_last_internal_error', 'gq.twitterbot')

    if ct:
      stat.elapsed_time = ct - lt

    return stat

  def append_tweet(self, text):
    if not botconfig.BotConfig["Production"]:
      log("  TaskQueue <- tweet: %s" % text.encode('Shift_JIS'))

    if botconfig.BotConfig["NoReply"]:
      log("  * ignored tweet task")
      return

    taskqueue.add(url = '/worker',  params = {'task': 'tweet', 'text': text, '_pass': botconfig.BotConfig["InternalPass"]})

  def append_update_icon_task(self):
    import time
    t = time.localtime()
    tid = "updateicon-%04d%02d%02d%02d%02d" % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)

    try:
      taskqueue.add(url = '/worker', name = tid, params = {'task': 'update_icon', '_pass': botconfig.BotConfig["InternalPass"]})
    except taskqueue.TaskAlreadyExistsError:
      log('update_icon task already exists')
    except taskqueue.TombstonedTaskError:
      log('update_icon task raised TombstonedTaskError')

  def append_call_task(self, f):
    taskqueue.add(url = '/worker', params = {'task': 'call_function', 'func': f, '_pass': botconfig.BotConfig["InternalPass"]})

class LastServiceStatus(object):
  rel_time       = 0
  elapsed_time   = 0
  api_error      = None
  internal_error = None

# -- TaskQueue 実行 --
class RunTaskService(hbase.ServiceBase):
  twc = None

  def ensure_twitter_client(self):
    if not self.twc:
      self.twc = twitterclient.TwitterClient(botconfig.BotConfig["ConsumerKey"], botconfig.BotConfig["ConsumerSecret"])
      self.twc.set_access_key(botconfig.BotConfig["AccessKey"], botconfig.BotConfig["AccessSecret"])

    return self.twc

  def post(self):
    if not self.request.get('_pass') == botconfig.BotConfig["InternalPass"]:
      self.forbidden()
      return

    task_type = self.request.get('task')

    if task_type == "tweet":
      self.do_tweet_task(self.request.get('text'))
    elif task_type == "update_icon":
      self.do_update_icon_task()
    elif task_type == "call_function":
      self.do_call_task(self.request.get('func'))

    self.response.out.write("OK")

  def do_tweet_task(self, text):
    if botconfig.BotConfig["Production"]:
      res = self.ensure_twitter_client().post_tweet(text)
      log("send tweet: %d" % int(res.status_code))

  def do_update_icon_task(self):
    imap = twitterclient.TweetList.load_icons_from_memcache()
    if imap:
      botm = __import__(botconfig.BotConfig["BotModule"])
      botm.process_icon_map(imap)

    twitterclient.TweetList.clear_icons_cache()


  def do_call_task(self, f):
    func = __import__(botconfig.BotConfig["BotModule"]).__getattribute__(f)
    func()

def log(s):
  print >>sys.stderr, s

# -- 管理データ用モデル --
class ManagementData(db.Model):
  last_reply_id = db.IntegerProperty(required=False)

  @classmethod
  def ensure_entry(cls):
    a = cls.all()
    entry = None
    if (a.count() < 1):
      entry = cls(last_reply_id = 0)
      entry.put()
    else:
      entry = a.fetch(limit = 1)[0]

    return entry

  @classmethod
  def get_last_reply_id(cls):
    entry = cls.ensure_entry()
    return entry.last_reply_id

  @classmethod
  def update_last_reply_id(cls, max_id):
    entry = cls.ensure_entry()
    entry.last_reply_id = max_id
    entry.put()

# -- 初期化 --
def main():
  handlers = [
      ('/observe', ObserveService),
      ('/worker',  RunTaskService),
      ('/auth', OAuthSetupPage)
    ]

  # production mode?
  pro = botconfig.BotConfig["Production"]

  # register additional servlets
  botm = __import__(botconfig.BotConfig["BotModule"])
  botm.register_custom_servlets(handlers)

  application = webapp.WSGIApplication(handlers, debug = (not pro))
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
