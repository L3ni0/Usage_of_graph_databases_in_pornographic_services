# -*- coding: UTF-8 -*-
import re
from .core import *


class Stars(object):
    def __init__(self, ProxyDictionary, *args):
        self.ProxyDictionary = ProxyDictionary

    def _sortStars(self, sort_by):
        sort_dict = dict()

        if not sort_by:
            return sort_dict

        sort_types = {
            "view": "mv",
            "trend": "t",
            "subs": "ms",
            "alpha": "a",
            "videos": "nv",
            "random": "r",
        }

        for key in sort_types:
            if key in sort_by.lower():
                sort_dict["o"] = sort_types[key]
                return sort_dict

        return sort_dict

    def _craftStarsPage(self, page_num, sort_by):
        payload = dict()

        stars_sort = self._sortStars(sort_by)
        for key in stars_sort:
            payload[key] = stars_sort[key]

        payload["page"] = page_num
        return payload

    def _loadStarsPage(self, page_num, sort_by):
        r = requests.get(
            BASE_URL + PORNSTARS_URL,
            params=self._craftStarsPage(page_num, sort_by),
            headers=HEADERS,
            proxies=self.ProxyDictionary,
            cookies=COOKIES,
        )
        html = r.text

        return BeautifulSoup(html, "lxml")

    def _scrapLiStars(self, soup_data):
        # get div with list of stars (month popular is the 1st)
        div_el = soup_data.findAll(
            "div", {"class": "sectionWrapper", "id": "pornstarsFilterContainer"}
        )[0]
        # get each porn star info (held in list block)
        li_el = div_el.find_all("li")

        return li_el

    def _scrapStarInfo(self, li_el):
        data = {
            "name": None,  # string
            "rank": None,  # integer
            "type": None,  # string
            "videos": None,  # integer
            "views": None,  # string
            "verified": False,  # bool
            "trophy": False,  # bool
            "url": None,  # string
            "photo": None,  # string
        }

        # scrap rank
        for span_tag in li_el.find_all("span", class_="rank_number"):
            try:
                data["rank"] = int(span_tag.text)
            except Exception as e:
                pass

        # scrap name and url
        for a_tag in li_el.find_all("a", href=True):
            try:
                url = a_tag.attrs["href"]

                if isStar(url):
                    data["url"] = BASE_URL + url
                    data["name"] = url.split("/")[-1]

                    break
            except Exception as e:
                pass

        # scrap photo url
        for img_tag in li_el.find_all("img", src=True):
            try:
                photo_url = img_tag.attrs["data-thumb_url"]
                if isStarPhoto(photo_url):
                    data["photo"] = photo_url
                    break
            except Exception as e:
                pass

        # scrap num of videos
        for span_tag in li_el.find_all("span", {"class": "videosNumber"}):
            try:
                data["videos"] = int(span_tag.text.split()[0])
                break
            except Exception as e:
                pass

        # scrap num of views
        for span_tag in li_el.find_all("span", {"class": "viewsNumber"}):
            try:
                views = span_tag.text.split()[0]
                if views[-1].isdigit():
                    data["views"] = int(views)
                else:
                    data["views"] = int(float(views[:-1]) * INT_SUFFIXES[views[-1]])
                break
            except Exception as e:
                pass

        # scrap badges
        for span_tag in li_el.find_all("span", class_="modelBadges"):
            if span_tag.find_all("i", class_="verifiedIcon"):
                data["verified"] = True

            if span_tag.find_all("i", class_="trophyPornStar"):
                data["trophy"] = True

        # scrap type
        try:
            if "pornstar" in data["url"]:
                data["type"] = "pornstar"
            else:
                data["type"] = "model"
        except Exception as e:
            pass

        # return
        return data if None not in data.values() else False

    def getStars(self, quantity=1, page=1, sort_by=None, infinity=False):
        """
        Get pornstar's basic informations.

        :param quantity: number of pornstars to return
        :param page: starting page number
        :param infinity: never stop downloading
        """

        quantity = quantity if quantity >= 1 else 1
        page = page if page >= 1 else 1
        found = 0

        while True:
            for possible_star in self._scrapLiStars(self._loadStarsPage(page, sort_by)):
                data_dict = self._scrapStarInfo(possible_star)

                if data_dict:
                    yield data_dict

                    if not infinity:
                        found += 1
                        if found >= quantity:
                            return

            page += 1

    def getStarsVideos(self, username, type="pornstar"):
        """
        Get pornstar links to videos.

        :param username: username of pornstar/model
        :param type: describe if person is a pornstar or a model. default(pornstar)
        """

        # Input validation
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")

        if type.lower() not in ["pornstar", "model"]:
            raise ValueError("Type must be 'pornstar' or 'model'")

        # Build the URL based on type
        if type.lower() == "pornstar":
            url = BASE_URL + PORNSTAR_URL + username + CHANNEL_VIDEO_URL
        elif type.lower() == "model":
            url = BASE_URL + MODEL_URL + username + CHANNEL_VIDEO_URL

        page = 1

        while True:
            try:
                r = requests.get(
                    url,
                    params={"page": page},
                    headers=HEADERS,
                    proxies=self.ProxyDictionary,
                    cookies=COOKIES,
                )
                html = r.text
                li_el = BeautifulSoup(html, "lxml")

                title = li_el.title.string if li_el.title else ""
                if "Page Not Found" in title:
                    break
                elif title.startswith("Top Pornstars and Models"):
                    raise NameError(f"{type} {username} doesn't exist")

            except requests.RequestException as e:
                raise ConnectionError(f"Failed to fetch page {page}: {e}")

            video_links = li_el.find_all("a", href=re.compile(r"^/view_video\."))
            for link in video_links:
                yield BASE_URL + link["href"]

            page += 1
