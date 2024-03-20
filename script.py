import requests
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_data(data):
    events_data = []
    for event in data['Value']:
        event_info = {
            'homeTeam': event.get("O1", "Недоступно"),
            'awayTeam': event.get("O2", "Недоступно")
        }

        for total in event.get("E", []):
            group = total.get("G")
            if group == 17:
                event_info['total'] = total.get("P", "Не указан")
            elif group == 15:
                event_info['home'] = total.get("P", "Не указан")
            elif group == 62:
                event_info['away'] = total.get("P", "Не указан")

        events_data.append(event_info)

    return events_data

def send_telegram_message(bot_token, chat_id, message):
    """Отправляет сообщение в Telegram."""
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    send_params = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    response = requests.get(send_url, params=send_params)
    return response.json()

def main():
    bot_token = "6979637911:AAERF6iIlMmzoAFgpGsxQesbJmly3RKDRxw"  # Замените на ваш токен от BotFather
    chat_id = "271084305"  # Замените на ваш chat_id в Telegram

    try:
        data_url = "https://betwinner-232507.top/service-api/LiveFeed/Get1x2_VZip?sports=3&champs=2626462&count=20&gr=495&mode=4"
        predict_url = "http://3.65.182.213:5000/predict"
        headers = {'Content-Type': 'application/json'}

        response = requests.get(data_url)
        if response.status_code == 200:
            data = response.json()
            processed_data = parse_data(data)

            response = requests.post(predict_url, data=json.dumps(processed_data), headers=headers)
            if response.status_code == 200:
                predict_response = response.json()

                for item in predict_response:
                    if 'messages' in item and item['messages']:
                        message_text = f"{item['homeTeam']} vs {item['awayTeam']}:\n" + "\n".join(item['messages'])
                        telegram_response = send_telegram_message(bot_token, chat_id, message_text)
                        if telegram_response.get("ok"):
                            print("Сообщение успешно отправлено в Telegram.")
                        else:
                            print(f"Ошибка при отправке сообщения в Telegram: {telegram_response}")
            else:
                print(f"Ошибка при отправке данных на сервер предсказаний: HTTP {response.status_code}")
                print(f"Ответ сервера: {response.text}")
        else:
            print(f"Ошибка при получении данных: HTTP {response.status_code}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == '__main__':
    main()
