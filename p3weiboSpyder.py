import re
import string
import sys
import os
import urllib
from bs4 import BeautifulSoup
import requests
from lxml import etree
import traceback







class Weibo:
    cookie = {"_T_WM": 'c08cdb625aad5b5d39c7ff083b60b110',
              "SCF": 'AhQquoQdLEeDlLQTfn-lvh4L-X2uzJhyJOnOG_nDZNbt27Pc5IcmEjad561dU1kPI-doq9gvWULyWq5Nyv_F5TQ.',
              "WEIBOCN_WM": '3349', "H5_wentry": 'H5', "backURL": 'http%3A%2F%2Fm.weibo.cn%2F',
              "SUBP": '0033WrSXqPxfM725Ws9jqgMF55529P9D9WF1QPMOr_F7zp0rdq_i6Z715JpX5o2p5NHD95Qf1hBR1hz0ShqcWs4DqcjeqJ8.9cHEPNxDUs8V',
              "H5_INDEX": '3', "H5_INDEX_TITLE": 'Harry_ZH_Xu',
              "M_WEIBOCN_PARAMS": 'luicode%3D10000011%26lfid%3D102803_ctg1_8999_-_ctg1_8999_home%26fid%3D102803_ctg1_8999_-_ctg1_8999_home%26uicode%3D10000011',
              "SUB": '_2A251gg9YDeTxGedH4lsY9ivKyT-IHXVWjJEQrDV6PUJbkdBeLXCjkW1oxcLA9m-GqmbPcuTCF0X91EoLEg..',
              "SUHB": '0FQ63KZHNkLeCn', "SSOLoginState": '1485209352'}

    # weibo
    def __init__(self, user_id, filter=0):
        self.user_id = user_id  # id������Ҫ������������֣����ǳ�Ϊ��Dear-�����Ȱ͡���idΪ1669879400
        self.filter = filter  # ȡֵ��ΧΪ0��1������Ĭ��ֵΪ0������Ҫ��ȡ�û���ȫ��΢����1����ֻ��ȡ�û���ԭ��΢��
        self.userName = ''  # �û������硰Dear-�����Ȱ͡�
        self.weiboNum = 0  # �û�ȫ��΢����
        self.weiboNum2 = 0  # ��ȡ����΢����
        self.following = 0  # �û���ע��
        self.followers = 0  # �û���˿��
        self.weibos = []  # ΢������
        self.num_zan = []  # ΢����Ӧ�ĵ�����
        self.num_forwarding = []  # ΢����Ӧ��ת����
        self.num_comment = []  # ΢����Ӧ��������

    def getusername(self):
        try:
            url = 'http://weibo.cn/%d/info' % (self.user_id)
            html = requests.get(url, cookies=Weibo.cookie).content
            selector = etree.HTML(html)
            userName = selector.xpath("//title/text()")[0]
            self.userName = userName[:-3].encode('gbk')
        # print '�û��ǳƣ�' + self.userName
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getuserinfo(self):
        try:
            url = 'http://weibo.cn/u/%d?filter=%d&page=1' % (self.user_id, self.filter)
            html = requests.get(url, cookies=Weibo.cookie).content
            selector = etree.HTML(html)
            pattern = r"\d+\.?\d*"

            # ΢����
            str_wb = selector.xpath("//div[@class='tip2']/span[@class='tc']/text()")[0]
            guid = re.findall(pattern, str_wb, re.S | re.M)
            for value in guid:
                num_wb = int(value)
                break
            self.weiboNum = num_wb
            # print '΢����: ' + str(self.weiboNum)

            # ��ע��
            str_gz = selector.xpath("//div[@class='tip2']/a/text()")[0]
            guid = re.findall(pattern, str_gz, re.M)
            self.following = int(guid[0])
            # print '��ע��: ' + str(self.following)

            # ��˿��
            str_fs = selector.xpath("//div[@class='tip2']/a/text()")[1]
            guid = re.findall(pattern, str_fs, re.M)
            self.followers = int(guid[0])
        # print '��˿��: ' + str(self.followers)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def getweiboinfo(self):
        try:
            url = 'http://weibo.cn/u/%d?filter=%d&page=1' % (self.user_id, self.filter)
            html = requests.get(url, cookies=Weibo.cookie).content
            selector = etree.HTML(html)
            if selector.xpath('//input[@name="mp"]') == []:
                pageNum = 1
            else:
                pageNum = (int)(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
            pattern = r"\d+\.?\d*"
            for page in range(1, pageNum + 1):
                url2 = 'http://weibo.cn/u/%d?filter=%d&page=%d' % (self.user_id, self.filter, page)
                html2 = requests.get(url2, cookies=Weibo.cookie).content
                selector2 = etree.HTML(html2)
                info = selector2.xpath("//div[@class='c']")
                # print len(info)
                if len(info) > 3:
                    for i in range(0, len(info) - 2):
                        self.weiboNum2 = self.weiboNum2 + 1
                        # ΢������
                        str_t = info[i].xpath("div/span[@class='ctt']")
                        weibos = str_t[0].xpath('string(.)').encode('gbk', 'ignore')
                        self.weibos.append(weibos)
                        # print '΢�����ݣ�'+ weibos
                        # ������
                        str_zan = info[i].xpath("div/a/text()")[-4]
                        guid = re.findall(pattern, str_zan, re.M)
                        num_zan = int(guid[0])
                        self.num_zan.append(num_zan)
                        # print '������: ' + str(num_zan)
                        # ת����
                        forwarding = info[i].xpath("div/a/text()")[-3]
                        guid = re.findall(pattern, forwarding, re.M)
                        num_forwarding = int(guid[0])
                        self.num_forwarding.append(num_forwarding)
                        # print 'ת����: ' + str(num_forwarding)
                        # ������
                        comment = info[i].xpath("div/a/text()")[-2]
                        guid = re.findall(pattern, comment, re.M)
                        num_comment = int(guid[0])
                        self.num_comment.append(num_comment)
                        # print '������: ' + str(num_comment)
            if self.filter == 0:
                print
                '��' + str(self.weiboNum2) + '��΢��'
            else:
                print
                '��' + str(self.weiboNum) + '��΢��������' + str(self.weiboNum2) + '��Ϊԭ��΢��'
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def start(self):
        try:
            Weibo.getusername(self)
            Weibo.getuserinfo(self)
            Weibo.getweiboinfo(self)
            print('===========================================================================')
        except Exception as e:
            print("Error: ", e)


    def writetxt(self):
        try:
            if self.filter == 1:
                resultHeader = '\n\nԭ��΢�����ݣ�\n'
            else:
                resultHeader = '\n\n΢�����ݣ�\n'
            result = '�û���Ϣ\n�û��ǳƣ�' + self.userName + '\n�û�id��' + str(self.user_id) + '\n΢������' + str(
                self.weiboNum) + '\n��ע����' + str(self.following) + '\n��˿����' + str(self.followers) + resultHeader
            for i in range(1, self.weiboNum2 + 1):
                text = str(i) + ':' + self.weibos[i - 1] + '\n' + '��������' + str(
                    self.num_zan[i - 1]) + '	 ת������' + str(self.num_forwarding[i - 1]) + '	 ��������' + str(
                    self.num_comment[i - 1]) + '\n\n'
                result = result + text
            if os.path.isdir('weibo') == False:
                os.mkdir('weibo')
            f = open("weibo/%s.txt" % self.user_id, "wb")
            f.write(result)
            f.close()
            file_path = os.getcwd() + "\weibo" + "\%d" % self.user_id + ".txt"
            print
            '΢��д���ļ���ϣ�����·��%s' % (file_path)
        except Exception as e:
            print("Error: ", e)


# ʹ��ʵ��,����һ���û�id��������Ϣ����洢��wbʵ����
user_id = 1669879400  # ���Ըĳ�����Ϸ����û�id�������΢��id���⣩
filter = 1  # ֵΪ0��ʾ��ȡȫ����΢����Ϣ��ԭ��΢��+ת��΢������ֵΪ1��ʾֻ��ȡԭ��΢��
wb = Weibo(user_id, filter)  # ����weibo�࣬����΢��ʵ��wb
wb.start()  # ��ȡ΢����Ϣ
print('username: ', wb.userName.decode('gbk')) # need to decode to 'gbk' to display chinese
print('weibo_number: ', str(wb.weiboNum))
print('weibo_following: ', str(wb.following))
print('weibo_follower: ', str(wb.followers))
print('weibos[0]: ', wb.weibos[0].decode('gbk'))  # need to decode to 'gbk' to display chinese
print('weibo_numzan: ', str(wb.num_zan[0]))
print('weibo_num_forwarding:', str(wb.num_forwarding[0]))
print('weibo_num_comment: ', str(wb.num_comment[0]))

# wb.writeTxt()