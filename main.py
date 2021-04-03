import redis
from sys import argv
from utils.modelmanager import ModelManager
from utils.phrasegenerator import PhraseGenerator
from threading import Thread

host = ('host', argv[argv.index('--redis-host') + 1]) if '--redis-host' in argv else None
port = ('port', int(argv[argv.index('--redis-port') + 1])) if '--redis-port' in argv else None
db = ('db', int(argv[argv.index('--redis-db') + 1])) if '--redis-db' in argv else None
modelonly = True if '--model-only' in argv else False
generatoronly = True if '--generator-only' in argv else False

redisargs = dict([arg for arg in [host, port, db] if arg])
r = redis.Redis(**redisargs)

mmgr = Thread(target=ModelManager(r).startpolling)
pgen = Thread(target=PhraseGenerator(r).startgenerating)

if __name__ == '__main__':
    if not generatoronly:
        mmgr.start()
    if not modelonly:
        pgen.start()