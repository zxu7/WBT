import re
import os
import requests
from lxml import etree
import traceback
import math
import csv
import unicodecsv
import time

# new cookie
cookies = "_T_WM=a85ab53b99784a1487b65c1751d50ed6; ALF=1492200360; SCF=AmES_i-r8gJgsJjWSlNRlA0B0d_5cKUigF8UCDVgKNU5lVZExrA_Zz7amrYoln4KQN8FRa3lRPUkXewngGortkc.; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5M7oS2VRfSs0gDk6TRvlOr5JpX5o2p5NHD95Qp1K.41KqfSoz0Ws4DqcjTCs8EMrLkg.ykgG-t; SUB=_2A251ze-TDeTxGedH4lsY9ivKyT-IHXVXMfHbrDV6PUJbkdBeLRikkW0mwCsqBtxLjbyAh1GZT8ZUut0axg..; SUHB=0z1R9Lxp_Izg83; SSOLoginState=1489608643"
cookie = {k:v for cookie in cookies.split(';') for (k, v) in [cookie.split('=')]}

# start time
start_time = time.time()

'''
    Manual Scrapping Weibo data
    Created by 01/22/2017
'''


class Weibo(object):
    _info_url = 'http://weibo.cn/%d/info'
    _filter_url = 'http://weibo.cn/u/%d?filter=%d&page=1'
    _page_url = 'http://weibo.cn/u/%d?filter=%d&page=%d'
    _following_url = 'http://weibo.cn/%d/follow?page=%d'
    _cookie = cookie

    # initialize weibo parameters
    def __init__(self, user_id, filter=0):
        self.user_id = user_id  # user id, id is usually a number. eg: id for "Dear-迪丽热巴" is 1669879400
        self.original_weibo_filter = filter  # 0: all weibo posts, 1: only original weibo posts
        self.userName = ''  # user name
        self.weiboNum = 0  # number of weibo posts
        self.scrapped_weiboNum = 0  # number of weibo posts scrapped
        self.following = 0  # number of followings
        self.followers = 0  # number followers
        self.weibos = []  # contents of weibo posts
        self.num_like = []  # number of posts that this person liked
        self.num_forwarding = []  # number of posts that this person forwarded
        self.num_comment = []  # number of comments
        self.num_requests = 0  # number of requests sent
        self.save_file_name = "weibo/{0}.txt".format(self.user_id) if not self.original_weibo_filter \
            else "weibo/{0}_filter.txt".format(self.user_id)

    # start scrapping
    def start(self):
        try:
            Weibo.get_user_name(self)
            Weibo.get_user_info(self)
            Weibo.get_weibo_info(self)
            print('=' * 40)
        except Exception as e:
            print("Error: ", e)

    # get user name
    def get_user_name(self):
        try:
            url = self._info_url % (self.user_id)
            html = requests.get(url, cookies=Weibo._cookie).content
            self.num_requests += 1
            self.check_requests_time()
            selector = etree.HTML(html)
            userName = selector.xpath("//title/text()")[0]
            self.userName = userName[:-3].encode('gbk')
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    # user weibo posts, followers,
    def get_user_info(self):
        num_wb = 0
        try:
            url = self._filter_url % (self.user_id, self.original_weibo_filter)
            html = requests.get(url, cookies=Weibo._cookie).content
            self.num_requests += 1
            self.check_requests_time()
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
    def get_weibo_info(self):
        try:
            url = self._filter_url % (self.user_id, self.original_weibo_filter)
            html = requests.get(url, cookies=Weibo._cookie).content
            self.num_requests +=1
            self.check_requests_time()
            selector = etree.HTML(html)
            if not selector.xpath('//input[@name="mp"]'):
                pageNum = 1
            else:
                pageNum = int(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
            pattern = r"\d+\.?\d*"
            for page in range(1, pageNum + 1):
                url2 = self._page_url % (self.user_id, self.original_weibo_filter, page)
                html2 = requests.get(url2, cookies=Weibo._cookie).content
                self.num_requests +=1
                self.check_requests_time()
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

    def get_following_info(self, to_csv = False):
        """
        get a list of [name, id, nb_fans] the user_id is following
        :param to_csv: True if wants an csv output;
        :return: following_info: list of [name, id, nb_fans]
        """
        url = self._following_url % (self.user_id, 1)
        # number of followers
        html = requests.get(url, cookies=cookie).content
        self.num_requests +=1
        self.check_requests_time()
        selector = etree.HTML(html)
        selector_span = selector.xpath("//span[@class='tc']")
        nb_following = int(re.findall(r"\d+\.?\d*",selector_span[0].text)[0])
        # number of pages
        pages = math.ceil(nb_following/10)
        following_info = [['name','id','nb_fans']]
        # parse each page
        for page in range(1,pages+1):
            url = self._following_url % (self.user_id, page)
            html = requests.get(url, cookies=cookie).content
            self.num_requests +=1
            self.check_requests_time()
            selector = etree.HTML(html)
            # all td tags
            selector_tdtag = selector.xpath("//td[@valign='top']")
            for tag in selector_tdtag:
                tag_a = tag.xpath("a")
                tag_br = tag.xpath("br")
                # following name, id, nb_fans
                following_info1 = []
                for tag_a1 in tag_a:
                    if tag_a1.text:
                        tag_a1_href = tag_a1.attrib['href']
                        if '?uid=' in tag_a1_href:
                            uid = re.findall(r"uid=\d*&",tag_a1_href)[0]
                            uid = re.findall(r"\d+\d*",uid)[0]
                            following_info1.append(uid)
                        else:
                            tag_a1_text = tag_a1.text
                            following_info1.append(tag_a1_text)
                if tag_br:
                    tag_br1 = etree.tostring(tag_br[0]).decode('gbk')
                    nb_fans = tag_br1.split(';')[-2].split('&')[0] # number of fans
                    following_info1.append(nb_fans)
                if following_info1:
                    following_info.append(following_info1)
        if to_csv:
            csv_filename = "{}_following_info.csv".format(self.user_id)
            with open(csv_filename,'wb') as f:
                csv_writer = unicodecsv.writer(f, delimiter=',')
                csv_writer.writerows(following_info)
                print("file {} created...".format(csv_filename))
        return following_info

    def get_1stlayer_info(self, threshold):
        """
        get user_id's 1st layer friends' weibo info and store them in a folder
        :param threshold: number of fans threshold. weibos of users fans above or equal to threshold will not be considered
        :return: None
        """
        print("get following's information...")
        followings = self.get_following_info(to_csv=False)
        folder_name = '{}_following'.format(self.user_id)
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        ticker=0
        os.chdir(folder_name)
        print("start parsing following's weibo posts...")
        for following in followings:
            if len(following) == 3 and following[2].isnumeric():
                if int(following[2])<threshold:
                    user_id = int(following[1])
                    post_filter = 0
                    wb = Weibo(user_id, post_filter)
                    wb.start()
                    print("username: ", wb.userName.decode('GBK'))
                    wb.save_results()
            ticker+=1
            if ticker%10 == 0:
                print("{} of {} followings' weibo posts parsed...".format(ticker,len(followings)))
        os.chdir('..')
        return None

    def check_requests_time(self):
        """
        make sure the request frequency is under 900 requests/hour
        :return: 
        """
        time_elapsed = time.time()-start_time
        req_time_ratio = self.num_requests/time_elapsed
        if req_time_ratio > 900/3600: # 900 requests per hour
            time.sleep(3600/900*self.num_requests-time_elapsed)
        return None

    ''' Save restuls in TXT file'''
    def save_results(self):
        if self.original_weibo_filter == 1:
            resultHeader = '\n\noriginal weibo content: \n'
        else:
            resultHeader = '\n\nweibo content: \n'
        result = 'user_info or user_nickname: ' + self.userName.decode('GBK') \
                 + '\nuser_id: ' + str(self.user_id) \
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
        f = open(self.save_file_name, "w")
        f.write(result)
        f.close()
        file_path = os.getcwd() + "/weibo" + "/%d" % self.user_id + ".txt"
        print('saved file path is: ', file_path)


# ---------------------------- Main Function -------------------------- #
if __name__ == "__main__":
    user_id = 1917901324
    post_filter = 0
    wb = Weibo(user_id, post_filter)
    # print(wb._cookie)
    # wb.start()

    # print('following:', wb.get_following_info(to_csv=True))
    wb.get_1stlayer_info(threshold=3000)
    print(time.time()-start_time)

    print('username: ', wb.userName.decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_posts: ', str(wb.weiboNum))
    print('weibo_num_followings: ', str(wb.following))
    print('weibo_num_followers: ', str(wb.followers))
    print('first weibo: ', wb.weibos[0].decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_likes: ', str(wb.num_like[0]))
    print('weibo_num_forwardings:', str(wb.num_forwarding[0]))
    print('weibo_num_comments: ', str(wb.num_comment[0]))
    # wb.save_results()
