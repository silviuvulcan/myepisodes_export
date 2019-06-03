#!/usr/bin/env python
# -*- coding: utf-8 -*-
# From: https://github.com/maximeh/script.myepisodes/
# Author: maximeh

from BeautifulSoup import BeautifulSoup
import cookielib
import re
import urllib, urllib2, urlparse

MYEPISODE_URL = "http://www.myepisodes.com"


class MyEpisodes(object):

    def __init__(self, userid, password):
        self.userid = userid
        self.password = password
        self.shows = []
        self.show_list = []

        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', 'Lynx/2.8.1pre.9 libwww-FM/2.14')
        ]

    def send_req(self, url, data=None):
        try:
            response = self.opener.open(url, data)
            return ''.join(response.readlines())
        except:
            return None

    def login(self):
        login_data = urllib.urlencode({
            'username': self.userid,
            'password': self.password,
            'action': "Login",
            })
        login_url = "%s/%s" % (MYEPISODE_URL, "login.php")
        data = self.send_req(login_url, login_data)
        # Quickly check if it seems we are logged on.
        if (data is None) or (self.userid not in data):
            return False

        return True

    #let id be url now // API changes in myepisodes
    def get_show_list(self):
        # Populate shows with the list of show_ids in our account
        wasted_url = "%s/%s" % (MYEPISODE_URL, "life_wasted.php")
        data = self.send_req(wasted_url)
        if data is None:
            return False
        soup = BeautifulSoup(data)
        mylist = soup.find("table", {"class": "mylist"})
        mylist_tr = mylist.findAll("tr")[1:-1]
        for row in mylist_tr:
            link = row.find('a', {'href': True})
            showid = link.get('href')
            self.shows.append(str(showid))
            self.show_list.append({'id': str(showid), 'name': link.string})
        return True

    #let id be url now // API changes in myepisodes
    def get_show_data(self, show_id):
        # Try to add the show to your account.
        url = 'http://www.myepisodes.com/ajax/service.php?mode=view_epsbyshow' #<-update here
        show_id_num = re.search('epsbyshow\/(\d+)\/', show_id).group(1)
        post = urllib.urlencode({'showid':show_id_num})
        data = self.send_req(url, post)
        if data is None:
            return False
        soup = BeautifulSoup(data)
        out = {}
        mylist = soup.find("table", {"class": "mylist"})
        mylist_tr = mylist.findAll("tr", {"class": ["odd", "even"]})
        for row in mylist_tr:
            episode = row.find('td', {'class': "longnumber"})
            episode_data = episode.string.split('x')
            acquired = row.find('input', attrs={'type': "checkbox", "name": re.compile("^A")})
            is_acquired = True if acquired.get('checked') else False
            viewed = row.find('input', attrs={'type': "checkbox", "name": re.compile("^V")})
            is_viewed = True if viewed.get('checked') else False
            out.setdefault(episode_data[0], [])
            out[episode_data[0]].append({'episode': episode_data[1], 'acquired': is_acquired, 'viewed': is_viewed})
        return out

    def get_seen_episodes(self, show_id):
        data = self.get_show_data(show_id)
        out = []
        for season in data:
            episodes_data = [{'number': int(episode['episode'])} for episode in data[season] if episode['viewed']]
            if episodes_data:
                out.append({'number': int(season), 'episodes': episodes_data})
        return out

    def get_collection_episodes(self, show_id):
        data = self.get_show_data(show_id)
        out = []
        for season in data:
            episodes_data = [{'number': int(episode['episode']) } for episode in data[season] if episode['acquired']]
            if episodes_data:
                out.append({'number': int(season), 'episodes': episodes_data})
        return out
