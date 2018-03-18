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
import os
import json
import webapp2
import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.api import users

from twilio.rest import Client

from env_variables import ACCOUNT_SID, AUTH_TOKEN, SERVICE_NUMBER


class RegisteredUsers(ndb.Model):
    name = ndb.StringProperty(default="")
    number = ndb.StringProperty(default="")
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)


class Messages(ndb.Model):
    user_key = ndb.KeyProperty()
    content = ndb.TextProperty(default="")
    direction = ndb.StringProperty(default="")  # outbound / inbound
    sid = ndb.StringProperty(default="")
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)


def renderTemplate(template_name, values={}):
    path = os.path.join(os.path.dirname(__file__), 'templates/', template_name)
    template_values = {}
    response = template.render(path, values)
    return response

def ajax_respond(self):
    data_to_send = json.dumps(self.response_dict)
    data_wrapper = self.request.get('callback')
    if data_wrapper:  # for jquery requests
        data_to_send = data_wrapper + "(" + data_to_send + ")"
    return self.response.write(data_to_send)

class MainPage(webapp2.RequestHandler):
    def get(self):
        template = renderTemplate(template_name="index.html")
        return self.response.out.write(template)


class RegisterNumberHandler(webapp2.RequestHandler):
    def post(self):
        new_user = RegisteredUsers()
        new_user.number = str(self.request.get("inbound"))
        new_user.name = str(self.request.get("body")).strip().split(" ")[0]
        new_user.put()
        return self.response.write('Ok!')


class BroadcastMessageHandler(webapp2.RequestHandler):
    def get(self):
        users = RegisteredUsers.query()
        messages = [
            "Hi %s, thanks for signing up! Let's learn a little more about you.",
            "On a scale of 1-10 how much time do you spend engaging with the Barking and Dagenham community?",
            "Where 1 is never and 10 is every day.",
        ]
        values = {
            "users": users,
            "messages": messages
        }
        template = renderTemplate(template_name="broadcast.html", values=values)
        return self.response.out.write(template)

    def post(self):
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = self.request.get("message")
        numbers = RegisteredUsers.query()
        for user in numbers:
            to_number = user.number
            resp = client.messages.create(
                to=to_number,
                from_=SERVICE_NUMBER,
                body=message)
            new_message = Messages()
            new_message.user_key = user.key
            new_message.content = message
            new_message.sid = resp.sid
            new_message.put()
        self.response_dict = {
            "message": "Message sent! (%s)" % message
        }
        return ajax_respond(self)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/register', RegisterNumberHandler),
    ('/broadcast', BroadcastMessageHandler),
], debug=True)
