import logging

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Чтобы получить список заправок - воспользуйтесь /stations\n"
                                                                          "Чтобы получить список заправок по городу - воспользуйтесь /stations город\n"
                                                                          "Чтобы получить информацию о заправке - воспользуйтесь /station id")


async def stations(update: Update, context: CallbackContext.DEFAULT_TYPE):
    # Get fuel stations list from API and provide it to user
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы не указали фильтр, проверка всех заправок")
        context.args = [""]
    try:
        response = requests.get(url='https://api.wog.ua/fuel_stations')
        if response.status_code == 200:
            data = response.json()['data']
            stations = data['stations']
            filtered_stations = [station for station in stations if
                                 ('name' in station.keys() and context.args[0] in station['name']) or
                                 ('city' in station.keys() and context.args[0] in station['city'])
                                 ]
            logging.info(f'Got request response: %s', response)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f'Найдено {len(filtered_stations)} заправок')
            if len('\n'.join([f'{station["id"]} - {station["name"]}' for station in filtered_stations])) < 4096:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='\n'.join([f'{station["id"]} - {station["name"]}' for station in filtered_stations]))
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text='Слишком много заправок для отправки')
        else:
            logging.error(f'Got request response: %s', response)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Список заправок на данный момент недоступен')
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Список заправок на данный момент недоступен")


async def station(update: Update, context: CallbackContext.DEFAULT_TYPE):
    # Get fuel station info from API and provide it to user
    try:
        response = requests.get(url=f'https://api.wog.ua/fuel_stations/{context.args[0]}')
        if response.status_code == 200:
            data = response.json()['data']
            fuel_station_info = ""
            if 'city' in data.keys():
                fuel_station_info += f'Город: {data["city"]}\n'
            if 'coordinates' in data.keys():
                fuel_station_info += f'Заправка на карте: https://maps.google.com/?q={data["coordinates"]["latitude"]},{data["coordinates"]["longitude"]}\n'
            if 'fuels' in data.keys():
                fuel_station_info += f'Топливо: {", ".join([fuel["name"] for fuel in data["fuels"]])}\n'
            if 'name' in data.keys():
                fuel_station_info += f'Название: {data["name"]}\n'
            if 'schedule' in data.keys():
                if data['schedule'] is list:
                    fuel_station_info += f'Расписание: {", ".join([schedule["name"] for schedule in data["schedule"]])}\n'
                else:
                    fuel_station_info += f'Расписание: {data["schedule"]}\n'
            if 'services' in data.keys():
                fuel_station_info += f'Услуги: {", ".join([service["name"] for service in data["services"]])}\n'
            if 'workDescription' in data.keys():
                fuel_station_info += f'Описание работ: {data["workDescription"]}\n'
            if len(fuel_station_info) < 4096:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=fuel_station_info)
            else:
                # Split text into chunks
                chunks = [fuel_station_info[i:i + 4096] for i in range(0, len(fuel_station_info), 4096)]
                for chunk in chunks:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk)
        else:
            logging.error(f'Got request response: %s', response)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Информация о запрошенной заправке на данный момент недоступна')
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Информация о запрошенной заправке на данный момент недоступна')


if __name__ == '__main__':
    application = ApplicationBuilder().token('TOKEN').build()

    start_handler = CommandHandler('start', start)
    stations_handler = CommandHandler('stations', stations)
    station_handler = CommandHandler('station', station)
    application.add_handler(start_handler)
    application.add_handler(stations_handler)
    application.add_handler(station_handler)

    application.run_polling()