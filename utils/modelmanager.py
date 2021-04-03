import json
from math import trunc
import time

class ModelManager:
    def __init__(self, client):
        self.client = client
        self.cleanup()

    def cleanup(self):
        _maxtrainingbatches = self.client.get('param:maxtrainingbatches')
        maxtrainingbatches = int(_maxtrainingbatches) if _maxtrainingbatches != None else 1
        expiredbatches = list(self.client.zrange('batches:current', maxtrainingbatches, -1))

        wordsetspipe = self.client.pipeline()
        for batch in [b.decode('utf-8') for b in expiredbatches]:
            wordsetspipe.smembers('words:{0}'.format(batch))
        wordsets = wordsetspipe.execute()

        cleanuppipe = self.client.pipeline()
        for batch, wordset in zip([b.decode('utf-8') for b in expiredbatches], wordsets):
            words = list(wordset)
            for word in [b.decode('utf-8') for b in words]:
                wordid = 'words:{0}:{1}'.format(batch, word)
                cleanuppipe.delete(wordid)
                cleanuppipe.srem('words:all:{0}'.format(word), wordid)
        for batch in [b.decode('utf-8') for b in expiredbatches]:
            cleanuppipe.delete('words:{0}'.format(batch))
            cleanuppipe.delete('seeds:{0}'.format(batch))
            cleanuppipe.zrem('batches:current', batch)
        cleanuppipe.execute()

    def addtomodel(self, batch=0, phrase=[]):
        pipe = self.client.pipeline()
        for index, word in enumerate(phrase):
            key = word['key']
            value = word['value']
            nextkey = phrase[index + 1]['key'] if index < len(phrase) - 1 else None

            if index == 0:
                pipe.sadd('seeds:{0}'.format(batch), json.dumps(dict(value=value, key=key, nextkey=nextkey)))
            wordid = 'words:{0}:{1}'.format(batch, key)
            pipe.lpush(wordid, json.dumps(dict(value=value, nextkey=nextkey)))
            pipe.sadd('words:{0}'.format(batch), key)
            pipe.sadd('words:all:{0}'.format(key), wordid)
        pipe.zadd('batches:current', { str(batch): -1 * trunc(time.time() * 1000) })
        pipe.execute()

    def startpolling(self):
        while True:
            phrasejson = self.client.brpop('batches:training')[1]
            try:
                phrase = json.loads(phrasejson)
                self.addtomodel(**phrase)
                self.cleanup()
            except ValueError:
                pass