import subprocess
import json
import socket

CLI = "ookla-speedtest"

class Speedtest:
    def check_internet_connection(self):
        try:
            host = socket.gethostbyname("speedtest.net")
            socket.create_connection((host, 80), 2)
            return True
        except Exception as err: 
            print(err)
            return False

    def get_servers(self):
        process = subprocess.run([CLI, "--servers", "--format=json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode != 0:
            raise Exception("Failed to get servers")

        return json.loads(process.stdout)["servers"]

    def start(self, server_id, stop_event, callback):
        process = subprocess.Popen([CLI, "--server-id=" + str(server_id), "--format=json", "--progress", "--progress-update-interval=100"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while update := process.stdout.readline():
            if not update: break

            if stop_event.is_set():
                process.terminate()
                break
            
            update = json.loads(update)

            callback(update)
