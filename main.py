import json
import os.path
import re
import time
import telebot
import schedule
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# Input parameters
API_TOKEN = "TELEGRAM_BOT_TOKEN"
bot = telebot.TeleBot(API_TOKEN)
regions = {45: "г. Москва", 46: "Московская область"}
# pub_dt = "26.11.2022"
pub_dt = datetime.strftime(datetime.now(), '%d.%m.%Y')
translate = {
    'publication_datetime': 'Дата сообщения',
    'publication_url': 'Ссылка на сообщение',
    'debtor': 'Должник',
    'debtor_card': 'Карточка должника',
    'published_by': 'Организатор торгов',
    'published_url': 'Ссылка на организатора'
}


def scrapy_data():
    files = {}
    for k, v in regions.items():
        cookies = {
            'qrator_ssid': '1669410074.793.k84gZPs0FaTGnxKU-75mhu7cvi1tic0r4vda0uu1cn366pi7d',
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            # 'Cookie': 'qrator_ssid=1669410074.793.k84gZPs0FaTGnxKU-75mhu7cvi1tic0r4vda0uu1cn366pi7d',
            'Origin': 'https://old.bankrot.fedresurs.ru',
            'Referer': 'https://old.bankrot.fedresurs.ru/Messages.aspx',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'X-MicrosoftAjax': 'Delta=true',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        data = {
            'ctl00$PrivateOffice1$ctl00': 'ctl00$PrivateOffice1$ctl00|ctl00$cphBody$ibMessagesSearch',
            '__PREVIOUSPAGE': 'u0YJjgLPY8IcrrwtjyQQyAByUrDnIF2hgMnHcGz5GQsVuQzVrMYdXP131VSJH6EoLidaUV2RDa6yf_YOiLwgUzYJ6Qk1',
            'ctl00$PrivateOffice1$tbLogin': '',
            'ctl00$PrivateOffice1$tbPassword': '',
            'ctl00$PrivateOffice1$cbRememberMe': 'on',
            'ctl00$PrivateOffice1$tbEmailForPassword': '',
            'ctl00_PrivateOffice1_RadToolTip1_ClientState': '',
            'ctl00$DebtorSearch1$inputDebtor': 'поиск',
            'ctl00$cphBody$tbMessageNumber': '',
            'ctl00$cphBody$mdsMessageType$tbSelectedText': 'Иное сообщение',
            'ctl00$cphBody$mdsMessageType$hfSelectedValue': 'Other',
            'ctl00$cphBody$mdsMessageType$hfSelectedType': '',
            'ctl00$cphBody$ddlCourtDecisionType': '',
            'ctl00$cphBody$mdsPublisher$tbSelectedText': '',
            'ctl00$cphBody$mdsPublisher$hfSelectedValue': '',
            'ctl00$cphBody$mdsPublisher$hfSelectedType': '',
            'ctl00$cphBody$ucRegion$ddlBoundList': str(k),
            'ctl00$cphBody$mdsDebtor$tbSelectedText': '',
            'ctl00$cphBody$mdsDebtor$hfSelectedValue': '',
            'ctl00$cphBody$mdsDebtor$hfSelectedType': '',
            'ctl00$cphBody$cldrBeginDate$tbSelectedDate': pub_dt,
            'ctl00$cphBody$cldrBeginDate$tbSelectedDateValue': pub_dt,
            'ctl00$cphBody$cldrEndDate$tbSelectedDate': pub_dt,
            'ctl00$cphBody$cldrEndDate$tbSelectedDateValue': pub_dt,
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '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aW5kb3dfY3RsMDBfY3BoQm9keV9tZHNNZXNzYWdlVHlwZSgpZAIBDw9kFgIfBAUuT3Blbk1vZGFsV2luZG93X2N0bDAwX2NwaEJvZHlfbWRzTWVzc2FnZVR5cGUoKWQCAg8PZBYCHwQFJENsZWFyX2N0bDAwX2NwaEJvZHlfbWRzTWVzc2FnZVR5cGUoKWQCBQ9kFgICAQ9kFgICAQ8QDxYCHgtfIURhdGFCb3VuZGdkEBUbBtCS0YHQtSjQviDQstCy0LXQtNC10L3QuNC4INC90LDQsdC70Y7QtNC10L3QuNGPOdC+INCy0LLQtdC00LXQvdC40Lgg0LLQvdC10YjQvdC10LPQviDRg9C/0YDQsNCy0LvQtdC90LjRj0PQviDQstCy0LXQtNC10L3QuNC4INGE0LjQvdCw0L3RgdC+0LLQvtCz0L4g0L7Qt9C00L7RgNC+0LLQu9C10L3QuNGPM9C+INC/0YDQvtC00LvQtdC90LjQuCDRgdGA0L7QutCwINC/0YDQvtGG0LXQtNGD0YDRizPQvtCxINC40LfQvNC10L3QtdC90LjQuCDRgdGD0LTQtdCx0L3QvtCz0L4g0LDQutGC0LAt0L7QsSDQvtGC0LzQtdC90LUg0YHRg9C00LXQsdC90L7Qs9C+INCw0LrRgtCwyAHQviDQv9GA0LjQt9C90LDQvdC40Lgg0L7QsdC+0YHQvdC+0LLQsNC90L3Ri9C8INC30LDRj9Cy0LvQtdC90LjRjyDQviDQv9GA0LjQt9C90LDQvdC40Lgg0LPRgNCw0LbQtNCw0L3QuNC90LAg0LHQsNC90LrRgNC+0YLQvtC8INC4INCy0LLQtdC00LXQvdC40Lgg0YDQtdGB0YLRgNGD0LrRgtGD0YDQuNC30LDRhtC40Lgg0LXQs9C+INC00L7Qu9Cz0L7Qsn3QviDQv9GA0LjQt9C90LDQvdC40Lgg0LTQvtC70LbQvdC40LrQsCDQsdCw0L3QutGA0L7RgtC+0Lwg0Lgg0L7RgtC60YDRi9GC0LjQuCDQutC+0L3QutGD0YDRgdC90L7Qs9C+INC/0YDQvtC40LfQstC+0LTRgdGC0LLQsEvQvtCxINC+0YLQutCw0LfQtSDQsiDQv9GA0LjQt9C90LDQvdC40Lgg0LTQvtC70LbQvdC40LrQsCDQsdCw0L3QutGA0L7RgtC+0LyaAdC+INC/0YDQuNC80LXQvdC10L3QuNC4INC/0YDQuCDQsdCw0L3QutGA0L7RgtGB0YLQstC1INC00L7Qu9C20L3QuNC60LAg0L/RgNCw0LLQuNC7INC/0LDRgNCw0LPRgNCw0YTQsCDCq9CR0LDQvdC60YDQvtGC0YHRgtCy0L4g0LfQsNGB0YLRgNC+0LnRidC40LrQvtCywrtr0L4g0L/QtdGA0LXQtNCw0YfQtSDQtNC10LvQsCDQvdCwINGA0LDRgdGB0LzQvtGC0YDQtdC90LjQtSDQtNGA0YPQs9C+0LPQviDQsNGA0LHQuNGC0YDQsNC20L3QvtCz0L4g0YHRg9C00LBp0L7QsSDRg9GC0LLQtdGA0LbQtNC10L3QuNC4INC/0LvQsNC90LAg0YDQtdGB0YLRgNGD0LrRgtGD0YDQuNC30LDRhtC40Lgg0LTQvtC70LPQvtCyINCz0YDQsNC20LTQsNC90LjQvdCwWtC+INC30LDQstC10YDRiNC10L3QuNC4INGA0LXRgdGC0YDRg9C60YLRg9GA0LjQt9Cw0YbQuNC4INC00L7Qu9Cz0L7QsiDQs9GA0LDQttC00LDQvdC40L3QsI4B0L4g0L/RgNC40LfQvdCw0L3QuNC4INCz0YDQsNC20LTQsNC90LjQvdCwINCx0LDQvdC60YDQvtGC0L7QvCDQuCDQstCy0LXQtNC10L3QuNC4INGA0LXQsNC70LjQt9Cw0YbQuNC4INC40LzRg9GJ0LXRgdGC0LLQsCDQs9GA0LDQttC00LDQvdC40L3QsKYB0L4g0L3QtdC/0YDQuNC80LXQvdC10L3QuNC4INCyINC+0YLQvdC+0YjQtdC90LjQuCDQs9GA0LDQttC00LDQvdC40L3QsCDQv9GA0LDQstC40LvQsCDQvtCxINC+0YHQstC+0LHQvtC20LTQtdC90LjQuCDQvtGCINC40YHQv9C+0LvQvdC10L3QuNGPINC+0LHRj9C30LDRgtC10LvRjNGB0YLQslTQviDQt9Cw0LLQtdGA0YjQtdC90LjQuCDRgNC10LDQu9C40LfQsNGG0LjQuCDQuNC80YPRidC10YHRgtCy0LAg0LPRgNCw0LbQtNCw0L3QuNC90LBH0L4g0LfQsNCy0LXRgNGI0LXQvdC40Lgg0LrQvtC90LrRg9GA0YHQvdC+0LPQviDQv9GA0L7QuNC30LLQvtC00YHRgtCy0LBA0L4g0L/RgNC10LrRgNCw0YnQtdC90LjQuCDQv9GA0L7QuNC30LLQvtC00YHRgtCy0LAg0L/QviDQtNC10LvRg4MB0L4g0LLQvtC30L7QsdC90L7QstC70LXQvdC40Lgg0L/RgNC+0LjQt9Cy0L7QtNGB0YLQstCwINC/0L4g0LTQtdC70YMg0L4g0L3QtdGB0L7RgdGC0L7Rj9GC0LXQu9GM0L3QvtGB0YLQuCAo0LHQsNC90LrRgNC+0YLRgdGC0LLQtSlN0L7QsSDRg9GC0LLQtdGA0LbQtNC10L3QuNC4INCw0YDQsdC40YLRgNCw0LbQvdC+0LPQviDRg9C/0YDQsNCy0LvRj9GO0YnQtdCz0L5t0L7QsSDQvtGB0LLQvtCx0L7QttC00LXQvdC40Lgg0LjQu9C4INC+0YLRgdGC0YDQsNC90LXQvdC40Lgg0LDRgNCx0LjRgtGA0LDQttC90L7Qs9C+INGD0L/RgNCw0LLQu9GP0Y7RidC10LPQvogB0L4g0L/RgNC40LfQvdCw0L3QuNC4INC00LXQudGB0YLQstC40LkgKNCx0LXQt9C00LXQudGB0YLQstC40LkpINCw0YDQsdC40YLRgNCw0LbQvdC+0LPQviDRg9C/0YDQsNCy0LvRj9GO0YnQtdCz0L4g0L3QtdC30LDQutC+0L3QvdGL0LzQuNUB0L4g0LLQt9GL0YHQutCw0L3QuNC4INGBINCw0YDQsdC40YLRgNCw0LbQvdC+0LPQviDRg9C/0YDQsNCy0LvRj9GO0YnQtdCz0L4g0YPQsdGL0YLQutC+0LIg0LIg0YHQstGP0LfQuCDRgSDQvdC10LjRgdC/0L7Qu9C90LXQvdC40LXQvCDQuNC70Lgg0L3QtdC90LDQtNC70LXQttCw0YnQuNC8INC40YHQv9C+0LvQvdC10L3QuNC10Lwg0L7QsdGP0LfQsNC90L3QvtGB0YLQtdC5nQHQvtCxINGD0LTQvtCy0LvQtdGC0LLQvtGA0LXQvdC40Lgg0LfQsNGP0LLQu9C10L3QuNC5INGC0YDQtdGC0YzQuNGFINC70LjRhiDQviDQvdCw0LzQtdGA0LXQvdC40Lgg0L/QvtCz0LDRgdC40YLRjCDQvtCx0Y/Qt9Cw0YLQtdC70YzRgdGC0LLQsCDQtNC+0LvQttC90LjQutCwJtCU0YDRg9Cz0LjQtSDRgdGD0LTQtdCx0L3Ri9C1INCw0LrRgtGLJNCU0YDRg9Cz0LjQtcKg0L7Qv9GA0LXQtNC10LvQtdC90LjRjxUbAAIxMQExATkCMjkCMzACMzECMTgBNwIxMAIyNgIyNwIyMAIyMQIxOQIyNAIyNQIyOAE4ATMBNAE2AjIyAjIzAjE3AjEyAjE2FCsDG2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAgcPZBYIZg8PFgIfA2UWAh8EBSxPcGVuTW9kYWxXaW5kb3dfY3RsMDBfY3BoQm9keV9tZHNQdWJsaXNoZXIoKWQCAQ8PZBYCHwQFLE9wZW5Nb2RhbFdpbmRvd19jdGwwMF9jcGhCb2R5X21kc1B1Ymxpc2hlcigpZAICDw9kFgIfBAUiQ2xlYXJfY3RsMDBfY3BoQm9keV9tZHNQdWJsaXNoZXIoKWQCBQ8VASQvRGVidG9yTGlzdFdpbmRvdy5hc3B4P2lkVHlwZT1jb21tb25kAgsPZBYCZg8QDxYCHwVnZBAVXAAb0JDQu9GC0LDQudGB0LrQuNC5INC60YDQsNC5H9CQ0LzRg9GA0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywp0JDRgNGF0LDQvdCz0LXQu9GM0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywn0JDRgdGC0YDQsNGF0LDQvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJ9CR0LXQu9Cz0L7RgNC+0LTRgdC60LDRjyDQvtCx0LvQsNGB0YLRjB/QkdGA0Y/QvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJ9CS0LvQsNC00LjQvNC40YDRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCnQktC+0LvQs9C+0LPRgNCw0LTRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCXQktC+0LvQvtCz0L7QtNGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJdCS0L7RgNC+0L3QtdC20YHQutCw0Y8g0L7QsdC70LDRgdGC0YwQ0LMuINCc0L7RgdC60LLQsCHQsy4g0KHQsNC90LrRgi3Qn9C10YLQtdGA0LHRg9GA0LMa0LMuINCh0LXQstCw0YHRgtC+0L/QvtC70Yw20JTQvtC90LXRhtC60LDRjyDQvdCw0YDQvtC00L3QsNGPINGA0LXRgdC/0YPQsdC70LjQutCwNtCV0LLRgNC10LnRgdC60LDRjyDQsNCy0YLQvtC90L7QvNC90LDRjyDQvtCx0LvQsNGB0YLRjCPQl9Cw0LHQsNC50LrQsNC70YzRgdC60LjQuSDQutGA0LDQuSXQl9Cw0L/QvtGA0L7QttGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMI9CY0LLQsNC90L7QstGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMQdCY0L3Ri9C1INGC0LXRgNGA0LjRgtC+0YDQuNC4LCDQstC60LvRjtGH0LDRjyDQsy7QkdCw0LnQutC+0L3Rg9GAIdCY0YDQutGD0YLRgdC60LDRjyDQvtCx0LvQsNGB0YLRjDzQmtCw0LHQsNGA0LTQuNC90L4t0JHQsNC70LrQsNGA0YHQutCw0Y8g0KDQtdGB0L/Rg9Cx0LvQuNC60LAt0JrQsNC70LjQvdC40L3Qs9GA0LDQtNGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMIdCa0LDQu9GD0LbRgdC60LDRjyDQvtCx0LvQsNGB0YLRjB3QmtCw0LzRh9Cw0YLRgdC60LjQuSDQutGA0LDQuTzQmtCw0YDQsNGH0LDQtdCy0L4t0KfQtdGA0LrQtdGB0YHQutCw0Y8g0KDQtdGB0L/Rg9Cx0LvQuNC60LAl0JrQtdC80LXRgNC+0LLRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCHQmtC40YDQvtCy0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywl0JrQvtGB0YLRgNC+0LzRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCPQmtGA0LDRgdC90L7QtNCw0YDRgdC60LjQuSDQutGA0LDQuSHQmtGA0LDRgdC90L7Rj9GA0YHQutC40Lkg0LrRgNCw0Lkj0JrRg9GA0LPQsNC90YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywd0JrRg9GA0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywp0JvQtdC90LjQvdCz0YDQsNC00YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywf0JvQuNC/0LXRhtC60LDRjyDQvtCx0LvQsNGB0YLRjDjQm9GD0LPQsNC90YHQutCw0Y8g0L3QsNGA0L7QtNC90LDRjyDRgNC10YHQv9GD0LHQu9C40LrQsCXQnNCw0LPQsNC00LDQvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMI9Cc0L7RgdC60L7QstGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMI9Cc0YPRgNC80LDQvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMMNCd0LXQvdC10YbQutC40Lkg0LDQstGC0L7QvdC+0LzQvdGL0Lkg0L7QutGA0YPQsynQndC40LbQtdCz0L7RgNC+0LTRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCfQndC+0LLQs9C+0YDQvtC00YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywp0J3QvtCy0L7RgdC40LHQuNGA0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywb0J7QvNGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJ9Ce0YDQtdC90LHRg9GA0LPRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCHQntGA0LvQvtCy0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywj0J/QtdC90LfQtdC90YHQutCw0Y8g0L7QsdC70LDRgdGC0YwZ0J/QtdGA0LzRgdC60LjQuSDQutGA0LDQuR3Qn9GA0LjQvNC+0YDRgdC60LjQuSDQutGA0LDQuSHQn9GB0LrQvtCy0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywh0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JDQtNGL0LPQtdGPH9Cg0LXRgdC/0YPQsdC70LjQutCwINCQ0LvRgtCw0Lkt0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JHQsNGI0LrQvtGA0YLQvtGB0YLQsNC9I9Cg0LXRgdC/0YPQsdC70LjQutCwINCR0YPRgNGP0YLQuNGPJdCg0LXRgdC/0YPQsdC70LjQutCwINCU0LDQs9C10YHRgtCw0L0n0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JjQvdCz0YPRiNC10YLQuNGPJdCg0LXRgdC/0YPQsdC70LjQutCwINCa0LDQu9C80YvQutC40Y8j0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JrQsNGA0LXQu9C40Y8d0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JrQvtC80Lgd0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JrRgNGL0Lwk0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0JzQsNGA0LjQuSDQrdC7JdCg0LXRgdC/0YPQsdC70LjQutCwINCc0L7RgNC00L7QstC40Y8s0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0KHQsNGF0LAgKNCv0LrRg9GC0LjRjylB0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0KHQtdCy0LXRgNC90LDRjyDQntGB0LXRgtC40Y8gLSDQkNC70LDQvdC40Y8n0KDQtdGB0L/Rg9Cx0LvQuNC60LAg0KLQsNGC0LDRgNGB0YLQsNC9HdCg0LXRgdC/0YPQsdC70LjQutCwINCi0YvQstCwI9Cg0LXRgdC/0YPQsdC70LjQutCwINCl0LDQutCw0YHQuNGPI9Cg0L7RgdGC0L7QstGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMIdCg0Y/Qt9Cw0L3RgdC60LDRjyDQvtCx0LvQsNGB0YLRjCHQodCw0LzQsNGA0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywl0KHQsNGA0LDRgtC+0LLRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCXQodCw0YXQsNC70LjQvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJ9Ch0LLQtdGA0LTQu9C+0LLRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCPQodC80L7Qu9C10L3RgdC60LDRjyDQvtCx0LvQsNGB0YLRjCXQodGC0LDQstGA0L7Qv9C+0LvRjNGB0LrQuNC5INC60YDQsNC5I9Ci0LDQvNCx0L7QstGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMH9Ci0LLQtdGA0YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywd0KLQvtC80YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywf0KLRg9C70YzRgdC60LDRjyDQvtCx0LvQsNGB0YLRjCHQotGO0LzQtdC90YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywp0KPQtNC80YPRgNGC0YHQutCw0Y8g0KDQtdGB0L/Rg9Cx0LvQuNC60LAl0KPQu9GM0Y/QvdC+0LLRgdC60LDRjyDQvtCx0LvQsNGB0YLRjB/QpdCw0LHQsNGA0L7QstGB0LrQuNC5INC60YDQsNC5StCl0LDQvdGC0Yst0JzQsNC90YHQuNC50YHQutC40Lkg0LDQstGC0L7QvdC+0LzQvdGL0Lkg0L7QutGA0YPQsyAtINCu0LPRgNCwI9Cl0LXRgNGB0L7QvdGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMJdCn0LXQu9GP0LHQuNC90YHQutCw0Y8g0L7QsdC70LDRgdGC0Ywn0KfQtdGH0LXQvdGB0LrQsNGPINCg0LXRgdC/0YPQsdC70LjQutCwIdCn0LjRgtC40L3RgdC60LDRjyDQvtCx0LvQsNGB0YLRjDjQp9GD0LLQsNGI0YHQutCw0Y8g0KDQtdGB0L/Rg9Cx0LvQuNC60LAgLSDQp9GD0LLQsNGI0LjRjzLQp9GD0LrQvtGC0YHQutC40Lkg0LDQstGC0L7QvdC+0LzQvdGL0Lkg0L7QutGA0YPQszvQr9C80LDQu9C+LdCd0LXQvdC10YbQutC40Lkg0LDQstGC0L7QvdC+0LzQvdGL0Lkg0L7QutGA0YPQsyXQr9GA0L7RgdC70LDQstGB0LrQsNGPINC+0LHQu9Cw0YHRgtGMFVwAATECMTACMTECMTICMTQCMTUCMTcCMTgCMTkCMjACNDUCNDADMjAxAzIwNQI5OQMxMDEDMjA0AjI0AzIwMwIyNQI4MwIyNwIyOQIzMAI5MQIzMgIzMwIzNAEzATQCMzcCMzgCNDECNDIDMjA2AjQ0AjQ2AjQ3AzIwMAIyMgI0OQI1MAI1MgI1MwI1NAI1NgI1NwE1AjU4Ajc5Ajg0AjgwAjgxAjgyAjI2Ajg1Ajg2Ajg3AzIwMgI4OAI4OQI5OAMxMDICOTICOTMCOTUCNjACNjECMzYCNjMCNjQCNjUCNjYBNwI2OAIyOAI2OQI3MAI3MQI5NAI3MwE4AzEwMwMyMDcCNzUCOTYCNzYCOTcCNzcDMTA0Ajc4FCsDXGdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZGQCDQ9kFghmDw8WAh8DZRYCHwQFKU9wZW5Nb2RhbFdpbmRvd19jdGwwMF9jcGhCb2R5X21kc0RlYnRvcigpZAIBDw9kFgIfBAUpT3Blbk1vZGFsV2luZG93X2N0bDAwX2NwaEJvZHlfbWRzRGVidG9yKClkAgIPD2QWAh8EBR9DbGVhcl9jdGwwMF9jcGhCb2R5X21kc0RlYnRvcigpZAIFDxUBJC9EZWJ0b3JMaXN0V2luZG93LmFzcHg/aWRUeXBlPWNvbW1vbmQCDw9kFggCAw8PZBYEHghvbmNoYW5nZQU2U2V0SGlkZGVuRmllbGRfY3RsMDBfY3BoQm9keV9jbGRyQmVnaW5EYXRlKHRoaXMudmFsdWUpHgpvbmtleXByZXNzBTZTZXRIaWRkZW5GaWVsZF9jdGwwMF9jcGhCb2R5X2NsZHJCZWdpbkRhdGUodGhpcy52YWx1ZSlkAgUPD2QWAh8EBSpTaG93Q2FsZW5kYXJfY3RsMDBfY3BoQm9keV9jbGRyQmVnaW5EYXRlKClkAgYPD2QWBB4FU3R5bGUFMGN1cnNvcjogcG9pbnRlcjsgdmlzaWJpbGl0eTpoaWRkZW47IGRpc3BsYXk6bm9uZR8EBShDbGVhcklucHV0X2N0bDAwX2NwaEJvZHlfY2xkckJlZ2luRGF0ZSgpZAIHDw8WAh4YQ2xpZW50VmFsaWRhdGlvbkZ1bmN0aW9uBSlWYWxpZGF0ZUlucHV0X2N0bDAwX2NwaEJvZHlfY2xkckJlZ2luRGF0ZWRkAhEPZBYIAgMPD2QWBB8GBTRTZXRIaWRkZW5GaWVsZF9jdGwwMF9jcGhCb2R5X2NsZHJFbmREYXRlKHRoaXMudmFsdWUpHwcFNFNldEhpZGRlbkZpZWxkX2N0bDAwX2NwaEJvZHlfY2xkckVuZERhdGUodGhpcy52YWx1ZSlkAgUPD2QWAh8EBShTaG93Q2FsZW5kYXJfY3RsMDBfY3BoQm9keV9jbGRyRW5kRGF0ZSgpZAIGDw9kFgQfCAUwY3Vyc29yOiBwb2ludGVyOyB2aXNpYmlsaXR5OmhpZGRlbjsgZGlzcGxheTpub25lHwQFJkNsZWFySW5wdXRfY3RsMDBfY3BoQm9keV9jbGRyRW5kRGF0ZSgpZAIHDw8WAh8JBSdWYWxpZGF0ZUlucHV0X2N0bDAwX2NwaEJvZHlfY2xkckVuZERhdGVkZAIDD2QWAmYPZBYCAgcPZBYCZg9kFgJmD2QWAmYPFgIeBXN0eWxlBRRwYWRkaW5nLWJvdHRvbToyMHB4O2QYAgUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgsFFmN0bDAwJHJhZFdpbmRvd01hbmFnZXIFKWN0bDAwJFByaXZhdGVPZmZpY2UxJGliUHJpdmF0ZU9mZmljZUVudGVyBSFjdGwwMCRQcml2YXRlT2ZmaWNlMSRjYlJlbWVtYmVyTWUFIGN0bDAwJFByaXZhdGVPZmZpY2UxJFJhZFRvb2xUaXAxBR9jdGwwMCRQcml2YXRlT2ZmaWNlMSRpYnRSZXN0b3JlBSJjdGwwMCREZWJ0b3JTZWFyY2gxJGliRGVidG9yU2VhcmNoBRZjdGwwMCRjcGhCb2R5JGNiV2l0aEF1BR1jdGwwMCRjcGhCb2R5JGNiV2l0aFZpb2xhdGlvbgUeY3RsMDAkY3BoQm9keSRpYk1lc3NhZ2VzU2VhcmNoBRZjdGwwMCRjcGhCb2R5JGltZ0NsZWFyBRtjdGwwMCRjcGhCb2R5JGliRXhjZWxFeHBvcnQFGGN0bDAwJGNwaEJvZHkkZ3ZNZXNzYWdlcw88KwAMAQgCAWQb8THkuohegxP2nwFPJIIpTFMjpw==',
            '__VIEWSTATEGENERATOR': '8EE02EF5',
            '__ASYNCPOST': 'true',
            'ctl00$cphBody$ibMessagesSearch.x': '51',
            'ctl00$cphBody$ibMessagesSearch.y': '6',
        }

        try:
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            response = session.post('https://old.bankrot.fedresurs.ru/Messages.aspx', cookies=cookies, headers=headers, data=data)
            # response = requests.post('https://old.bankrot.fedresurs.ru/Messages.aspx', cookies=cookies, headers=headers, data=data, timeout=0.3)
        except requests.exceptions.ConnectionError as e:
            print(e)
        except requests.exceptions.ReadTimeout as e:
            print(e)

        if response:
            fn = "scrapy_data-" + str(k) + ".html"
            with open(fn, "w", encoding="utf-8") as f:
                f.write(response.text)
                files[k] = fn

            time.sleep(2)
        else:
            print("Запрос на получение данных не прошел")

    return files


def parse_scrapy_files(scrapy_files):
    url = "https://old.bankrot.fedresurs.ru"
    files = {}

    for reg, file in scrapy_files.items():
        items = {"debtors_list": []}
        file_to_save = f"scrapy_data-{reg}.json"

        with open(file, 'r', encoding="utf-8") as f:
            file_data = f.read()

        soup = BeautifulSoup(file_data, "lxml")
        table_tr = soup.find("table", id="ctl00_cphBody_gvMessages").find_all("tr")
        for line in table_tr[-1:0:-1]:
            table_tr_td = line.find_all("td")
            item = {
                "publication_datetime": table_tr_td[0].get_text().strip(),
                "publication_url": url + table_tr_td[1].a['href'],
                "debtor": table_tr_td[2].a.get_text().strip(),
                "debtor_card": url + table_tr_td[2].a['href'],
                "published_by": table_tr_td[4].a.get_text().strip() if table_tr_td[4].a else table_tr_td[
                    4].get_text().strip(),
                "published_url": url + table_tr_td[4].a['href'] if table_tr_td[4].a else ''
            }
            items["debtors_list"].append(item)

        with open(file_to_save, "w", encoding="utf-8") as f:
            f.write(json.dumps(items, ensure_ascii=False, sort_keys=False))
            files[reg] = file_to_save

    return files


def parse_json_files(parse_files):
    new_rows = {}
    for reg, file in parse_files.items():
        try:
            with open(file, "r", encoding="utf-8") as f:
                debtors_list = json.load(f)
            if len(debtors_list["debtors_list"]) > 0:
                new_rows[reg] = []
                db_name = f"db_{reg}-{pub_dt}.json"
                file_exists = os.path.exists(db_name)
                if file_exists:
                    with open(db_name, "r", encoding="utf-8") as f:
                        db_debtors = json.load(f)
                else:
                    db_debtors = {"debtors_list": [], "publications_datetime": []}

                for item in debtors_list["debtors_list"]:
                    if not item["publication_datetime"] in db_debtors["publications_datetime"]:
                        db_debtors["debtors_list"].append(item)
                        new_rows[reg].append(item)
                        db_debtors["publications_datetime"].append(item["publication_datetime"])

                with open(db_name, "w", encoding="utf-8") as f:
                    f.write(json.dumps(db_debtors, ensure_ascii=False, sort_keys=False, indent=2))
        except Exception as e:
            print(e)

    return new_rows


def start_schedule():
    schedule.every(6).minutes.do(send_message)

    while True:
        schedule.run_pending()
        time.sleep(1)


def send_message():
    scrapy_files = scrapy_data()
    parse_files = parse_scrapy_files(scrapy_files)
    add_new_debtors = parse_json_files(parse_files)

    l_str = []
    for nd in add_new_debtors:
        if len(add_new_debtors[nd]) > 0:
            l_str.append(f"\n<b>*** {regions[nd]} ***</b>\n")
            for item in add_new_debtors[nd]:
                l_str.append("\n-=-=-=-=-=-=-=-=-=-=-\n")
                for k, v in item.items():
                    if re.search('http', v):
                        l_str.append(f'<b><i>{translate[k]}</i></b>: <a href="{v}">перейти</a>\n')
                    else:
                        l_str.append(f'<b><i>{translate[k]}</i></b>: {v}\n')

    if len(l_str) > 0:
        mes = "".join(l_str)
        bot.send_message(256155479, mes, parse_mode="html")
    print(time.strftime('%c'))


if __name__ == "__main__":
    # send_message()

    print(time.strftime('%c'))
    start_schedule()
    try:
        bot.polling(none_stop=True)
    except:
        pass

    # scrapy_files = scrapy_data()
    # print(scrapy_files)
    # parse_files = parse_scrapy_files(scrapy_files)
    # add_new_debtors = parse_json_files(parse_files)

    # scrapy_files = scrapy_data()
    # scrapy_files = {45: 'scrapy_data-45.html', 46: 'scrapy_data-46.html'}
    # print(repr(scrapy_files))
    # parse_files = {45: 'scrapy_data-45.json', 46: 'scrapy_data-46.json'}
    # parse_files = parse_scrapy_files(scrapy_files)
    # print(repr(parse_files))
    # add_new_debtors = parse_json_files(parse_files)
    # print(json.dumps(add_new_debtors, ensure_ascii=False, sort_keys=False, indent=2))
