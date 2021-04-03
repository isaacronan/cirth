
import json
from random import choice, randint
import time
from math import trunc

class PhraseGenerator:
    def __init__(self, client):
        self.client = client
        self.syncparams()
        self.cleanup()

    def syncparams(self):
        _maxphraselength = self.client.get('param:maxphraselength')
        self.maxphraselength = int(_maxphraselength) if _maxphraselength else 10
        _maxphrasecount = self.client.get('param:maxphrasecount')
        self.maxphrasecount = int(_maxphrasecount) if _maxphrasecount else 10
        _phraseattemptcount = self.client.get('param:phraseattemptcount')
        self.phraseattemptcount = int(_phraseattemptcount) if _phraseattemptcount else 10
        _phraseattemptinterval = self.client.get('param:phraseattemptinterval')
        self.phraseattemptinterval = float(_phraseattemptinterval) if _phraseattemptinterval else 1

    def cleanup(self):
        lengths = self.client.smembers('phrases:lengths')
        pipe = self.client.pipeline()
        for length in [int(b) for b in lengths]:
            if length > self.maxphraselength:
                pipe.delete('phrases:{0}'.format(length))
                pipe.srem('phrases:lengths', length)
            else:
                pipe.zremrangebyrank('phrases:{0}'.format(length), self.maxphrasecount, -1)
        pipe.execute()

    def attemptphrase(self):
        batches = list(self.client.zrange('batches:current', 0, -1))
        if len(batches) == 0:
            return None
        seedbatch = choice(batches).decode('utf-8')

        seedjson = self.client.srandmember('seeds:{0}'.format(seedbatch))
        if seedjson == None:
            return None
        seed = json.loads(seedjson)

        currentkey = seed['nextkey']
        randomwords = [seed['value']]
        for i in range(self.maxphraselength - 1):
            if currentkey == None:
                break
            
            wordid = self.client.srandmember('words:all:{0}'.format(currentkey))
            if wordid == None:
                return None
            nextwords = [json.loads(s) for s in self.client.lrange(wordid, 0, -1)]
            if len(nextwords) == 0:
                break
            nextword = choice(nextwords)
            randomwords.append(nextword['value'])
            currentkey = nextword['nextkey']
        if currentkey == None:
            return randomwords
        return None

    def addtostore(self, phrase):
        length = len(phrase)
        pipe = self.client.pipeline() 
        pipe.zadd('phrases:{0}'.format(length), { ' '.join(phrase): -1 * trunc(time.time() * 1000) })
        pipe.zremrangebyrank('phrases:{0}'.format(length), self.maxphrasecount, -1)
        pipe.sadd('phrases:lengths', length)
        pipe.execute()

    def startgenerating(self):
        count = 0
        while True:
            phrase = self.attemptphrase()
            if phrase != None:
                self.addtostore(phrase)
            count = (count + 1) % self.phraseattemptcount
            if count == 0:
                self.syncparams()
                self.cleanup()
                time.sleep(self.phraseattemptinterval)
