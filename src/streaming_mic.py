import json
import sys
import time

import pyaudio
import requests

from clean_response import clean_response

args = sys.argv
json_name = args[1]
oauth_url = 'https://api.ce-cotoha.com/v1/oauth/accesstokens'
model_id = 'ja-gen_tf-16'
hostname = 'https://api.ce-cotoha.com/api/'
url = hostname + 'asr/v1/speech_recognition/' + model_id
with open(json_name) as f:
    credential = json.load(f)
client_id = credential['client_id']
client_secret = credential['client_secret']
domain_id = credential['domain_id']


class StreamingRequester:
    def __init__(self):

        self.channels = 1
        self.format = pyaudio.paInt16
        self.rate = 44100
        self.Interval = 0.24
        self.nframes = int(self.rate * self.Interval)

        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.param_json = {"param": {
            "baseParam.samplingRate": self.rate,
            "recognizeParameter.domainId": domain_id,
            "recognizeParameter.enableContinuous": 'true'
            }}

    def get_token(self):
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        obj = {'grantType': 'client_credentials', 'clientId': self.client_id,
               'clientSecret': self.client_secret}
        data_json = json.dumps(obj).encode("utf-8")
        response = requests.post(url=oauth_url, data=data_json,
                                 headers=headers)
        self.access_token = response.json()['access_token']

    def check_response(self):  # エラー発生時の処理
        if self.response.status_code not in [200, 204]:
            print("STATUS_CODE:", self.response.status_code)
            print(self.response.text)
            exit()

    def print_result(self):  # レスポンスをパースし認識結果を標準出力
        # statusが200のときのみresponseにjsonが含まれる
        if self.response.status_code == 200:
            for res in self.response.json():
                if res['msg']['msgname'] == 'recognized':
                    # type=2ではsentenceの中身が空の配列の場合がある
                    if res['result']['sentence'] != []:
                        print(clean_response(res['result']['sentence'][0]['surface']))

    def start(self):  # 開始要求
        obj = self.param_json
        obj['msg'] = {'msgname': 'start'}
        data_json = json.dumps(obj).encode("utf-8")
        headers = {"Content-Type": "application/json;charset=UTF-8",
                   "Authorization": "Bearer " + self.access_token}
        self.requests = requests.Session()
        self.response = self.requests.post(url=self.url, data=data_json,
                                           headers=headers)
        self.check_response()
        # uniqueIdはデータ転送、停止要求に必要
        self.unique_id = self.response.json()[0]['msg']['uniqueId']

    def stop(self):  # 停止要求
        headers = {"Unique-ID": self.unique_id,
                   "Content-Type": "application/json;charset=UTF-8  ",
                   "Authorization": "Bearer " + self.access_token}
        obj = {"msg": {"msgname": "stop"}}
        data_json = json.dumps(obj).encode("utf-8")
        self.response = self.requests.post(url=self.url, data=data_json,
                                           headers=headers)
        self.check_response()
        self.print_result()

    def _post(self):
        self.headers = {"Content-Type": "application/octet-stream",
                        "Unique-ID": self.unique_id,
                        "Authorization": "Bearer " + self.access_token}

        self.response = self.requests.post(url=self.url, data=self.data,
                                           headers=self.headers)

        self.check_response()
        self.print_result()

    def _transfer(self):
        start = time.time()
        self._post()
        elapsed = time.time() - start
        if elapsed < self.Interval:
            time.sleep(self.Interval - elapsed)

    def listen(self):

        p = pyaudio.PyAudio()

        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.nframes
                        )

        print("Now Recording")

        try:
            while True:
                self.data = stream.read(self.nframes, exception_on_overflow=False)
                self._transfer()

        except KeyboardInterrupt:
            stream.close()
            p.terminate()
            sys.exit("Exit Voice Recognition")


if __name__ == '__main__':
    requester = StreamingRequester()
    requester.get_token()
    requester.start()
    requester.listen()
    requester.stop()