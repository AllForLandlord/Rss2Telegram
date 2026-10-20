from bs4 import BeautifulSoup
from telebot import types
from time import gmtime
import feedparser
import os
import re
import telebot
import telegraph
import time
import random
import requests
import sqlite3

def get_variable(variable):
    if not os.environ.get(f'{variable}'):
        var_file = open(f'{variable}.txt', 'r')
        return var_file.read()
    return os.environ.get(f'{variable}')

URL = get_variable('URL')
DESTINATION = get_variable('DESTINATION')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
EMOJIS = os.environ.get('EMOJIS', '🗞,📰,🗒,🗓,📋,🔗,📝,🗃')
PARAMETERS = os.environ.get('PARAMETERS', False)
HIDE_BUTTON = os.environ.get('HIDE_BUTTON', False)
DRYRUN = os.environ.get('DRYRUN')
TOPIC = os.environ.get('TOPIC', False)
TELEGRAPH_TOKEN = os.environ.get('TELEGRAPH_TOKEN', False)

bot = telebot.TeleBot(BOT_TOKEN)

MAX_SEND_RETRIES = 3
RETRY_DELAY_SECONDS = 5
MAX_RETRY_WAIT_SECONDS = 60

def add_to_history(link):
    conn = sqlite3.connect('rss2telegram.db')
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (link) VALUES (?)', (link,))
        conn.commit()
    finally:
        conn.close()

def check_history(link):
    conn = sqlite3.connect('rss2telegram.db')
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history WHERE link = ?', (link,))
        return cursor.fetchone()
    finally:
        conn.close()

def firewall(text):
    try:
        rules = open(f'RULES.txt', 'r')
    except FileNotFoundError:
        return True
    result = None
    for rule in rules.readlines():
        opt, arg = rule.split(':')
        arg = arg.strip()
        if arg == 'ALL' and opt == 'DROP':
            result = False
        elif arg == 'ALL' and opt == 'ACCEPT':
            result = True
        elif arg.lower() in text.lower() and opt == 'DROP':
            result = False
        elif arg.lower() in text.lower() and opt == 'ACCEPT':
            result = True
    return result

def send_with_retry(send_func, *args, **kwargs):
    waited_seconds = 0
    for attempt in range(MAX_SEND_RETRIES + 1):
        try:
            for arg in args:
                if hasattr(arg, 'seek'):
                    arg.seek(0)
            return send_func(*args, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            error_code = getattr(e, 'error_code', None)
            if error_code != 429 and (error_code is None or error_code < 500):
                raise
            if attempt == MAX_SEND_RETRIES:
                raise

            retry_after = None
            result_json = getattr(e, 'result_json', None)
            if error_code == 429 and isinstance(result_json, dict):
                parameters = result_json.get('parameters', {})
                if isinstance(parameters, dict):
                    retry_after = parameters.get('retry_after')
            try:
                delay = max(0, int(retry_after)) if retry_after is not None else RETRY_DELAY_SECONDS * (2 ** attempt)
            except (TypeError, ValueError):
                delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            if waited_seconds + delay > MAX_RETRY_WAIT_SECONDS:
                print(f'重试等待预算已达{MAX_RETRY_WAIT_SECONDS}秒，留待下次轮询（{e}）')
                raise
            print(f'Telegram暂时发送失败，{delay}秒后重试（{attempt + 1}/{MAX_SEND_RETRIES}）：{e}')
            time.sleep(delay)
            waited_seconds += delay
        except telebot.apihelper.ApiHTTPException as e:
            status_code = getattr(getattr(e, 'result', None), 'status_code', None)
            if status_code != 429 and (status_code is None or status_code < 500):
                raise
            if attempt == MAX_SEND_RETRIES:
                raise
            headers = getattr(getattr(e, 'result', None), 'headers', {})
            retry_after = headers.get('Retry-After') if status_code == 429 else None
            try:
                delay = max(0, int(retry_after)) if retry_after is not None else RETRY_DELAY_SECONDS * (2 ** attempt)
            except (TypeError, ValueError):
                delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            if waited_seconds + delay > MAX_RETRY_WAIT_SECONDS:
                print(f'重试等待预算已达{MAX_RETRY_WAIT_SECONDS}秒，留待下次轮询（{e}）')
                raise
            print(f'发送暂时失败，{delay}秒后重试（{attempt + 1}/{MAX_SEND_RETRIES}）：{e}')
            time.sleep(delay)
            waited_seconds += delay
        except requests.exceptions.ConnectTimeout as e:
            if attempt == MAX_SEND_RETRIES:
                raise
            delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            if waited_seconds + delay > MAX_RETRY_WAIT_SECONDS:
                print(f'重试等待预算已达{MAX_RETRY_WAIT_SECONDS}秒，留待下次轮询（{e}）')
                raise
            print(f'发送暂时失败，{delay}秒后重试（{attempt + 1}/{MAX_SEND_RETRIES}）：{e}')
            time.sleep(delay)
            waited_seconds += delay

def create_telegraph_post(topic):
    telegraph_auth = telegraph.Telegraph(
        access_token=f'{get_variable("TELEGRAPH_TOKEN")}'
    )
    response = telegraph_auth.create_page(
        f'{topic["title"]}',
        html_content=(
            f'{topic["summary"]}<br><br>'
            + f'<a href="{topic["link"]}">查看原文（{topic["site_name"]}）</a>'
        ),
        author_name=f'{topic["site_name"]}'
    )
    return response["url"]

def try_create_telegraph_post(topic):
    try:
        return create_telegraph_post(topic)
    except Exception as e:
        print(f'Telegraph页面创建失败，稍后重新尝试（{topic["title"]}）：{e}')
        return False

def send_message(topic, button):
    if DRYRUN == 'failure':
        return False

    MESSAGE_TEMPLATE = os.environ.get(f'MESSAGE_TEMPLATE', False)

    if MESSAGE_TEMPLATE:
        MESSAGE_TEMPLATE = set_text_vars(MESSAGE_TEMPLATE, topic)
    else:
        MESSAGE_TEMPLATE = f'<b>{topic["title"]}</b>'

    if not firewall(str(topic)):
        print(f'已按过滤规则跳过：{topic["title"]}')
        return True

    if TELEGRAPH_TOKEN:
        iv_link = try_create_telegraph_post(topic)
        if not iv_link:
            return False
        MESSAGE_TEMPLATE = f'<a href="{iv_link}">󠀠</a>{MESSAGE_TEMPLATE}'

    btn_link = button
    if button:
        btn_link = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(f'{button}', url=topic['link'])
        btn_link.row(btn)

    if topic['photo'] and not TELEGRAPH_TOKEN and not HIDE_BUTTON:
        try:
            response = requests.get(topic['photo'], headers={'User-agent': 'Mozilla/5.1'}, timeout=(3, 10))
            response.raise_for_status()
            with open('img', 'wb') as image_file:
                image_file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f'图片下载失败，改为文字发送（{topic["title"]}）：{e}')
            topic['photo'] = False

    if HIDE_BUTTON or TELEGRAPH_TOKEN:
        for dest in DESTINATION.split(','):
            send_with_retry(bot.send_message, dest, MESSAGE_TEMPLATE, parse_mode='HTML', reply_to_message_id=TOPIC)
    else:
        if topic['photo'] and not TELEGRAPH_TOKEN:
            for dest in DESTINATION.split(','):
                try:
                    with open('img', 'rb') as photo:
                        send_with_retry(bot.send_photo, dest, photo, caption=MESSAGE_TEMPLATE, parse_mode='HTML', reply_markup=btn_link, reply_to_message_id=TOPIC)
                except telebot.apihelper.ApiTelegramException as e:
                    error_code = getattr(e, 'error_code', None)
                    if error_code != 400:
                        raise
                    print(f'图片发送失败，改为文字发送（{topic["title"]}）：{e}')
                    send_with_retry(bot.send_message, dest, MESSAGE_TEMPLATE, parse_mode='HTML', reply_markup=btn_link, disable_web_page_preview=True, reply_to_message_id=TOPIC)
        else:
            for dest in DESTINATION.split(','):
                send_with_retry(bot.send_message, dest, MESSAGE_TEMPLATE, parse_mode='HTML', reply_markup=btn_link, disable_web_page_preview=True, reply_to_message_id=TOPIC)
        print(f'发送成功：{topic["title"]}')
    time.sleep(0.2)
    return True

