#-*-coding=utf-8-*-

import csv
import time
from utils import START_DATETIME, END_DATETIME, _default_mongo, get_module_keywords, START_TS, END_TS

mongo = _default_mongo()

query_dict = {
    "timestamp": {
        "$gte": START_TS,
        "$lt": END_TS
    },
    "keywords_hit": True,
    "rubbish": False
}

def ts2date(ts):
    return time.strftime('%Y-%m-%d', time.localtime(ts))

def _encode_utf8(us):
    if isinstance(us, unicode):
        us = us.encode('utf-8')

    if not us:
        us = ''

    return us

def get_keywords(keywords_file):
    keywords = []
    keywords_file = '../source/' + keywords_file
    f = open(keywords_file)
    for line in f:
        if '!' in line:
            strip_no_querys = []
            querys = line.strip().lstrip('(').rstrip(')').split(' | ')
            for q in querys:
                strip_no_querys.append(q.split(' !')[0])
            strip_no_querys = '+'.join(strip_no_querys)
            line = strip_no_querys
        keywords_para = line.strip().lstrip('(').rstrip(')').split(' | ')
        keywords.extend(keywords_para)
    f.close()

    return keywords


def sheqi_author_stat():
    texts = []
    keywords = get_keywords('keywords_corp_baidu.txt')

    # 发布来源统计
    author_dict = dict()

    # 涉及企业的信息数统计
    corp_dict = dict()

    # 各渠道信息条数的周走势
    source_daily_dict = {
        "微博": {},
        "微信": {},
        "论坛": {},
        "新闻": {}
    }

    query_dict["$or"] = [{"source_category": "keywords_corp_weiboapi.txt"}, {"source_category": "keywords_hot_weiboapi.txt"}, {"source_category": "keywords_leader_weiboapi.txt"}]
    query_dict["source_website"] = "weibo_api_search_spider"
    count = mongo.master_timeline_weibo.find(query_dict).count()
    results = mongo.master_timeline_weibo.find(query_dict)
    author_dict["微博"] = count
    for r in results:
        texts.append(r['text'].encode('utf-8'))
        try:
            source_daily_dict["微博"][ts2date(r["timestamp"])] += 1
        except KeyError:
            source_daily_dict["微博"][ts2date(r["timestamp"])] = 1

    query_dict["$or"] = [{"category": "keywords_corp_forum.txt"}, {"category": "keywords_hot_forum.txt"}, {"category": "keywords_leader_forum.txt"}]
    del query_dict["source_website"]
    count = mongo.boatcol.find(query_dict).count()
    results = mongo.boatcol.find(query_dict)
    author_dict["论坛"] = count
    for r in results:
        title = _encode_utf8(r['title'])
        content168 = _encode_utf8(r['content168'])
        summary = _encode_utf8(r['summary'])

        text = title  + content168 + summary
        texts.append(text)
        try:
            source_daily_dict["论坛"][r["date"]] += 1
        except KeyError:
            source_daily_dict["论坛"][r["date"]] = 1

    query_dict["$or"] = [{"category": "keywords_corp_weixin.txt"}, {"category": "keywords_hot_weixin.txt"}, {"category": "keywords_leader_weixin.txt"}]
    count = mongo.boatcol.find(query_dict).count()
    results = mongo.boatcol.find(query_dict)
    author_dict["微信"] = count
    for r in results:
        title = _encode_utf8(r['title'])
        content168 = _encode_utf8(r['content168'])
        summary = _encode_utf8(r['summary'])

        text = title  + content168 + summary
        texts.append(text)
        try:
            source_daily_dict["微信"][r["date"]] += 1
        except KeyError:
            source_daily_dict["微信"][r["date"]] = 1

    query_dict["$or"] = [{"category": "keywords_corp_baidu.txt"}, {"category": "keywords_hot_baidu.txt"}, {"category": "keywords_leader_baidu.txt"}]
    query_dict["source_website"] = "baidu_ns_search"
    results = mongo.boatcol.find(query_dict)
    for r in results:
        try:
            author_dict[r['user_name']] += 1
        except KeyError:
            author_dict[r['user_name']] = 1
        title = _encode_utf8(r['title'])
        content168 = _encode_utf8(r['content168'])
        summary = _encode_utf8(r['summary'])

        text = title  + content168 + summary
        texts.append(text)
        try:
            source_daily_dict["新闻"][r["date"]] += 1
        except KeyError:
            source_daily_dict["新闻"][r["date"]] = 1

    fw = csv.writer(open('sheqi_author_stat_%s_%s.csv' % (START_DATETIME, END_DATETIME), 'wb'), delimiter='^')
    results = sorted(author_dict.iteritems(), key=lambda(k, v): v, reverse=True)
    for k, v in results:
        if k == "":
            continue
        fw.writerow((_encode_utf8(k), v))

    for text in texts:
        for keyword in keywords:
            if keyword in text:
                try:
                    corp_dict[keyword] += 1
                except KeyError:
                    corp_dict[keyword] = 1

    fw = csv.writer(open('sheqi_gongsi_stat_%s_%s.csv' % (START_DATETIME, END_DATETIME), 'wb'), delimiter='^')
    results = sorted(corp_dict.iteritems(), key=lambda(k, v): v, reverse=True)
    for k, v in results:
        if k == "":
            continue
        fw.writerow((_encode_utf8(k), v))

    fw = csv.writer(open('sheqi_source_stat_%s_%s.csv' % (START_DATETIME, END_DATETIME), 'wb'), delimiter='^')
    for source, daily_dict in source_daily_dict.iteritems():
        for date, count in daily_dict.iteritems():
            fw.writerow((_encode_utf8(source), date, count))


if __name__=="__main__":
    sheqi_author_stat()