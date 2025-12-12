import socket
import sys

# Настройки для подключения к ESP8266
ESP_IP = '192.168.4.166'  # <--- ЗАМЕНИТЕ на IP-адрес, который вы получили в Serial Monitor
ESP_PORT = 80  # Должен совпадать с serverPort в коде ESP8266


def send_led_command(command):
    """
    Отправляет команду ON или OFF на TCP-сервер ESP8266.
    """
    if command.upper() not in ["ON", "OFF"]:
        print("Неверная команда. Используйте 'ON' или 'OFF'.")
        return

    # Создаем сокет (IPv4, TCP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            print(f"Попытка подключения к {ESP_IP}:{ESP_PORT}...")
            # Устанавливаем соединение
            client_socket.connect((ESP_IP, ESP_PORT))
            print("✅ Успешно подключен.")

            # Команда должна быть отправлена с символом новой строки (\n),
            # так как сервер ESP8266 читает до '\n'.
            full_command = command.upper() + "\n"

            # Отправляем команду, кодируя ее в байты
            client_socket.sendall(full_command.encode('utf-8'))
            print(f"-> Отправлено: '{command.upper()}'")

            # Получаем ответ от сервера
            response = client_socket.recv(1024)
            print(f"<- Получено от ESP: {response.decode('utf-8').strip()}")

        except ConnectionRefusedError:
            print(f"❌ Ошибка: Соединение отклонено. ESP8266 не запущен или не подключен к сети.")
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        # Проверяем, что пользователь передал команду как аргумент
        print("Использование: python client.py [ON/OFF]")
        print("Пример: python client.py ON")
    else:
        # Запускаем отправку команды
        send_led_command(sys.argv[1])