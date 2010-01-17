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
import twncalendar

DAYNAMES   = ['月','火','水','木','金','土','日']
MARKER_IMG    = "images/pin.gif"
WK_MARKER_IMG    = "images/pin2.gif"
NA_MARKER_IMG = "images/na.gif"

class DayChart:
  def __init__(self, lc, og, num):
    self.location   = lc
    self.origin     = og
    self.num_days   = num
    
  def generate_table(self, records, wk_records):

    cols = []
    mon_heads = []
    mon_spans = 0
    prev_mon = -1

    for ofs in range(self.num_days):
      ot = self.origin - ofs * 86400
      wake_ot = self.origin - ofs * 86400 + 86400

      ts = time.gmtime(ot)
      wake_ts = time.gmtime(wake_ot)

      d_y = ts.tm_year
      d_m = ts.tm_mon
      d_d = ts.tm_mday

      mon_spans += 1
      if (d_m <> prev_mon):
        if (prev_mon >= 0):
          mon_heads.append(mon_spans)
          mon_spans = 1
        else:
          mon_spans = 0

        prev_mon = d_m

      col_class = ts.tm_wday
      day_id    = ('%02d' % d_m) + ('%02d' % d_d)
      day_label = ('%02d' % d_d) + '<br />' + DAYNAMES[ts.tm_wday]
      full_day_id = int(str(d_y) + day_id)

      wake_day_id = ('%02d' % wake_ts.tm_mon) + ('%02d' % wake_ts.tm_mday)
      full_day_id_for_wake = int(str(wake_ts.tm_year) + wake_day_id)

      colobj = DayChartCol(day_label, '%02d' % wake_ts.tm_mday, col_class)
      colobj.show_g = ts.tm_wday==0
      colobj.mday = d_d
      colobj.sun_times = twncalendar.SUN_TABLES[self.location][day_id]
      colobj.sleep_time =    records[full_day_id] if full_day_id in    records else None
      colobj.wake_time  = wk_records[full_day_id_for_wake] if full_day_id_for_wake in wk_records else None
      cols.append(colobj)

    cols.reverse()

    mon_heads.append(mon_spans)
    if len(mon_heads) == 1:
      mon_heads[0] = 30

    mon_heads.reverse()
    return {
             'chart_js': 'var PIX_PER_MIN = %f; TIMES = [%s]; WTIMES = [%s]; DATES = [%s];' % (PIX_PER_MIN,
                                                                                ",".join(map(lambda c:str(c.get_js_val()), cols)),
                                                                                ",".join(map(lambda c:str(c.get_wake_js_val()), cols)),
                                                                                ",".join(map(lambda c:str(c.get_mday()), cols))  ),
             'mon_heads': "\n".join( self.make_mon_header(mon_heads, prev_mon) ),
             'headings': "\n".join( map(lambda c:c.get_th_html(), cols) ),
             'wake_headings': "\n".join( map(lambda c:c.get_wake_th_html(), cols) ),
             'cols'    : "\n".join( map(lambda c:c.get_html(),    cols) )
           }

  def make_mon_header(self, spans, last_mon):
    list = []

    for s in spans:
      list.append('<th colspan="%d">%d月</th>' % (s, last_mon))
      last_mon = (last_mon%12)+1

    return list

class DayChartCol:
  def __init__(self, lb, wl, cc):
    self.sleep_time = None
    self.wake_time = None
    self.show_g = False
    self.col_label = lb
    self.wake_col_label = wl
    self.col_class = cc
    self.sun_times = twncalendar.SUN_TABLES['tokyo']['0101']

  def get_js_val(self):
    return self.time_label(self.sleep_time) if self.sleep_time else -1

  def get_wake_js_val(self):
    return self.time_label_d(self.wake_time) if self.wake_time else -1

  def get_mday(self):
    return self.mday

  def get_th_html(self):
    return '<th>'+self.col_label+'</th>'

  def get_wake_th_html(self):
    return '<th>'+self.wake_col_label+'</th>'

  def get_html(self):
    g_open  = '<div class="g">' if self.show_g else ''
    g_close = '</div>' if self.show_g else ''
    ofsx = str(self.col_class * -26) + 'px'

    sunset_t  = self.sun_times[1]
    sunrise_t = self.sun_times[0]
    sunset_y  = -178 + ( (int(sunset_t/100)-16)*60 + (sunset_t%100) )*PIX_PER_MIN
    sunrise_y = 264 + ( (int(sunrise_t/100)-8 )*60 + (sunrise_t%100) )*PIX_PER_MIN

    mks = []
    if self.sleep_time:
      mks.append('<img alt="%s 就寝 " class="marker" style="top: %dpx;" src="%s" />' % (self.time_label(self.sleep_time), self.calc_marker_pos(), MARKER_IMG) )
    if self.wake_time:
      mks.append('<img alt=" %s 起床" class="marker" style="top: %dpx;" src="%s" />' % (self.time_label(self.wake_time ), self.calc_wake_marker_pos(), WK_MARKER_IMG) )

    if (len(mks) == 0):
      mks.append( '<img alt="N/A" class="na-mk" src="%s" />' % NA_MARKER_IMG )


    return '<td style="background-position: '+ofsx+' '+str(sunrise_y)+'px;"><div style="background-position: '+ofsx+' '+str(sunset_y)+'px;" class="wrap">'+g_open+''.join(mks)+g_close+'</div></td>'

  def calc_marker_pos(self):
    return int(((self.sleep_time['hour']-15) * 60 + self.sleep_time['min']) * PIX_PER_MIN) - 4

  def calc_wake_marker_pos(self):
    ofs = 0 if not self.sleep_time else -7
    return int(((self.wake_time['hour']+9) * 60 + self.wake_time['min']) * PIX_PER_MIN) - 4 + ofs

  def time_label(self, t):
    return '%02d%02d' % (t['hour'], t['min'])

  def time_label_d(self, t):
    return '%d' % (t['hour']*100 + t['min'])

PIX_PER_MIN = 24.0 / 60.0

