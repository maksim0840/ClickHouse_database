Программа представляет собой класс базы данных "DB", содержащей
вложенные классы-таблицы: "users_info", "urls_info", "visitors_info"

QuickStart

Подключение:
1) Преносим папку с проектом в дирректорию на один уровень к вашей программе
2) Устанавливаем библиотеку clickhouse_driver для обращения к базе данных
   ```pip install clickhouse_driver```
4) Импортируем класс DB из файла ClientWrapper
5) Создаём объект класса DB

При подключении класса, к нему подтягиваются данные для подключения к базе данных из файла "secret.py" и SSL-сертификат, служащий для шифрованного соединения. При создании объекта класса генерируется клиент для обращения к базе данных и вместе с этим инициализируются вложенные классы, нужные для обращения к конкретной таблице.

```python
from ClientWrapper import DB
db = DB()
```

Методы подклассов:

Класс DB имеет 3 вложенных подкласса ("users_info", "urls_info", "visitors_info"), которые имеют одинаковую структуру и методы.

Для работы с конкретной таблицей обращаемся к методам вложенных классов "users_info", "urls_info", "visitors_info" по слежующим методам:
- create() - Создаёт таблицу выбронного подкласса, если таблицы не существует
- drop() - Удаляет таблицу выбронного подкласса, если таблица существует
- clear() - Очищает все данные полей таблицы выбранного подкласса, если таблица существует
- print(output="console") - Печатает данные таблицы на экран построчно в виде массива из значений ряда,
  можно задать необязательные параметр output на имя/путь файла (с указанием расширения), в который будут ДОПИСАНЫ значения полей таблицы
- append_from_file(file_name) - ДОПИСЫВАЕТ информацию в таблицу из указанного файла с зданным именем/путём (с указанием расширения)
  

```python
# Примеры методов для работы с таблицей users_info

db.users_info.create()
db.users_info.drop()
db.users_info.clear()

db.users_info.print()
db.users_info.print("file_name.csv")
db.users_info.append_from_file("db_test_files/users_info.csv")
```

Пояснение (правила работы с файлами):
1) Строчки таблицы разделены переносом строки ('\n')
2) Значения в полях строчки разделены ';'
3) Указанны все поля в верном порядке, без лишних знаков
4) В одном файле может нахдится записи только одной таблицы
5) Файл сохранён текстовом формате
6) При загрузке данных их корректность, полнота и ункальность проверяется только ограничаниями типов, заданных в столбцах таблицы

Методы класса DB:
- get(column, by) - Получить информацию из колонки под именем переданной перменной класса "column", связанную с информацией из колонки, переданную под именем метода класса "by" с указанием значения
- delete(by) - Удалить информацию из таблицы, по указанному значению, переданного методу класса "by" с указанием значения
- create_new_user(ip="0.0.0.0", username="", password="") - Добавляет информацию о новом пользователе в таблицу "users_info". Если пользователь не зарегестрировался на сайте, а просто хочет создать ссылку, то для его добавления можно указывать только поле "ip", если пользователь зарегестрировался нужно указать "ip", "username", "password". (ВОЗВРАЩАЕТ: None если пользователь под таким ником уже зарегестрирован, user_id если запись успешно добавлена)
- create_new_url(owner_id, short_url="", url="") - Добавляет инфомрацию о скоращённой ссылке в таблицу "urls_info". Если 
- create_visitor_note(resource_id, visitor_ip="0.0.0.0", country="", city=""):
  
Пояснение 1 (классы By и Column):

1) Классы by и column созданы для хранения определённых значений и зависимостей, отличающихся при выборе разных колонок базы данных.
2) База данных не имеет повторяющихся названий столбцов в таблицах, что позволяет не указывать названия таблиц из которых следует искать переданные столбцы, а составлять запросы и искать зависимости, работая только с названиями столбцов.
3) При указании класса "Column" нужно указать через '.' только название столбца, при указании класса "By" нужно указать через '.' название столбца и параметр-фильтр, по которому будет искаться инфомрация в скобочках ( пример By.USERNAME("useruser2310") ).
  Доступные обращения:
- USER_ID, IP, USERNAME, PASSWORD, REGISTRATION_DATE - таблица "users_info"
- URL_ID, OWNER_ID, SHORT_URL, URL, DATA_COLLECTION, CREATION_DATE - таблица "urls_info"
- NOTE_ID, RESOURCE_ID,VISITOR_IP, VISIT_DATE, COUNTRY, CITY - таблица "visitors_info"

Пояснение 2 (автоматическое удаление данных):

1) Незарегестрированный пользователь может создавать укороченные ссылки, но информация о переходах по ним не будет сохраняться в базу данных, и пользователь не будет иметь доступа к просмотру (колонка "data collection" - показатель доступа к таблице "visitors_info"). По истечению срока 30 дней (со дня создания записи в таблицы отдельно взятого пользовтеля) информация о пользователе в таблице "users_info" и его ссылки в таблице "urls_info" по независимому друг от друга сроку будет удалена базой данных автоматически.
2) Зарегестрированный пользователь может создавать укороченные ссылки, и ифнормация о его аккаунте в таблице "users_info" никогда не будет удалена автоматически. Также пользователь будет иметь доступ на просмотр статистики переходов по ссылке, информация о которой будет сохраняться в таблицу "urls_info".
3) Информация о переходах по ссылке в таблице "visitors_info" независимо от типа аккаунта будет автоматически удалятся спустя 30 дней (каждая отдельная запись имеет свой срок, независимый от других)

*Пояснение 3 (ручное удаление данных):

Каждая следующая таблица зависит от записей предыдущих (users_info -> urls_info -> visitors_info), поэтому если удалить данные в более близкой к началу иерархии таблице, то все следующие таблицы и их записи, связанные с этой инофрмацией, тоже будут удалены (пример: если удалить информацию по "short_url", то удаляются все связанные с этим параметром строки таблиц "urls_info" и "visitors_info" .
```python
# Создание записи пользователя без авторизации:
id = db.create_new_user(ip="143.122.100.250")
url_id1 = db.create_new_url(id, "https://shrot_url", "https://user_long_long_long_long_long_url") # с сохранениум url_id
db.create_new_url(id, "https://shrot_url", "https://user_long_long_long_long_long_url") # без сохранения url_id
db.
db.get(Column.USERNAME, By.COUNTRY("China"))
db.delete(By.URL(""))
db.delete(By.URL(""))
db.delete(By.URL(""))

user_id = db.create_new_user("198.203.021.122") # регистрация пользователя без 
user_id = db.create_new_user()

db.users_info.print()
db.users_info.print("file_name.csv")
db.users_info.append_from_file("db_test_files/users_info.csv")
```


