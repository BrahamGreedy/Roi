#include <ESP8266WiFi.h>

// Настройки вашей Wi-Fi сети
const char* ssid = "class 2G";     // <--- Введите имя вашей Wi-Fi сети
const char* password = "zvezda2021"; // <--- Введите пароль

// Порт, который будет слушать сервер
const int serverPort = 80;

// Вывод, к которому подключен встроенный светодиод
// (Обычно это D4/GPIO2 на NodeMCU/D1 mini. Он активен низким уровнем!)
const int LED_PIN = 2; 

// Объект сервера, который будет слушать подключения
WiFiServer server(serverPort);

void setup() {
  Serial.begin(115200);
  
  // Настройка вывода светодиода
  pinMode(LED_PIN, OUTPUT);
  // Начнем с выключенного состояния (LOW = ON для встроенного LED на GPIO2!)
  digitalWrite(LED_PIN, HIGH); 
  
  // Подключение к Wi-Fi
  Serial.print("Подключение к ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  // Успешное подключение
  Serial.println("\nWiFi подключен.");
  Serial.print("IP адрес: ");
  Serial.println(WiFi.localIP());

  // Запуск сервера
  server.begin();
  Serial.print("Сервер запущен на порту: ");
  Serial.println(serverPort);
  Serial.println("Ожидание команд...");
}

void loop() {
  // Проверяем, есть ли новые клиенты, пытающиеся подключиться
  WiFiClient client = server.available();
  
  if (client) {
    Serial.println("\n[НОВОЕ СОЕДИНЕНИЕ]");
    
    // Читаем первую строку команды от клиента
    String command = client.readStringUntil('\n');
    command.trim(); // Убираем пробелы и символы новой строки
    
    Serial.print("Получена команда: ");
    Serial.println(command);
    
    // Обработка команды
    if (command == "ON") {
      // Встроенный светодиод на GPIO2 обычно активен LOW
      digitalWrite(LED_PIN, LOW); // LOW включает LED
      client.println("LED ON");
      Serial.println("-> Светодиод ВКЛ");
    } else if (command == "OFF") {
      digitalWrite(LED_PIN, HIGH); // HIGH выключает LED
      client.println("LED OFF");
      Serial.println("-> Светодиод ВЫКЛ");
    } else {
      client.println("Неизвестная команда. Используйте ON или OFF.");
    }
    
    // Даем клиенту время получить ответ
    delay(1);
    // Закрываем соединение
    client.stop();
    Serial.println("[СОЕДИНЕНИЕ ЗАКРЫТО]");
  }
}