import re
import os
import requests
from lxml import etree
import traceback
import unicodecsv
from datetime import datetime

'''
    Manual Scrapping Weibo data
    Created by 01/22/2017
'''


def counted(f):
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return f(*args, **kwargs)
    wrapped.calls = 0
    return wrapped


class Weibo(object):
    _info_url = 'http://weibo.cn/%d/info'
    _filter_url = 'http://weibo.cn/u/%d?filter=%d&page=1'
    _page_url = 'http://weibo.cn/u/%d?filter=%d&page=%d'
    _following_url = 'http://weibo.cn/%d/follow?page=%d'
    # new cookie
    _cookies = "_T_WM=5377d3c2f295406e00eee8c16e4110b4; SUB=_2A251yB5LDeRxGeBP7FEQ8S3NzjmIHXVXMqIDrDV6PUJbkdBeLRSlkW1PZUvnOpLRkM2C2iLZwQFZVIbucg..; SUHB=0P1MYFqrSXqk9I; SCF=AumzimxfGzBaR_By2JTYpDcyzzhMifJeUaRt3A_IHTmB-V56YKtRQ5zjILFBWvVeEP5jnPdOws2MwwzC0Mg1gzg.; SSOLoginState=1489792539"
    _cookie = {k: v for cookie in _cookies.split(';') for [k, v] in [cookie.split('=')]}

    # initialize weibo parameters
    def __init__(self, filter=0):
        self.filter = filter

    # start scrapping
    def scrap_user(self, user_id):
        try:
            self._clear_countings()
            self._get_user_name(user_id)
            self._get_user_info(user_id)
            self._get_post_likes_info(user_id)
            print('=' * 40)
        except Exception as e:
            print("Error: ", e)

    def _clear_countings(self):
        self.original_weibo_filter = self.filter    # 0: all weibo posts, 1: only original weibo posts
        self.userName = ''  # user name
        self.weiboNum = 0  # number of weibo posts
        self.scrapped_weiboNum = 0  # number of weibo posts scrapped
        self.following = 0  # number of followings
        self.followers = 0  # number followers
        self.weibos = []  # contents of weibo posts
        self.num_like = []  # number of posts that this person liked
        self.num_forwarding = []  # number of posts that this person forwarded
        self.num_comment = []  # number of comments

    # get user name
    def _get_user_name(self, user_id):
        try:
            url = self._info_url % user_id
            html = self.weibo_request(url)
            # self.check_requests_time()
            selector = etree.HTML(html)
            userName = selector.xpath("//title/text()")[0]
            self.userName = userName[:-3].encode('gbk')
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    # user weibo posts, followers,
    def _get_user_info(self, user_id):
        num_wb = 0
        try:
            url = self._filter_url % (user_id, self.original_weibo_filter)
            html = self.weibo_request(url)
            # self.check_requests_time()
            selector = etree.HTML(html)
            pattern = r"\d+\.?\d*"

            # number of weibo posts
            str_wb = selector.xpath("//div[@class='tip2']/span[@class='tc']/text()")[0]
            guid = re.findall(pattern, str_wb, re.S | re.M)
            for value in guid:
                num_wb = int(value)
                break
            self.weiboNum = num_wb

            # number of followings
            str_gz = selector.xpath("//div[@class='tip2']/a/text()")[0]
            guid = re.findall(pattern, str_gz, re.M)
            self.following = int(guid[0])

            # number of followers
            str_fs = selector.xpath("//div[@class='tip2']/a/text()")[1]
            guid = re.findall(pattern, str_fs, re.M)
            self.followers = int(guid[0])
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    # Get weibo likes, forwarding posts, comments
    def _get_post_likes_info(self, user_id):
        try:
            url = self._filter_url % (user_id, self.original_weibo_filter)
            html = self.weibo_request(url)
            # self.check_requests_time()
            selector = etree.HTML(html)
            if not selector.xpath('//input[@name="mp"]'):
                pageNum = 1
            else:
                pageNum = int(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
            pattern = r"\d+\.?\d*"
            for page in range(1, pageNum + 1):
                url2 = self._page_url % (user_id, self.original_weibo_filter, page)
                html2 = self.weibo_request(url2)
                # self.check_requests_time()
                selector2 = etree.HTML(html2)
                info = selector2.xpath("//div[@class='c']")
                if len(info) > 3:
                    for i in range(0, len(info) - 2):
                        self.scrapped_weiboNum += 1

                        # weibo comments
                        str_t = info[i].xpath("div/span[@class='ctt']")
                        weibos = str_t[0].xpath('string(.)').encode('gbk', 'ignore')
                        self.weibos.append(weibos)

                        # number of likes
                        str_zan = info[i].xpath("div/a/text()")[-4]
                        guid = re.findall(pattern, str_zan, re.M)
                        num_zan = int(guid[0])
                        self.num_like.append(num_zan)

                        # number of forwarding posts
                        forwarding = info[i].xpath("div/a/text()")[-3]
                        guid = re.findall(pattern, forwarding, re.M)
                        num_forwarding = int(guid[0])
                        self.num_forwarding.append(num_forwarding)

                        # number of comments
                        comment = info[i].xpath("div/a/text()")[-2]
                        guid = re.findall(pattern, comment, re.M)
                        num_comment = int(guid[0])
                        self.num_comment.append(num_comment)

            if self.original_weibo_filter == 0:
                print('Total number of scrapped posts: ' + str(self.scrapped_weiboNum))
            else:
                print('Total number of scrapped posts: ' + str(self.weiboNum) +
                      ', where number of original posts is: ' + str(self.scrapped_weiboNum))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    @counted
    def weibo_request(self, url):
        return requests.get(url, cookies=self._cookie).content

    def get_1stlayer_info(self, user_id, threshold, save_to_csv=True):
        """
            get user_id's 1st layer friends' weibo info and store them in a folder
            :param threshold: number of fans threshold. weibos of users fans above or equal to threshold will not be considered
            :param save_to_csv: whether save the results to csv file
            :return: None
        """
        start_time = datetime.utcnow()
        print("get userId %s following's information..." % user_id)
        followings = self.get_following_info(user_id, to_csv=save_to_csv)
        folder_name = '{}_following'.format(user_id)
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        ticker = 0
        os.chdir(folder_name)
        print("start parsing following's weibo posts...")
        for following in followings:
            if len(following) == 3 and following[2].isdigit():
                if int(following[2]) < threshold:
                    ticker += 1
                    user_id = int(following[0])
                    print("Parsing username: ", following[1])   #.decode('GBK'))
                    self.scrap_user(user_id)
                    self.save_results(user_id)
                else:
                    print("Skip parsing username: ", following[1])

            if ticker % 10 == 0:
                print("{} of {} followings' weibo posts parsed...".format(ticker, len(followings)))
        os.chdir('..')
        print(datetime.utcnow() - start_time)

        print ("%s weibo requests have been called in total" % self.weibo_request.calls)

    def get_following_info(self, user_id, to_csv=False):
        """
            get a list of [name, id, nb_fans] the user is following
            :param to_csv: True if wants an csv output;
            :return: following_info: list of [name, id, nb_fans]
        """
        following_url = self._following_url % (user_id, 1)
        # number of followers
        html = self.weibo_request(following_url)
        # self.check_requests_time()
        selector = etree.HTML(html)
        selector_span = selector.xpath("//span[@class='tc']")
        nb_following = int(re.findall(r"\d+\.?\d*", selector_span[0].text)[0])
        # number of pages
        pages = int(nb_following/10)
        following_info = [['name', 'id', 'nb_fans']]

        # parse each page
        for page in range(1, pages+1):
            url = self._following_url % (user_id, page)
            html = self.weibo_request(url)
            # self.check_requests_time()
            selector = etree.HTML(html)
            # all td tags
            selector_tdtag = selector.xpath("//td[@valign='top']")
            for tag in selector_tdtag:
                tag_a = tag.xpath("a")
                tag_br = tag.xpath("br")
                # following name, id, nb_fans
                uid, name, nb_fans = None, None, None
                for tag_a1 in tag_a:
                    if tag_a1.text:
                        tag_a1_href = tag_a1.attrib['href']
                        if '?uid=' in tag_a1_href:
                            uid = re.findall(r"uid=\d*&", tag_a1_href)[0]
                            uid = re.findall(r"\d+\d*", uid)[0]
                        else:
                            name = tag_a1.text
                if tag_br:
                    tag_br1 = etree.tostring(tag_br[0]).decode('gbk')
                    nb_fans = tag_br1.split(';')[-2].split('&')[0]  # number of fans
                if uid or name or nb_fans:
                    following_info.append([uid, name, nb_fans])

        print("%s weibo requests have been called in get_following process" % self.weibo_request.calls)

        if to_csv:
            csv_filename = "{}_following_info.csv".format(user_id)
            with open(csv_filename, 'wb') as f:
                csv_writer = unicodecsv.writer(f, delimiter=',')
                csv_writer.writerows(following_info)
                print("file {} created...".format(csv_filename))
        return following_info

    # def check_requests_time(self):
    #     """
    #     make sure the request frequency is under 900 requests/hour
    #     :return:
    #     """
    #     time_elapsed = datetime.utcnow() - self.start_time
    #     req_time_ratio = self.num_requests/time_elapsed
    #     if req_time_ratio > 900/3600: # 900 requests per hour
    #         time.sleep(3600/900*self.num_requests-time_elapsed)
    #     return None

    ''' Save restuls in TXT file'''
    def save_results(self, user_id):
        save_file_name = "weibo/{0}.txt".format(user_id) if not self.original_weibo_filter \
            else "weibo/{0}_filter.txt".format(user_id)

        if self.original_weibo_filter == 1:
            resultHeader = '\n\noriginal weibo content: \n'
        else:
            resultHeader = '\n\nweibo content: \n'
        result = 'user_info or user_nickname: ' + self.userName.decode('GBK') \
                 + '\nuser_id: ' + str(user_id) \
                 + '\nweibo_Num: ' + str(self.weiboNum) \
                 + '\nNum_followings: ' + str(self.following) \
                 + '\nNum_followers: ' + str(self.followers) \
                 + resultHeader
        for i in range(1, self.scrapped_weiboNum + 1):
            text = str(i) + ':' + self.weibos[i - 1].decode('GBK') + '\n' + 'num_like: ' + str(
                self.num_like[i - 1]) + '   forwardings: ' + str(self.num_forwarding[i - 1]) + ' comments: ' + str(
                self.num_comment[i - 1]) + '\n\n'
            result += text
        if not os.path.isdir('weibo'):
            os.mkdir('weibo')
        f = open(save_file_name, "w")
        f.write(result)
        f.close()
        print('saved data to file: %s' % save_file_name)


# ---------------------------- Main Function -------------------------- #
if __name__ == "__main__":
    user_id = 1917901324
    post_filter = 0
    wb = Weibo(post_filter)
    wb.get_1stlayer_info(user_id, threshold=3000)

    print('username: ', wb.userName.decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_posts: ', str(wb.weiboNum))
    print('weibo_num_followings: ', str(wb.following))
    print('weibo_num_followers: ', str(wb.followers))
    print('first weibo: ', wb.weibos[0].decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_likes: ', str(wb.num_like[0]))
    print('weibo_num_forwardings:', str(wb.num_forwarding[0]))
    print('weibo_num_comments: ', str(wb.num_comment[0]))
    # wb.save_results()
