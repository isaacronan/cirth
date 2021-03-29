import redis
import json
from sys import argv

host = ('host', argv[argv.index('--redis-host') + 1]) if '--redis-host' in argv else None
port = ('port', int(argv[argv.index('--redis-port') + 1])) if '--redis-port' in argv else None
db = ('db', int(argv[argv.index('--redis-db') + 1])) if '--redis-db' in argv else None

redisargs = dict([arg for arg in [host, port, db] if arg])
r = redis.Redis(**redisargs)

def addtomarkovchain(timestamp=0, phrase=[]):
    pipe = r.pipeline()
    isnewbatch = not r.sismember('batches:current', timestamp)
    if isnewbatch:
        wordsetspipe = r.pipeline()
        batches = list(r.smembers('batches:current'))
        for batch in [b.decode('utf-8') for b in batches]:
            wordsetspipe.smembers('words:{0}'.format(batch))
        wordsets = wordsetspipe.execute()

        for wordset in wordsets:
            words = list(wordset)
            for word in [b.decode('utf-8') for b in words]:
                pipe.delete(word)
        for batch in [b.decode('utf-8') for b in batches]:
            pipe.delete('words:{0}'.format(batch))
            pipe.delete('words:{0}:seeds'.format(batch))
            pipe.srem('batches:current', batch)
        pipe.sadd('batches:current', timestamp)

    for index, word in enumerate(phrase):
        key = word['key']
        value = word['value']
        nextkey = phrase[index + 1]['key'] if index < len(phrase) - 1 else None

        if index == 0:
            pipe.lpush('words:{0}:seeds'.format(timestamp), json.dumps(dict(value=value, key=key, nextkey=nextkey)))
        wordid = 'words:{0}:word:{1}'.format(timestamp, key)
        pipe.lpush(wordid, json.dumps(dict(value=value, nextkey=nextkey)))
        pipe.sadd('words:{0}'.format(timestamp), wordid)

    pipe.execute()

while True:
    phrase = json.loads(r.brpop('batches:pending')[1])
    addtomarkovchain(**phrase)