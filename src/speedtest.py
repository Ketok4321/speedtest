import subprocess
import json

class Speedtest:
    def __init__(self):
        pass

    def start(self, callback):
        process = subprocess.Popen(["ookla-speedtest", "--format=json", "--progress", "--progress-update-interval=100"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while update := process.stdout.readline():
            if not update: break
            
            update = json.loads(update)

            callback(update)
