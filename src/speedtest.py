import subprocess
import json

CLI = "ookla-speedtest"

class Speedtest:
    def __init__(self):
        pass

    def get_servers(self):
        process = subprocess.run([CLI, "--servers", "--format=json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(process.stdout)["servers"]

    def start(self, server_id, callback):
        process = subprocess.Popen([CLI, "--server-id=" + str(server_id), "--format=json", "--progress", "--progress-update-interval=100"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while update := process.stdout.readline():
            if not update: break
            
            update = json.loads(update)

            callback(update)
