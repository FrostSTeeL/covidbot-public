import datetime
import threading
import time

import pandas as pd
import requests
import schedule
from bs4 import BeautifulSoup, CData
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

token = 'Token'
update_interval = 30
data_url = 'https://covid19.saglik.gov.tr/TR-66935/genel-koronavirus-tablosu.html'


# Initial data update ###################################################################################################

page = requests.get(data_url)
htmlpage = BeautifulSoup(page.text, 'html.parser')
scriptelements = htmlpage.find_all('script')
scriptcontent = ['date']
check = scriptcontent[0]
string = ""
for script in scriptelements:
    string = str(script)
    if 'CDATA' in string and 'geneldurumjson' in string:
        scriptcontent = string.replace('//<![CDATA[', '').replace('var geneldurumjson = ', '').replace(
            '{', '').replace('}', '').replace(';//]]>', '').replace("[", "").replace("]", "").replace('"', "").split(",")
        scriptcontent = [i.split(':')[-1] for i in scriptcontent]
        check = scriptcontent[0]
        print('Initial data update has been completed...\n')

# Data updater on interval ##############################################################################################


def data_main():
    print(
        f'Data updater started with the frequency of {update_interval} minutes...\n')

    def get_data():
        page = requests.get(data_url)
        htmlpage = BeautifulSoup(page.text, 'html.parser')
        scriptelements = htmlpage.find_all('script')
        global scriptcontent
        global check
        string = ""
        for script in scriptelements:
            string = str(script)
            if 'CDATA' in string and 'geneldurumjson' in string:
                scriptcontent = string.replace('//<![CDATA[', '').replace('var geneldurumjson = ', '').replace(
                    '{', '').replace('}', '').replace(';//]]>', '').replace("[", "").replace("]", "").replace('"', "").split(",")
                scriptcontent = [i.split(':')[-1] for i in scriptcontent]
                if check == scriptcontent[0]:
                    print(f'Still using {check} data')
                    pass
                else:
                    check = scriptcontent[0]
                    print(f'*** Data updated for: {check} ***')

    schedule.every(update_interval).minutes.do(get_data)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main_bot():
    print("Bot started...\n")

# Command throttler ####################################################################################################
    
    throttle_data = {
        'seconds': 3,
        'last_time': None
    }

    def throttle(func):
        def wrapper(*args, **kwargs):
            now = datetime.datetime.now()
            delta = now - \
                datetime.timedelta(seconds=throttle_data.get('seconds', 3))
            last_time = throttle_data.get('last_time')
            if not last_time:
                last_time = delta

            if last_time <= delta:
                throttle_data['last_time'] = now
                func(*args, **kwargs)
            else:
                return not_allowed(*args)
        return wrapper

    def not_allowed(update, context):
        update.message.reply_text(text="Komutlar arası 3 saniye beklemelisin.")

    def sample_responses(input_text):
        user_message = str(input_text).lower()
        if user_message in ("hello", "hi", "sup", "selam"):
            return "Selam!"
        return f'Anlayamadım 😟\n\nBu komutlarla bilgi sorgulayabilirsin:\n/hepsi /asi /test /vaka /hasta /vefat /iyi'
            
# Bot commands ########################################################################################################

    def start_command(update, context):
        first_name = update.message.from_user.first_name
        first_data = update.message.from_user
        print(f'{first_data} - started using bot!')
        update.message.reply_text(
            f'Merhaba {first_name}!\n\nBu komutlarla bilgi sorgulayabilirsin: /hepsi /asi /test /vaka /hasta /vefat /iyi')

    @throttle
    def help_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'Merhaba {first_name}!\n\nBu komutlarla bilgi sorgulayabilirsin: /hepsi /asi /test /vaka /hasta /vefat /iyi\n\nVeriler https://covid19.saglik.gov.tr sitesinden alınmaktadır.\n\nAnlık aşı verileri, bu zamana kadar yapılan aşıların ortalaması alınarak hesaplanmaktadır.', disable_web_page_preview=True)

    @throttle
    def asi_command(update, context):
        command = update.message.text
        df = pd.read_html(
            "https://covidvax.live/location/tur", parse_dates=True,)
        abcde = df[5].head(1)
        new_dose = str(format(abcde.iloc[0, 3], ',d'))
        update.message.reply_text(
            f'Gün içerisinde {new_dose} doz aşı yapıldı. 💉💉💉')

    @throttle
    def vaka_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde, {scriptcontent[2]} vaka tespit edildi. 🤒🤒🤒')

    @throttle
    def test_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde, {scriptcontent[1]} test yapıldı. 🧪🧪🧪')

    @throttle
    def hasta_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde, {scriptcontent[3]} hasta tespit edildi. 🦠🦠🦠')

    @throttle
    def vefat_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde, {scriptcontent[4]} hasta vefat etti. ⬛⬛⬛')

    @throttle
    def iyi_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde, {scriptcontent[5]} hasta iyileşti. 🎉🎉🎉')

    @throttle
    def hepsi_command(update, context):
        command = update.message.text
        update.message.reply_text(
            f'{scriptcontent[0]} tarihinde yapılan test sayısı {scriptcontent[1]}.\nToplam {scriptcontent[2]} vaka, {scriptcontent[3]} hasta teşhis edildi.\nVefat sayısı {scriptcontent[4]}, iyileşen hasta sayısı {scriptcontent[5]}.')

    def handle_message(update, context):
        text = str(update.message.text).lower()
        response = sample_responses(text)
        update.message.reply_text(response)

    def error(update, context):
        id = update.message.from_user.id
        command = update.message.text
        print(f'{id} caused error with {command}! {context.error}')

# Main bot ########################################################################################################        

    def main():
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler('start', start_command))
        dp.add_handler(CommandHandler('help', help_command))
        dp.add_handler(CommandHandler('asi', asi_command))
        dp.add_handler(CommandHandler('vaka', vaka_command))
        dp.add_handler(CommandHandler('test', test_command))
        dp.add_handler(CommandHandler('hasta', hasta_command))
        dp.add_handler(CommandHandler('vefat', vefat_command))
        dp.add_handler(CommandHandler('iyi', iyi_command))
        dp.add_handler(CommandHandler('hepsi', hepsi_command))
        
        dp.add_handler(MessageHandler(Filters.text, handle_message))
        dp.add_error_handler(error)

        updater.start_polling()
        updater.idle()

    main()

# Data updater thread #############################################################################################
thread = threading.Thread(target=data_main, daemon=True)
thread.start()
main_bot()
