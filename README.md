### test work for Open solutions

###Порты на хост систему для проверки (подробнее в docker-compose.yml)

55432 - postgres

56379 - redis

###Сборка
> docker-compose build

###Запуск контейнеров
> docker-compose up

для запуска в фоне

> docker-compose up -d

###Проверка

Тестовые девайсы 123 и 456 создаются запросом из tcp_client

>CREATE DEVICE  123
>CREATE DEVICE  456

При удачном подключении tcp_client ответит

> CLIENT 123 CONNECTED TO 8889
> CLIENT 456 CONNECTED TO 8889

при этом tcp_server выведет в консоль

> Server: connected device id @123,name@
> Server: connected device id @456,name@

, а web сервер выведет в консоль

> web on_message_input {'id': 123, 'report': 'name'}
> web on_message_input {'id': 456, 'report': 'name'}

или (Если id устройства не записан в БД)

> web on_message_input UNKNOWN device_id {'id': 33, 'report': 'name'}


#### Проверка с хост системы

Создает утсройства, сохраняет репорты, получает репорты выводит в консоль, проверяет наличие ключей в redis

> ./test.sh

после выполнения команды, по факту сохранения репорта в обменник брокера передается сообщение в очередь output, на которое подписался tcp_server.
При получении сообщения tcp_server выведет в консоль список всех подключенных клиентов, и отправит клиенту сообщение:

>  send to client 123
>  send to client 456

после чего клиент получит из потока связи с сервером сообщение и выведет его в консоль

> client01_1     | 2020-01-21 09:37:48.788244: Data b'@123,name@', Success
> client02_1     | 2020-01-21 09:37:48.811040: Data b'@456,name@', Success

"Success" означает что device_id клиента (заданный при подключении) совпал с полученным из потока

