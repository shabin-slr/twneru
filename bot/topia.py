# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2009 Tatsuya Noda <topia@cpan.org> and Satoshi Ueyama <gyuque@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
 
import re

class ParseTwneruText(object):
    verb = re.compile(u'(?:(?P<rel>([0-9]+)分後.*)?(?P<sleep>(?:寝|ね)(?:る|た|ま)|就寝|おやす)|(?P<wake>(?:起|お)き|起床|おは))')
    time = re.compile(u'([0-9]{1,2})[:時]([0-9]{1,2})?')
    date = re.compile(u'([1-9][0-9]?)日')

    yesterday = re.compile(u'昨日|きのう')
    one_day = 3600*24
    jst = 32400

    @classmethod
    def preprocess_rels(cls, text):
        import time
        match = cls.yesterday.search(text)

        if match:
            t = time.time() - cls.one_day + cls.jst
            gt = time.gmtime(t)
            return text.replace(match.group(0), u"%d日" % (gt.tm_mday))

        return text

    @classmethod
    def parse(cls, text):
        import jtrans

        text = cls.preprocess_rels(jtrans.to_han(text))
        match = cls.verb.search(text)
        if not match:
            raise ValueError('parse error')
        elif match.group('sleep'):
             mode = 'sleep'
        elif match.group('wake'):
            mode = 'wake'
        else:
            raise ValueError('parse error')

        rel_min = 0
        if match.group('rel'):
            rel_min = int(match.group(2))

        date = time = None

        if rel_min > 0:
            time = (-1, rel_min)
        else:
            match = cls.time.search(text)
            if match:
                time = tuple([int(i or '0', 10) for i in match.group(1, 2)])

        match = cls.date.search(text)
        if match:
            date = int(match.group(1))
        return date, time, mode
 
#parse = ParseTwneruText.parse
# 
#print parse(u'13日の寝た時刻を24:00に')
#print parse(u'寝た時刻を24時00に')
#print parse(u'寝た')
#print parse(u'21:00に起きた。もっと早く寝るべき')
#print parse(u'12時に寝た')
#print parse(u'きのうは11時におきた')
#try:
#    parse(u'12時に')
#except ValueError, e:
#    print 'error: %s' % e
