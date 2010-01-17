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
from google.appengine.ext             import webapp
from google.appengine.ext.webapp      import template

class ServiceBase(webapp.RequestHandler):
  def remote_error(self, status, msg):
    print >>sys.stderr, "* Remote Server Error"
    print >>sys.stderr, "Status: " + str(status)
    print >>sys.stderr, "Message: " + msg
    self.response.set_status(500)

  def forbidden(self):
    self.response.set_status(403)
    self.response.out.write("403 Forbidden")

  def get(self):
    return

class PageBase(webapp.RequestHandler):
  def write_page(self, template_file, params, content_type = None):
    path = os.path.join(os.path.dirname(__file__), template_file)
    if content_type:
      self.response.headers['Content-Type'] = content_type
    self.response.out.write(template.render(path, params))

