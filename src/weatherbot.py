from telegram.ext import Updater, CommandHandler
from datetime import *
import logging
import pyowm
import time

telegram_token = '892630064:AAFon_wv9u32z0zj4i-P-bOIHo_6FMpSAOo'
owm_key = '1424e0ec4742f956215bafa133857eb0'
owm = pyowm.OWM(owm_key)
subscriber_list = list()
user_data = dict()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    update.message.reply_text("Hey, I'm a weather bot! Type /now <city> to get information about the "
                              "weather in your location. Example: /now London\n"
                              + "You can fing available commands in /help")


def help_handler(bot, update):
    update.message.reply_text("Available commands:\n" +
                              "/location <city> - set your current city\n" +
                              "/subscribe - subscribe to the daily weather forecast\n" +
                              "/unsubscribe - unsubscribe from it\n" +
                              "/now - current weather\n" +
                              "/forecast - forecast at any particular time of day. Example: /forecast 20:00\n" +
                              "/week - forecast for 5 days/every 3 hours")


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def weather_now(bot, update, args):
    if len(args) > 0:
        text_location = "".join(str(x) for x in args)
    else:
        chat_id = update.message.chat_id
        if chat_id in user_data:
            text_location = user_data.get(chat_id)
        else:
            update.message.reply_text("Please set the location first with the command /location <place>. Example: "
                                      "/location London")
            return
    observation = owm.weather_at_place(text_location)
    weather = observation.get_weather()
    update.message.reply_text(print_weather(weather, text_location))


def print_weather(weather, place):
    result_string = ""
    date_time = weather.get_reference_time(timeformat='date')
    humidity = weather.get_humidity()
    wind = weather.get_wind()
    temp = weather.get_temperature('celsius')
    convert_temp = temp.get('temp')
    convert_wind = wind.get('speed')
    convert_humidity = humidity
    text_temp = str(convert_temp)
    text_wind = str(convert_wind)
    text_humidity = str(convert_humidity)
    status = weather.get_status()
    result_string += "Weather in : " + place + ' at ' + date_time.strftime("%d.%m.%y %H:%M") + "\n"
    result_string += status + "\n"
    result_string += "Temperature, celsius: " + text_temp + "\n"
    result_string += "Wind speed, m/s: " + text_wind + "\n"
    result_string += "Humidity, %: " + text_humidity + "\n"
    result_string += "Нехай проблеми та невзгоди не роблять Вам в житті погоди, хай Вам щастить, і будьте здорові!"
    return result_string


def weather_5day(bot, update, args):
    if len(args) > 0:
        text_location = "".join(str(x) for x in args)
    else:
        chat_id = update.message.chat_id
        if chat_id in user_data:
            text_location = user_data.get(chat_id)
        else:
            update.message.reply_text("Please set the location first with the command /location <place>. Example: "
                                      "/location London")
            return
    fc = owm.three_hours_forecast(text_location)
    f = fc.get_forecast()
    f.actualize()
    weathers = f.get_weathers()
    for weather in weathers:
        update.message.reply_text(print_weather(weather, text_location))


def weather_at(bot, update, args):
    if len(args) == 2:
        text_location = str(args[0])
        time_string = str(args[1])
        datetime_time = datetime.strptime(time_string, '%H:%M').time()
    else:
        if len(args) == 1:
            arg = str(args[0])
            if has_numbers(arg):
                time_string = arg
                datetime_time_temp = datetime.strptime(time_string, '%H:%M').time()
                datetime_time = datetime.combine(datetime.today(), datetime_time_temp)
                chat_id = update.message.chat_id
                if chat_id in user_data:
                    text_location = user_data.get(chat_id)
                else:
                    update.message.reply_text("Please set the location first with the command /location <place>. "
                                              "Example: /location London")
                    return
            else:
                weather_now(bot, update, str(args[0]))
                return
        else:
            if len(args) == 0:
                weather_now(bot, update, args)
                return
            else:
                update.message.reply_text("Wrong input. Please type something like /forecast 18:00 or /forecast "
                                          "London 18:00")
                return
    fc = owm.three_hours_forecast(text_location)
    f = fc.get_weather_at(datetime_time)
    update.message.reply_text(print_weather(f, text_location))


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def subscribe(bot, update):
    chat_id = update.message.chat_id
    if chat_id in user_data:
        subscriber_list.append(chat_id)
        update.message.reply_text("You will receive weather forecast starting from tomorrow 7:00")
    else:
        update.message.reply_text("Please set the location first with the command /location <place>. Example: "
                                  "/location London")


def unsubscribe(bot, update):
    chat_id = update.message.chat_id
    if chat_id in subscriber_list:
        subscriber_list.remove(chat_id)
        update.message.reply_text("You are unsubscribed from the weather forecast")


def send_subscription(bot, job):
    i = 0
    for chat_id in user_data.keys():
        place = user_data.get(chat_id)
        fc = owm.three_hours_forecast(place)
        f = fc.get_forecast()
        weathers = f.get_weathers()
        result_string = ""
        for weather in weathers[:8]:
            result_string += print_weather(weather, place)
        bot.send_message(chat_id, result_string)
        if i == 59:
            i = 0
            time.sleep(60)


def location(bot, update, args):
    chat_id = update.message.chat_id
    city_text = "".join(str(x) for x in args)
    if city_text is None or city_text == "":
        update.message.reply_text("PLease type some place like this: /location <place>. Example: "
                                  "/location London")
    else:
        user_data.update({chat_id: city_text})
        update.message.reply_text("I saved location " + city_text)


def main():
    updater = Updater(telegram_token)

    dp = updater.dispatcher

    job_queue = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_handler))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("location", location, pass_args=True))
    dp.add_handler(CommandHandler("now", weather_now, pass_args=True))
    dp.add_handler(CommandHandler("week", weather_5day, pass_args=True))
    dp.add_handler(CommandHandler("forecast", weather_at, pass_args=True))

    job_queue.run_daily(send_subscription, datetime(2019, 0o7, 0o7, 0o7, 00, 00))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
