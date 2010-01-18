# coding: utf-8

z_list = [u"：", u"０", u"１", u"２", u"３", u"４", u"５", u"６", u"７", u"８", u"９"]
h_list = [u":", u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9"]

zhmap = {}
for (z, h) in zip(z_list, h_list):
  zhmap[z] = h

# generic mapper
def map_text(mapper, src):
  dest = []
  for c in src:
    dest.append(mapper[c] if (c in mapper) else c)

  return ''.join(dest)

# specific mapper
def to_han(src):
  return map_text(zhmap, src)
