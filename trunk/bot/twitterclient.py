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
import oauth
from google.appengine.api import urlfetch

TWITTER_REQUEST_TOKEN_URL = "http://twitter.com/oauth/request_token"
TWITTER_ACCESS_TOKEN_URL  = "http://twitter.com/oauth/access_token"
TWITTER_AUTHORIZE_URL     = "http://twitter.com/oauth/authorize"

TWITTER_REPLIES_URL       = "http://twitter.com/statuses/replies.json"
TWITTER_UPDATE_URL        = "http://twitter.com/statuses/update.json"

TWITTER_CLIENT_NATSULION  = 1

class TwitterClient(object):
  def __init__(self, okey, osecret):
    self.oKey      = okey
    self.oSecret   = osecret
    self.oConsumer = oauth.OAuthConsumer(okey, osecret)

  # OAuth 1: Get Request Token
  def fetch_request_token(self):
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.oConsumer, http_url = TWITTER_REQUEST_TOKEN_URL)
    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.oConsumer, None)

    res = self.send_oauth_request(oauth_request)
    return (TWITTER_AUTHORIZE_URL +'?'+ res.content, oauth.OAuthToken.from_string(res.content))

  # OAuth 2: Get Access Token
  def fetch_access_token(self, a_k, a_s, a_v):
    tok = oauth.OAuthToken(a_k, a_s)
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.oConsumer, token=tok, verifier=a_v, http_url=TWITTER_ACCESS_TOKEN_URL)
    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.oConsumer, None)
    res = self.send_oauth_request(oauth_request)

    if int(res.status_code) < 400:
      return oauth.OAuthToken.from_string(res.content)

    return None

  def set_access_key(self, k, s):
    self.access_token = oauth.OAuthToken(k, s)

  # Twitter API

  def fetch_replies(self, count = 0):
    prms = None if count<=20 else {'count': str(count)}
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.oConsumer, token=self.access_token, http_url=TWITTER_REPLIES_URL, parameters=prms)

    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.oConsumer, self.access_token)

    if prms:
      oauth_request.http_url = "%s?count=%d" % (oauth_request.http_url, count)

    res = self.send_oauth_request(oauth_request)

    return res

  def post_tweet(self, text):
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.oConsumer, http_method = 'POST', token=self.access_token, http_url=TWITTER_UPDATE_URL, parameters={'status': text.encode('utf-8')})
    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.oConsumer, self.access_token)

    return self.send_oauth_request(oauth_request, oauth_request.to_postdata())

  def send_oauth_request(self, oreq, post_body = None):
    return urlfetch.fetch(url = oreq.http_url,
                   payload    = post_body,
                   method     = oreq.http_method,
                   headers    = {} if post_body else oreq.to_header() )

#   print >>sys.stderr, "---------"
#   print >>sys.stderr, res.status_code
#   print >>sys.stderr, res.content

def parse_tweets_json(src):
  from django.utils import simplejson

  tlist = TweetList()
  tweets = simplejson.loads(src)
  for t in tweets:
    tobj = Tweet()
    tobj.nick = t['user']['screen_name']
    tobj.icon = t['user']['profile_image_url']
    tobj.id   = int(t['id'])
    tobj.text = t['text']
    tobj.timestamp = t['created_at']

    if ('source' in t) and ('natsulion' in t['source']):
      tobj.client = TWITTER_CLIENT_NATSULION

    tlist.append(tobj)

  return tlist

class TweetList(object):
  def __init__(self):
    self.last_id = 0
    self.list = []

  def newer(self):
    return filter(lambda t: t.id > self.last_id, self.list)

  def append(self, t):
    self.list.append(t)

  def length(self):
    return len(self.list)

  def save_icons_to_memcache(self):
    from google.appengine.api import memcache

    pairs = None
    if len(self.list) > 0:
      pairs = []
      umap = {}
      for t in self.list:
        if not t.nick in umap:
          pairs.append( (t.nick, t.icon) )
          umap[t.nick] = True

    memcache.set("twitterbot_icons_list_temp", pairs)

  @classmethod
  def clear_icons_cache(cls):
    from google.appengine.api import memcache
    memcache.set("twitterbot_icons_list_temp", None)

  @classmethod
  def load_icons_from_memcache(cls):
    from google.appengine.api import memcache

    pairs = memcache.get("twitterbot_icons_list_temp")
    if not pairs:
      return None

    imap = {}
    for p in pairs:
      imap[p[0]] = p[1]

    return imap

class Tweet(object):
  text   = None
  icon   = None
  nick   = None
  client = 0
  id        = 0
  timestamp = None

  def __init__(self):
    self.user_data = {}