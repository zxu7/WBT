import re
from jieba import analyse, posseg, tokenize, cut_for_search

"""
Topic Extraction
Created by Xi Wang 4/4/2017
"""


class TopicExtractor (object):
    POS = ('ns', 'n', 'vn', 'v', 'nr')
    # regular expression
    CASE_FLAGS = re.IGNORECASE
    # hash-tags
    HASHTAG_EXP = r'(?:\#+[\u4e00-\u9fff\#]+)'
    HASHTAG_REGEX = re.compile(HASHTAG_EXP, CASE_FLAGS)

    def __init__(self, debug=True, topK=10):
        self.debug = debug
        self.top_k = topK
        analyse.set_stop_words("stopwords.txt")

    def get_topic(self, sentence):
        print("---- topics ----")
        tps = analyse.textrank(sentence, topK=self.top_k, withWeight=True)
        print(",".join([t for (t, w) in tps]))

    def get_tags(self, sentence):
        print("---- tags ----")
        tags = analyse.extract_tags(sentence, topK=self.top_k, withWeight=True, allowPOS=('ns', 'n'))
        print(",".join([t for (t, w) in tags]))

    def get_hashtag(self, sentence):
        hashtags = ""
        tags = self.HASHTAG_REGEX.findall(sentence)
        if tags:
            tokens = [tag.split('#')[1] for tag in tags]
            hashtags = ",".join(tokens)
        print("---- hashtags ----")
        print(hashtags)

    def get_numbers(self, sentence):
        numberonly = re.compile(r'\b\d+\b')
        num = numberonly.findall(sentence)
        print("---- numbers ----")
        print(",".join([n for n in num]))

    def get_nouns(self, sentence):
        words = posseg.dt.cut(sentence)
        str = ""
        for w in words:
            if w.flag in ['a', 'n', 'ns']:
                str += w.word
                if w.flag in ['n', 'ns']:
                    str += ","
        print("--- nouns ---")
        print(str)


# ------------------- main function -------------- #
if __name__ == "__main__":
    tp = TopicExtractor(debug=True, topK=10)
    text = "【迪士尼放话要千万片酬有条件 艾玛沃森两周做到】女星艾玛-沃森（Emma Watson）26岁已经红遍全球，在以《美女与野兽》中聪明、" \
           "勇敢的贝儿刷新观众的印象，先前传出迪士尼为了请到她演出，开出美金1500万元天价，不过开出一个条件，“只要达成就能拿到片酬”"
    text = "瘦腿真的不难，解决大腿粗肌肉腿的最佳塑型拉伸法~注意缓慢控制下到自己的极限，6个动作，" \
           "控制住四~八个呼吸，坚持拉伸好习惯，还你修长腿线 #健身达人"
    [print(t) for t in cut_for_search(text)]
    tp.get_topic(text)
    tp.get_tags(text)
    tp.get_hashtag(text)
    tp.get_numbers(text)
    tp.get_nouns(text)