__filename__ = 'weibo_parser.py'
__version = 1.0
__author__ = 'Xi Wang'
__created__ = '2017-02-20'


import re
import logging
import traceback
from jieba import cut, tokenize
from nltk.stem.porter import PorterStemmer


class WeiboParser(object):
    """ Text parser class """

    # regular expression
    CASE_FLAGS = re.IGNORECASE
    # hash-tags
    HASHTAG_EXP = r'(?:\#+[\u4e00-\u9fff\#]+)'
    HASHTAG_REGEX = re.compile(HASHTAG_EXP, CASE_FLAGS)

    # mentioned users
    USERNAME_REGEX = re.compile(r"(?:@[\w\u4e00-\u9fff]+[\w\u4e00-\u9fff\_\'\&0-9]*)", CASE_FLAGS)

    # emoticon
    EMOTICON_EYES = r"[:=;x8<]"
    EMOTICON_NOSES = r"-~'^oO"
    EMOTICON_MOUTHS = r"3)(/\|oOdp"
    EMOTICON_EXP = "[%s][%s]?[%s]" % tuple(map(re.escape, [EMOTICON_EYES, EMOTICON_NOSES, EMOTICON_MOUTHS]))
    EMOTICON_REGEX = re.compile(EMOTICON_EXP, CASE_FLAGS)

    # url
    URL_EXP = r"(?P<url>https?[\S]+)"
    URL_REGEX = re.compile(URL_EXP)

    # nltk parameters
    STOP_WORDS = list("#$%&\()+-/:;<=>@[\\]^_`{|}~") + ['rt', 'via', 'http', '…']
    KEPT_STOP_WORDS = list(",.?!'")

    # spelling correction threshold
    SPELL_CONFIDENCE_THRESHOLD = 0.9
    DEBUG = False
    LOGGER = logging.getLogger('TextParser')

    def __init__(self, debug=False, rm_stopw=False):
        self.DEBUG = debug
        self.pstm = PorterStemmer()
        if rm_stopw:
            with open('stopwords.txt', 'r') as f:
                self.STOP_WORDS = f.read().split('\n')
        self.LOGGER.info("Finished Initialization")

    def run(self, data):
        """ parse the text data
            STEP:
            0) remove emoji/emoticon in the text
            1) remove url
            2) get username being @
            3) process hashtags
            4) remove repeatign chars in the word
            5) spelling correction, remove long words
            6) remove punctuation
            NOTE:
            input data format is a either a dictionary with text string and its label
            or a text string
        """
        processed_text = ''
        hashtags = ''
        if isinstance(data, dict):
            text = data['text']
            label = data['label']
        elif isinstance(data, str):
            text = data
            label = ''
        else:
            raise Exception('Input data format is not a string or a dictionary with text string')

        if text:
            if self.DEBUG:
                print('[original text] ', text)
            try:
                sentence = self._remove_emoticon(text)
                sentence = self._remove_emoji(sentence)
                sentence = self._remove_numbers(sentence)
                sentence = self._remove_url(sentence)
                sentence = self._remove_users(sentence)
                sentence, hashtags = self._extract_hashtag(sentence)
                tokens = cut(sentence)
                # self._remove_escapted_quotation(tokens)
                tokens = [w for w in tokens if w and w not in self.STOP_WORDS]
                processed_text += "".join(["{0} ".format(v) for v in tokens if not v.isspace() and v not in self.STOP_WORDS])
                # processed_text = self._postprocessing(processed_text)
                if self.DEBUG:
                    print('[processed text] ', processed_text)
                    print('[hashtags] ', hashtags)
            except:
                if self.DEBUG:
                    print('[Exception] {0}'.format(traceback.format_exc(3)))
                else:
                    raise Exception('[Exception]: {0}'.format(traceback.format_exc(3)))
        return processed_text, hashtags, label

    # TODO: verify it works in Chinese context
    def _remove_emoticon(self, text):
        if self.DEBUG:
            print('[EMOTICONS] ', self.EMOTICON_REGEX.findall(text))
        text = self.EMOTICON_REGEX.sub('', text)
        return text

    @staticmethod
    def _remove_emoji(word):
        # ----------------- method 1 --------------------#
        try:
            word = word.decode('utf-8')
            word = word.encode('ascii', errors='ignore')
        except:
            pass
        return word

    @staticmethod
    def _remove_numbers(text):
        # remove numbers only
        numberonly = re.compile(r'\b\d+\b')
        return numberonly.sub("", text)

    def _remove_users(self, text):
        """ Extract username that has been @ in the text """
        usernames = []
        users = self.USERNAME_REGEX.findall(text)
        if users:
            for user in users:
                usernames.append(str(user.split('@')[1]))
                text = text.replace(user, '')
        usernames = " ".join([t for t in usernames])
        if self.DEBUG:
            print('[@username] ', usernames)
        return text

    def _remove_url(self, text):
        """ Remove url from the text"""
        urls = self.URL_REGEX.findall(text)
        if urls:
            for url in urls:
                text = text.replace(url, "")
        if self.DEBUG:
            print('[urls] ', urls)
        return text

    def _extract_hashtag(self, text):
        """ Extract and process hashtags from text """
        w = []
        hashtags = ""
        tags = self.HASHTAG_REGEX.findall(text)
        if tags:
            for tag in tags:
                text = text.replace(tag, '')
                tokens = [t[0] for t in tokenize(str(tag.split('#')[1]))]
                w.extend(tokens)
            hashtags = " ".join(w)
        return text, hashtags

    @staticmethod
    def _remove_escapted_quotation(tokens):
        """ nltk.word_tokenize changes starting double quotes changes from " -> ``
            and ending double quotes from " -> ''
        """
        for ind, v in enumerate(tokens):
            if v in ["``", "''"]:
                tokens[ind] = ''

    # TODO:
    def _postprocessing(self, text):
        """ Post-processing """
        pass


# ------------------- main function -------------- #
if __name__ == "__main__":
    parser = WeiboParser(debug=True)
    text = "我的三个老婆 @王洋爱傻笑 @ice艾晓琪  @楼佳悦Artemis ……还有@演员马可 当时马可老师在水里[微笑]今晚彩色电视机里见[微笑]#电视剧麻辣变形计# "
    parser.run(text)

    print('-'*30)

    parser = WeiboParser(debug=True,rm_stopw=True)
    text = "我的不尽三个老婆 @王洋爱傻笑 @ice艾晓琪  @楼佳悦Artemis ……还有@演员马可 当时马可老师在水里[微笑]今晚彩色电视机里见[微笑]#电视剧麻辣变形计# "
    parser.run(text)