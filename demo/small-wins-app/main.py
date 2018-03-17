# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2

from twilio.rest import Client

from google.appengine.ext import ndb
from env_variables import ACCOUNT_SID, AUTH_TOKEN, SERVICE_NUMBER

class RegisteredUser(ndb.Model):
    name = ndb.StringProperty(default="")
    number = ndb.StringProperty(default="")
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Welcome to Small Wins!')


class RegisterNumberHandler(webapp2.RequestHandler):
    def post(self):
        return self.abort(501)


class BroadcastMessageHandler(webapp2.RequestHandler):
    def get(self):
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = self.request.get("message")
        numbers = RegisteredUser.query()
        for user in numbers:
            to_number = user.number
            message = client.messages.create(
                to=to_number,
                from_=SERVICE_NUMBER,
                body=message)

            print(message.sid)
        response = "Message (%s) sent!" % message
        return self.response.write(response)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/register' + '/?(.*)?', RegisterNumberHandler),
    ('/broadcast' + '/?(.*)?', BroadcastMessageHandler),
], debug=True)
