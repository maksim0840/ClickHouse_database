Программа представляет собой класс базы данных "DB", содержащей вложенные классы-таблицы "users_info", "urls_info", "visitors_info",
использующиеся для отправки запросов СУБД ClickHouse.

Схема базы данных
===================================
 ![db_scheme](https://github.com/maksim0840/ClickHouse_database/assets/117035413/06ef8542-701e-4ba5-8b36-7af962a4d766)

Архитектура программы
===================================
![program_architecture](https://github.com/maksim0840/ClickHouse_database/assets/117035413/ef84e604-8adf-4747-a888-cde2cd6e825b)

QuickStart
===================================
Подключение:
-----------------------------------
1) Закидываем папку пакета "ClientWrapper" в директорию файла вашей программы
2) Устанавливаем библиотеку clickhouse_driver для обращения к базе данных
3) Импортируем все зависимости из пакета "ClientWrapper"
4) Создаём объект класса DB

При подключении класса подтягиваются данные для подключения к базе данных из файла "secret.py" и SSL-сертификат, служащий для шифрованного соединения. При создании объекта класса генерируется клиент для обращения к базе данных и вместе с этим инициализируются вложенные классы, нужные для обращения к конкретной таблице.

 ```pip install clickhouse_driver```
 
```python
from ClientWrapper import *
db = DB()
```

Классы By и Column
-----------------------------------
Эти классы ClientWrapper запрашивает из файла containers. Они созданы для упрощения запросов на поиск или удаление данных, помогая структуризировать запрос и сократить его.

1) Класс Column хранит переменные-константы (поля), а класс By под теми же именами хранит методы, позволяющие передать в них занчение. Возвращаемыми методомами By значениями будут являться те же константы, что находятся под таким же именем в Column, но с добавлением переданного значения.
2) При вызове поля класса "Column" нужно указать через '.' только название столбца, при указании класса "By" нужно указать через '.' название столбца и параметр-фильтр, по которому будет искаться инфомрация в скобочках
3) Поля Column указываются для того, чтобы показать с какой колонкой будет происходить действие, а методы By - это фильтр, в который передаются название колонки и значение, по кторому будут искаться те колонки Column, которые связанны с указанным в By значением
4) База данных не имеет повторяющихся названий столбцов в двух разных таблицах, что позволяет не указывать названия таблиц из которых следует искать переданные столбцы, а составлять запросы и искать зависимости, работая только с названиями столбцов.
5) Передаваемое значение в метод By обязательно должно совпадать по типу с рассматриваемой колонкой, иначе программа может выдать ошибку.

Доступные обращения к полям/методам:
- USER_ID, IP, USERNAME, PASSWORD, REGISTRATION_DATE - таблица "users_info"
- URL_ID, OWNER_ID, SHORT_URL, URL, DATA_COLLECTION, CREATION_DATE - таблица "urls_info"
- NOTE_ID, RESOURCE_ID,VISITOR_IP, VISIT_DATE, COUNTRY, CITY - таблица "visitors_info"

Примеры обращения к классам
```python
Column.USER_ID
By.USERNAME("useruser2310")
```

Методы подклассов DB:
-----------------------------------
Класс DB имеет 3 вложенных подкласса ("users_info", "urls_info", "visitors_info"), которые имеют одинаковую структуру и методы.

Для работы с конкретной таблицей обращаемся ко вложенным классам по следующим методам:

- `create()` - Создаёт таблицу выбронного подкласса, если таблицы не существует
- `drop()` - Удаляет таблицу выбронного подкласса, если таблица существует
- `clear()` - Очищает все данные полей таблицы выбранного подкласса, если таблица существует
- `print(output="console", rows=-1)` - Печатает данные таблицы на экран построчно в виде массива (output="console"), или добавляет (append-ит) в файл построчно (output="path_to_file.extension"), или отдёт массив для записи в перменную (output="variable"). Через параметр rows можно указать число строк, которые будут напечатаны (отрицательные значения печатают всю таблицу целиком)\
  _[возвращает: массив с min(указанным(>=0), действительным) количеством строк таблицы (если парметр output="variable")]_
- `append_from_file(file_name)` - Добавляет (append-ит) информацию в таблицу из указанного файла с зданным именем/путём файла (с указанием расширения)
- `get_all(by)` - Получает всю информацию из указанной таблицы (всю таблицу), по переданному через метод класса "By" значению\
  _[возвращает: массив с удовлетворяющими запросу строками таблицы]_
  
Примеры использования методов вложенных классов для работы с таблицей
```python
# Создание/удаление таблицы

db.users_info.create()
db.users_info.drop()
db.users_info.clear()

# Вывод/взятие ифнормации

db.users_info.print() # всю табилцу целиком в консоль
db.users_info.print(rows=10) # первые 10 строчек
value = db.users_info.print("variable")

print(db.visitors_info.get_all(By.NOTE_ID("Romania")))
dataframe = db.visitors_info.get_all(By.NOTE_ID("Romania"))

print(db.users_info.get_all(By.URL("https://url.url")))

# Работа с файлами

db.users_info.print("file.csv") # запись в файл (write параметром "a")
db.users_info.print("file.csv", 5) # первые 5 строчек
db.users_info.append_from_file("file.csv") # запись в базу данных из файла
```

Правила работы с файлами (для методов print и append_from_file):

