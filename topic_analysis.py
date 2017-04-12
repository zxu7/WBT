#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
analyze topic data
created by Xi 04/10/2017
"""


import os
import re
from collections import Counter, OrderedDict
from wordcloud import WordCloud
import matplotlib.pyplot as plt


class TopicAnalyze(object):
    tokens_regex = re.compile(r"\([\u4e00-\u9fff]+,\)")
    remove_char = ["'", "(", ")"]
    remove_topics = [u'评论', u'转发', u'视频', u'查看', u'删除', u'作者', u'抱歉', u'下载', u'客户端', "hashtag"]

    def run(self, file):
        self.generate_cloud(self.get_topics(file))

    def get_topics(self, file):
        topics_all = []
        saved_file_name = file.replace('_topics.txt', '_all_topics.txt')
        with open(file, "r") as f:
            for line in f:
                topics = line.split(":")[1].replace("'", "").replace("(", "").replace(")", "").replace("\n", "")
                if topics:
                    t = [w.strip() for w in topics.split(",") if w.strip() and not w.strip()[0].isdigit()]
                    topics_all.extend(t)

        t = Counter(topics_all)
        y = OrderedDict(t.most_common())
        [y.pop(t) for t in self.remove_topics if t in y]
        with open(saved_file_name, "w") as f:
            for item in y.items():
                f.write("%s: %s\n" % (item[0], item[1]))

        text = []
        for item in y.items():
            text.append(str(item[0] + ",").decode('utf-8'))
        return r"".join(text)

    def generate_cloud(self, text):
        # Generate a word cloud image
        wordcloud = WordCloud(font_path=u'simhei.ttf',
                              background_color="black", margin=5, width=2000, height=1200).generate(text)

        # Display the generated image:
        plt.figure()
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.show()


if __name__ == "__main__":
    topic_analyzer = TopicAnalyze()
    # path = os.path.abspath('./data/papijiang/2714280233_follower/topics')
    path = os.path.abspath('./data/papijiang')
    files = [f for f in os.listdir(path) if os.path.isfile("/".join([path, f])) and f.endswith("_topics.txt")]
    for file in files:
        fn = "/".join([path, file])
        topic_analyzer.run(fn)


