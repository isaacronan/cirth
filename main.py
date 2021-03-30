import redis
import json
from sys import argv
from math import trunc
import time

host = ('host', argv[argv.index('--redis-host') + 1]) if '--redis-host' in argv else None
port = ('port', int(argv[argv.index('--redis-port') + 1])) if '--redis-port' in argv else None
db = ('db', int(argv[argv.index('--redis-db') + 1])) if '--redis-db' in argv else None

redisargs = dict([arg for arg in [host, port, db] if arg])
r = redis.Redis(**redisargs)

def cleanup():
    _maxbatches = r.get('batches:param:maxbatches')
    maxbatches = int(_maxbatches) if _maxbatches else 1
    if r.zcard('batches:current') > maxbatches:
        pipe = r.pipeline()

        wordsetspipe = r.pipeline()
        expiredbatches = list(r.zrange('batches:current', maxbatches, -1))
        for batch in [b.decode('utf-8') for b in expiredbatches]:
            wordsetspipe.smembers('words:{0}'.format(batch))
        wordsets = wordsetspipe.execute()

        for batch, wordset in zip([b.decode('utf-8') for b in expiredbatches], wordsets):
            words = list(wordset)
            for word in [b.decode('utf-8') for b in words]:
                wordid = 'words:{0}:word:{1}'.format(batch, word)
                pipe.delete(wordid)
                pipe.srem('words:all:{0}'.format(word), wordid)
        for batch in [b.decode('utf-8') for b in expiredbatches]:
            pipe.delete('words:{0}'.format(batch))
            pipe.delete('words:{0}:seeds'.format(batch))
            pipe.zrem('batches:current', batch)
        pipe.execute()

def addtomarkovchain(timestamp=0, phrase=[]):
    pipe = r.pipeline()
    for index, word in enumerate(phrase):
        key = word['key']
        value = word['value']
        nextkey = phrase[index + 1]['key'] if index < len(phrase) - 1 else None

        if index == 0:
            pipe.sadd('words:{0}:seeds'.format(timestamp), json.dumps(dict(value=value, key=key, nextkey=nextkey)))
        wordid = 'words:{0}:word:{1}'.format(timestamp, key)
        pipe.lpush(wordid, json.dumps(dict(value=value, nextkey=nextkey)))
        pipe.sadd('words:{0}'.format(timestamp), key)
        pipe.sadd('words:all:{0}'.format(key), wordid)
    pipe.zadd('batches:current', { str(timestamp): -1 * trunc(time.time() * 1000) })
    pipe.execute()
    cleanup()

while True:
    phrase = json.loads(r.brpop('batches:pending')[1])
    addtomarkovchain(**phrase)