1) Строчки таблицы разделены переносом строки ('\n')
2) Значения в строчке разделены ';'
3) Все значения указаны в верном порядке, без лишних знаков
4) В одном файле может нахдится записи только одной таблицы
5) Файл сохранён текстовом формате
6) При загрузке данных их корректность, полнота и ункальность проверяется только ограничаниями типов, заданных в столбцах таблицы

Методы класса DB:
-----------------------------------
- `get(column, by)` - Получает информацию из колонки под именем переданной перменной класса "Column", связанную с информацией из колонки, переданную под именем метода класса "By" с указанием значения\
  _[возвращает: массив с удовлетворяющими запросу занчениями(если такой строчки нет возвращает []; а если она есть, но значение пустое (незаполненное), то возвращает [['']] ]_
- `delete(by)` - Удаляет информацию из таблицы, по указанному значению, переданного методу класса "By"
- `check_auth(username, password)` - Проверяет авторизацию пользователя\
  _[возвращает: пароль подходит - True, пароль не подходит - False, пользователя не существует - None]_ 
- `create_new_user(ip="0.0.0.0", username="", password="")` - Добавляет информацию о новом пользователе в таблицу "users_info". Если пользователь не зарегестрировался на сайте, а просто хочет создать ссылку, то для его добавления можно указывать только поле "ip", если пользователь зарегестрировался нужно указать "ip", "username", "password"\
  _[возвращает: ник занят - None, запись успешно добавлена - user_id]_
- `create_new_url(owner_id, short_url="", url="")` - Добавляет инфомрацию о переданной пользователем ссылке в таблицу "urls_info"\
  _[возвращает: такого айди не сущесвтует - None, запись успешно добавлена - url_id]_
- `create_visitor_note(resource_id, visitor_ip="0.0.0.0", country="", city="")` - Добавляет информацию о новом переходе по ссылке в таблицу "visitors_info"\
  _[возвращает: такого айди не сущесвтует или аккаунт не имеет прав на статистику - None, запись успешно добавлена - note_id]_

Примеры использования методов класса для работы с базой данных
```python
# Пример работы с пользователем без авторизации:


# Добавить пользователя в базу
id = db.create_new_user(ip="143.122.100.250")

# Создание ссылки с сохранением url_id
url_id1 = db.create_new_url(id, "https://shrot_url", "https://user_long_long_url")

# Создание ссылки без сохранения url_id и попытки его восстановить
db.create_new_url(id, "https://shrot_url", "https://user_long_long_url") # добавить ссылку без сохранения url_id
url_id_list = db.get(Column.URL_ID, By.USER_ID(id))
# или
url_id_list = db.get(Column.URL_ID, By.IP("143.122.100.250"))
# или
url_id_list = db.get(Column.USERNAME, By.URL("https://user_long_long_url"))

# Удаление записей
db.delete(By.URL_ID(url_id1)) # удалить из urls_info
db.delete(By.ID(id)) # полностью удалить информацию
db.delete(By.USERNAME(id)) # полностью удалить информацию


# Пример работы с пользователем c авторизацией:


# Регистрация пользователя
db.create_new_user("198.203.021.122", "useruser1010", "123zxc123") #  без получения id

# Получить потерянный id
ids_list = db.get(Column.USER_ID, By.USERNAME("useruser1010"))
if (ids_list == []):
   print("Пользователь не найден")
else:
   user_id = ids_list[0]
   print("id пользователя найден")

# Проверить авторизацию
if (db.check_auth("useruser1010", "zxc") == True):
   print("Пароль верный")
else:
   print("Пользователя с таким ником не существует или пароль невреный")

# Добавить ссылку с получением url_id
url_id = db.create_new_url(user_id, "https://shrot_url", "https://user_long_long_url")

# Создать записи посетителей ссылки
create_visitor_note(url_id, "1.2.3.4", "Country1", "City1")
create_visitor_note(url_id, "5.6.7.8", "Country2", "City2")
create_visitor_note(url_id, "9.10.11.12", "Country3", "City3")

# Удалить всю информацию связанную с пользователем
db.delete(By.USERNAME("useruser1010"))
# или
db.delete(By.USER_ID(user_id))
```

Доступ пользователей и автоматическое удаление данных (для методов create_new_user, create_new_url, create_visitor_note):

1) Незарегестрированный пользователь может создавать укороченные ссылки, но информация о переходах по ним не будет сохраняться в базу данных, и пользователь не будет иметь доступа к просмотру (колонка "data collection" - показатель доступа к таблице "visitors_info"). По истечению срока 30 дней (со дня создания записи в таблицы отдельно взятого пользовтеля) информация о пользователе в таблице "users_info" и его ссылки в таблице "urls_info" по независимому друг от друга сроку будет удалена базой данных автоматически.
2) Зарегестрированный пользователь может создавать укороченные ссылки, и ифнормация о его аккаунте в таблице "users_info" никогда не будет удалена автоматически. Также пользователь будет иметь доступ на просмотр статистики переходов по ссылке, информация о которой будет сохраняться в таблицу "visitors_info".
3) Информация о переходах по ссылке в таблице "visitors_info" независимо от типа аккаунта будет автоматически удалятся спустя 30 дней (каждая отдельная запись имеет свой срок, независимый от других)

Ручное удаление данных (для метода delete):

Каждая следующая таблица зависит от записей предыдущих (users_info -> urls_info -> visitors_info), поэтому если удалить данные в более близкой к началу иерархии таблице, то все следующие таблицы и их записи, связанные с этой инфрмацией, тоже будут удалены (пример: если удалить информацию по "short_url", то удаляются все связанные с этим параметром только строки таблиц "urls_info" и "visitors_info").
