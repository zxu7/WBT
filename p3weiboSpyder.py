import re
import os
import requests
from lxml import etree
import traceback


'''
    Manual Scrapping Weibo data
    Created by 01/22/2017
'''


class Weibo:
    _cookie = {"_T_WM": 'c08cdb625aad5b5d39c7ff083b60b110',
              "SCF": 'AhQquoQdLEeDlLQTfn-lvh4L-X2uzJhyJOnOG_nDZNbt27Pc5IcmEjad561dU1kPI-doq9gvWULyWq5Nyv_F5TQ.',
              "WEIBOCN_WM": '3349',
              "H5_wentry": 'H5',
              "backURL": 'http%3A%2F%2Fm.weibo.cn%2F',
              "SUBP": '0033WrSXqPxfM725Ws9jqgMF55529P9D9WF1QPMOr_F7zp0rdq_i6Z715JpX5o2p5NHD95Qf1hBR1hz0ShqcWs4DqcjeqJ8.'
                      '9cHEPNxDUs8V',
              "H5_INDEX": '3',
               "H5_INDEX_TITLE": 'Harry_ZH_Xu',
              "M_WEIBOCN_PARAMS": 'luicode%3D10000011%26lfid%3D102803_ctg1_8999_-_ctg1_8999_home%26fid%3D102803_ctg1'
                                  '_8999_-_ctg1_8999_home%26uicode%3D10000011',
              "SUB": '_2A251gg9YDeTxGedH4lsY9ivKyT-IHXVWjJEQrDV6PUJbkdBeLXCjkW1oxcLA9m-GqmbPcuTCF0X91EoLEg..',
              "SUHB": '0FQ63KZHNkLeCn',
              "SSOLoginState": '1485209352'}
    _info_url = 'http://weibo.cn/%d/info'
    _filter_url = 'http://weibo.cn/u/%d?filter=%d&page=1'
    _page_url = 'http://weibo.cn/u/%d?filter=%d&page=%d'

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
            selector = etree.HTML(html)
            if not selector.xpath('//input[@name="mp"]'):
                pageNum = 1
            else:
                pageNum = int(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
            pattern = r"\d+\.?\d*"
            for page in range(1, pageNum + 1):
                url2 = self._page_url % (self.user_id, self.original_weibo_filter, page)
                html2 = requests.get(url2, cookies=Weibo._cookie).content
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
    user_id = 1669879400
    post_filter = 0
    wb = Weibo(user_id, post_filter)
    wb.start()
    print('username: ', wb.userName.decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_posts: ', str(wb.weiboNum))
    print('weibo_num_followings: ', str(wb.following))
    print('weibo_num_followers: ', str(wb.followers))
    print('first weibo: ', wb.weibos[0].decode('gbk'))  # need to decode to 'gbk' to display chinese
    print('weibo_num_likes: ', str(wb.num_like[0]))
    print('weibo_num_forwardings:', str(wb.num_forwarding[0]))
    print('weibo_num_comments: ', str(wb.num_comment[0]))
    wb.save_results()
