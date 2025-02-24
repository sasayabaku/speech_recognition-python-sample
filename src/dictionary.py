# coding:utf-8
import requests
import json
import wave
import sys
import time
import pandas as pd
import os

args = sys.argv
json_name = args[1]

try:
    tsv_name = args[2]
    delete_flag = False
except IndexError:
    delete_flag = True

oauth_url = 'https://api.ce-cotoha.com/v1/oauth/accesstokens'
model_id = "ja-gen_tf-16"
hostname = 'https://api.ce-cotoha.com/api/'
url = hostname + 'asr/v1/speech_words/' + model_id

with open(json_name) as f:
    credential = json.load(f)
client_id = credential['client_id']
client_secret = credential['client_secret']
domain_id = credential['domain_id']


class Requester:
    def __init__(self):
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret

    def get_token(self):
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        obj = {'grantType': 'client_credentials', 'clientId': self.client_id, 'clientSecret': self.client_secret}
        data_json = json.dumps(obj).encode("utf-8")
        response = requests.post(url=oauth_url, data=data_json, headers=headers)
        self.access_token = response.json()['access_token']

    def set_dictionary(self):
        """
        辞書登録
        """
        self.url = url + "/upload?" + "domainid=" + domain_id
        print(self.url)
        headers = {"Authorization":"Bearer " + self.access_token}
        file = {"cascadeword": open(tsv_name, 'rb')}
        res = requests.post(self.url, files=file, headers=headers)
        print(res.text)

    def reset_dictionary(self):
        """
        辞書クリア
        """
        self.url = url + "/clear?" + "domainid=" + domain_id
        headers = {"Authorization":"Bearer " + self.access_token}
        res = requests.get(self.url, headers=headers)
        print(res.text)


def main():
    requester = Requester()
    requester.get_token()

    if delete_flag:
        requester.reset_dictionary()
    else:
        requester.set_dictionary()

if __name__ == "__main__":
    main()
