# -*- coding: utf-8 -*-
import topia

parse = topia.ParseTwneruText.parse

print parse(u'21:00に起きた。日食だ!!')
print parse(u'12時に寝た')
print parse(u'きのうは11時におきた')
print parse(u'15分後に寝る')