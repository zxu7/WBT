import re
import os
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

    def run_file(self, file):
        post_topics = []
        saved_file_name = file.replace('_new.txt', '_topics.txt')
        with open(file, 'r') as f:
            for i, line in enumerate(f):
                topics = self.get_topic(line)
                tags = self.get_tags(line)
                hashtags = self.get_hashtag(line)
                tp_tags = self.combine_topic_tags(topics, tags, hashtags, 0.7)
                post_topics.append("{0}: {1}\n".format(i+1, str(tp_tags).strip('[]')))

        with open(saved_file_name, "w") as f:
            f.writelines(post_topics)

    def get_topic(self, sentence):
        topics = analyse.textrank(sentence, topK=self.top_k, withWeight=True)
        if self.debug:
            print("---- topics ----")
            print(topics)
        return topics

    def get_tags(self, sentence):
        tags = analyse.extract_tags(sentence, topK=self.top_k, withWeight=True, allowPOS=self.POS)
        if self.debug:
            print("---- tags ----")
            print(tags)
        return tags

    """
        Combine the topics and tags into a set, remove duplicated words
        only consider tags whose tfidf values are above the threshold
        Note: default tfidf threshold is 1.0
    """
    def combine_topic_tags(self, topics, tags, hashtags, tfidf_threshould=0.7):
        tp = [k for (k, w) in topics]
        tags = [(k, w) for (k, w) in tags if w > tfidf_threshould and k not in tp]
        topics.extend(tags)
        tp_tags = sorted(topics, key=lambda x: topics.index(x))
        tp_tags.extend(hashtags)
        return tp_tags

    def get_hashtag(self, sentence):
        tags = self.HASHTAG_REGEX.findall(sentence)
        tgs = []
        if tags:
            tokens = [tag.split('#')[1] for tag in tags]
            tgs = [(t, "hashtag") for t in tokens]
        if self.debug:
            print("---- hashtags ----")
            print(tgs)
        return tgs

    def get_numbers(self, sentence):
        numberonly = re.compile(r'\b\d+\b')
        num = numberonly.findall(sentence)
        if self.debug:
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
        if self.debug:
            print("--- nouns ---")
            print(str)


# ------------------- main function -------------- #
if __name__ == "__main__":
    tp = TopicExtractor(debug=False, topK=10)
    path = os.path.abspath('./data/papijiang/2714280233_follower/weibo_new')
    # path = os.path.abspath('./data/papijiang')
    files = [f for f in os.listdir(path) if os.path.isfile("/".join([path, f])) and f.endswith("new.txt")]
    for f in files:
        fn = "/".join([path, f])
        tp.run_file(fn)

    # # test a single text string
    # # text = "瘦腿真的不难，解决大腿粗肌肉腿的最佳塑型拉伸法~注意缓慢控制下到自己的极限，6个动作，" \
    # #        "控制住四~八个呼吸，坚持拉伸好习惯，还你修长腿线 #健身达人"
    # text = "睡相一定要优美，提防身边手欠人。。。"
    # # # [print(t) for t in cut_for_search(text)]
    # tp.get_topic(text)
    # tp.get_tags(text)
    # tp.get_hashtag(text)
    # tp.get_numbers(text)
    # tp.get_nouns(text)