def get_img(url):
    try:
        response = requests.get(url, headers={'User-agent': 'Mozilla/5.1'}, timeout=(3, 10))
        response.raise_for_status()
        html = BeautifulSoup(response.content, 'html.parser')
        photo = html.find('meta', {'property': 'og:image'})['content']
    except (TypeError, KeyError, requests.exceptions.RequestException) as e:
        if not isinstance(e, (TypeError, KeyError)):
            print(f'无法获取文章图片：{e}')
        photo = False
    return photo

def define_link(link, PARAMETERS):
    if PARAMETERS:
        if '?' in link:
            return f'{link}&{PARAMETERS}'
        return f'{link}?{PARAMETERS}'
    return f'{link}'



def set_text_vars(text, topic):
    cases = {
        'SITE_NAME': topic['site_name'],
        'TITLE': topic['title'],
        'SUMMARY': re.sub('<[^<]+?>', '', topic['summary']),
        'LINK': define_link(topic['link'], PARAMETERS),
        'EMOJI': random.choice(EMOJIS.split(","))
    }
    for word in re.split('{|}', text):
        try:
            text = text.replace(word, cases.get(word))
        except TypeError:
            continue
    return text.replace('\\n', '\n').replace('{', '').replace('}', '')


def check_topics(url):
    now = gmtime()
    feed = feedparser.parse(url)
    try:
        source = feed['feed']['title']
    except KeyError:
        print(f'\n错误：{url} 似乎不是有效的 RSS 订阅源。')
        return
    print(f'\n正在检查 {source}：{url}')
    for tpc in reversed(feed['items'][:10]):
        if check_history(tpc.links[0].href):
            continue
        
        topic = {}
        topic['site_name'] = feed['feed']['title']
        topic['title'] = tpc.title.strip()
        topic['summary'] = tpc.get('summary', '') or ''
        topic['link'] = tpc.links[0].href
        topic['photo'] = get_img(tpc.links[0].href)
        BUTTON_TEXT = os.environ.get('BUTTON_TEXT', False)
        if BUTTON_TEXT:
            BUTTON_TEXT = set_text_vars(BUTTON_TEXT, topic)
        try:
            if send_message(topic, BUTTON_TEXT):
                add_to_history(tpc.links[0].href)
        except (telebot.apihelper.ApiTelegramException, telebot.apihelper.ApiException, requests.exceptions.RequestException) as e:
            print(e)
            

if __name__ == "__main__":
    for url in URL.split():
        check_topics(url)

