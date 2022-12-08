# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import os
import sys
from googletrans import Translator 
import time
import openai 
import threading 
import requests
from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def translate_text(text,de):
    translator = Translator()
    result = translator.translate(text, dest=de).text
    return result

def ask(q):
    import openai
    openai.api_key = "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"                   
    response = openai.Completion.create(
    model="text-curie-001",
    prompt=q,
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=["END"]
    )                     
    story = response['choices'][0]['text'] 
    return story

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if('、')in msg:
        msg = translate_text(msg,'en')
    else:
        zh_msg_list = msg.split(' ')
        msg = '、'.join(zh_msg_list)
        msg = translate_text(msg,'en')#輸入的句子轉英文

    en_msg_input = msg.split(',')
    msg = '、'.join(en_msg_input)
    ans=ask(msg)#輸出英文
    ans = translate_text(ans, 'zh-tw')#輸出轉成中文``
    ans_list = ans.split('->')
    ans = ans_list[1].replace(' ', '').replace('1。','1.').replace('2、','2.').replace('3、','3.').replace('4、','4.').replace('5、','5.')
    message = TextSendMessage(text=ans)
    line_bot_api.reply_message(event.reply_token, message)

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
