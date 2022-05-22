import json
import os

path = os.environ.get("CONFIG_PATH") or "config.json"

# read config file
print("Reading config file")
with open(path) as json_file:
    config = json.load(json_file)
    messages = config["MESSAGES"]
    channels = config["CHANNELS"]
    intents = config["INTENTS"]
    intervals = config["INTERVALS"]
    resco = config["RESCO"]
    utils = config["UTILS"]
