# cirth

Python utility for constructing a Markov chain from real-time text data. Continuously generates random phrases. Runs on Redis.

See a demonstration [here](https://ishero.dev/fakenews).

## Running

A Redis server must be running.

```bash
pip3 install -r requirements.txt
python3 main.py # optional arguments
```

### Docker

```bash
docker image build --tag cirth-image ~/path/to/cirth
docker run cirth-image # optional arguments
```

### Optional Arguments

* **--redis-host *value*** - hostname of the target Redis server
* **--redis-port *value*** - port number of the target Redis server
* **--redis-db *value*** - number of the target Redis database
* **--model-only** - runs the script only to listen for training data and update the model
* **--generator-only** - runs the script only to generate random phrases from the model and persist them to the store

## Model Training

Push training data into the `batches:training` Redis list. The model will be updated immediately. A training datum is a **stringified JSON object** of the following structure (corresponding to some phrase):

```javascript
{
    batchid: string,
    phrase: [{
        key: string,
        value: string
    }]
}
```

* **batchid** - an identifier linking the phrase to a particular batch of phrases (e.g. phrases from a common source); used to determine which data should be kept/discarded as the model grows
* **phrase** - an array of objects corresponding to the words in the phrase
    * **key** - a normalized identifier for the word, which should be common across the various occurences of the word (e.g. lowercase and stripped of leading/trailing punctuation)
    * **value** - the exact value of the particular occurence of the word, which will appear in randomly generated phrases (e.g. mixed case with punctuation)

## Random Phrase Generation

Generating a finite-length phrase is a non-deterministic task. With sufficient training data and time, the following fields will become available in the store:

* `phrases:lengths` - a Redis set containing the lengths (in words) of phrases that have been generated thus far
* `phrases:N` - a Redis sorted set containing the most recently generated phrases of length **N** (in words)

## Store Parameters

These parameters can be updated in the store at any time during execution.

* `param:maxtrainingbatches` *(default 1)* - maximum number of most recent training batches whose data should remain in the model
* `param:maxphraselength` *(default 10)* - maximum number of words allowed in a phrase
* `param:maxphrasecount` *(default 10)* - maximum number of most recently generated phrases to maintain in the store
* `param:phraseattemptcount` *(default 10)* - number of sequential phrase generation attempts that will be made at one time
* `param:phraseattemptinterval` *(default 1)* - floating point number of seconds to wait in between sequences of phrase generation attempts