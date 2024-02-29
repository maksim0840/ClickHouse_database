from containers import column, by
from secret import client_host, client_user, client_password
import clickhouse_driver
import datetime

class DB:
	''' Позволяет управлять базой данных и делать к ней запросы '''

	def __init__(self):
		# Клиент для отправки запросов
		self.__client = self.__get_db_client(client_host, client_user, client_password)
		self.__functions = [self.__drop, self.__clear, self.__print, self.__append_from_file]
		# Создание экземлпяров классов (доступные таблицы в базе данных)
		self.users_info = self.UsersInfo("users_info", self.__client, self.__functions)
		self.urls_info = self.UrlsInfo("urls_info", self.__client, self.__functions)
		self.visitors_info = self.VisitorsInfo("visitors_info", self.__client, self.__functions)


	''' PRIVAT МЕТОДЫ '''


	# Создаёт клиент для отправки запросов базе данных
	def __get_db_client(self, db_host, db_user, db_password):
		client = clickhouse_driver.Client(
			host=db_host,
            user=db_user,
            password=db_password,
            port=9440,
            secure=True,
            verify=True,
            ca_certs='/usr/local/share/ca-certificates/Yandex/RootCA.crt')
		return client

	# Генерация нового UUID (Universally Unique Identifier)
	def __generateUUID(self):
		uuid = self.__client.execute("""
			SELECT generateUUIDv4()
			""")[0][0]
		return uuid

		# Удалить таблицу, если она существует
	def __drop(self, table_name):
		self.__client.execute("""
			DROP TABLE IF EXISTS {0}
			""".format(table_name))

	# Удаляет все данные с таблицы, если она существует
	def __clear(self, table_name):
		self.__client.execute("""
			TRUNCATE TABLE IF EXISTS {0}
			""".format(table_name))

	def __print(self, table_name, output = "console"):
		data = self.__client.execute("""
			SELECT * FROM {0}
			""".format(table_name))
		for i in range(len(data)):
			data[i] = list(map(str, data[i]))

		if (output == "console"):
			for row in data:
				print(row)
		else:
			with open(output, 'a') as file:
				for row in data:
					file.write(';'.join(row) + '\n')

	# Добавить в таблицу данные из файла
	def __append_from_file(self, table_name, file_name, input_format):
		with open(file_name, 'r') as file:
			data = file.read().split('\n')
			if (data[-1] == ''):
				data = data[:-1]

			for row in data:
				row = row.split(';')
				self.__client.execute("""
					INSERT INTO {0} (*)
					Values {1}
					""".format(table_name, input_format.format(*row)))


	''' PUBLIC МЕТОДЫ '''


	# Получить информацию из таблицы по заданному значению
	def get(self, column, by):
		target_column, target_table, target_primary, target_connect = column
		key_value, key_column, key_table, key_primary, key_connect = by
		# Запрос несвязанных таблиц
		if ({target_table, key_table} == {"users_info", "visitors_info"}):
			mid_table = "urls_info" # промежуточный путь
			request = f"""
				SELECT {target_column} FROM {target_table} WHERE {target_primary} IN
				(SELECT {target_connect} FROM {mid_table} WHERE {key_connect} IN
				(SELECT {key_primary} FROM {key_table} WHERE {key_column}='{key_value}'))
				"""
		# Запрос одной таблицы
		elif (target_table == key_table):
			request = f"""
				SELECT {target_column} FROM {target_table} WHERE {key_column}='{key_value}'
				"""
		# Запрос связанных таблиц
		else:
			request = f"""
				SELECT {target_column} FROM {target_table} WHERE {target_primary} IN
				(SELECT {target_connect} FROM {key_table} WHERE {key_column}='{key_value}')
				"""
		return self.__client.execute(request)

	def delete(self, by):
		key_value, key_column, key_table, key_primary, key_connect = by

		if (key_table == "users_info"):
			self.__client.execute("""
				ALTER TABLE visitors_info DELETE WHERE resource_id IN
				(SELECT url_id FROM urls_info WHERE owner_id IN
				(SELECT user_id FROM users_info WHERE {0}='{1}'))
				""".format(key_column, key_value))
			self.__client.execute("""
				ALTER TABLE urls_info DELETE WHERE owner_id IN
				(SELECT user_id FROM users_info WHERE {0}='{1}')
				""".format(key_column, key_value))
		elif (key_table == "urls_info"):
			self.__client.execute("""
				ALTER TABLE visitors_info DELETE WHERE resource_id IN
				(SELECT url_id FROM urls_info WHERE {0}='{1}')
				""".format(key_column, key_value))

		self.__client.execute("""
			ALTER TABLE {0} DELETE WHERE {1}='{2}'
			""".format(key_table, key_column, key_value))

	# Создание новой записи о пользователе
	def create_new_user(self, ip="0.0.0.0", username="", password=""):
		user_id = self.__generateUUID()

		if ((username == "" or password == "")):
			self.__client.execute("""
				INSERT INTO users_info (* EXCEPT(username, password)) 
				Values ('{0}', '{1}', now64(3, 'Europe/Moscow'))
				""".format(user_id, ip))
		else:
			# Зарегестрирован ли уже пользователь с таким username (проверка СУЩЕСТВОВАНИЕ поля)
			if (self.get(column.USER_ID, by.USERNAME(username)) != []):
				return None # username занят другим пользователем

			self.__client.execute("""
				INSERT INTO users_info (*) 
				Values ('{0}', '{1}', '{2}', '{3}', now64(3, 'Europe/Moscow'))
				""".format(user_id, ip, username, password))
		return user_id

	# Добавить информацию о новой ссылке
	def create_new_url(self, owner_id, short_url="", url=""):
		# Существует ли пользователь (проверка СУЩЕСТВОВАНИЯ поля)
		if (self.get(column.USER_ID, by.OWNER_ID(owner_id)) == []):
			return None # пользователя с таким id не существует

		link_id = self.__generateUUID()
		# Индикатор, зарегестрирован пользователь на сайте или нет (проверка на ПУСТОТУ поля)
		data_collection = (self.get(column.USERNAME, by.USER_ID(owner_id)) != [('',)])

		self.__client.execute("""
				INSERT INTO urls_info (*) 
				Values ('{0}', '{1}', '{2}', '{3}', '{4}', now64(3, 'Europe/Moscow'))
				""".format(link_id, owner_id, short_url, url, data_collection))
		return link_id

	# Добавить информафию о переходе на ссылку
	def create_visitor_note(self, resource_id, visitor_ip="0.0.0.0", country="", city=""):
		# Существует ли ссылка (проверка СУЩЕСТВОВАНИЯ полей и СООТВЕТСТВИЯ требованиям)
		if ((self.get(column.URL_ID, by.URL_ID(resource_id)) == []) or
			(self.get(column.DATA_COLLECTION, by.URL_ID(resource_id)) == [(False,)])):
			return None # ссылки с таким id не существует или аккаунт не зарегестрирован для статистики
		
		note_id = self.__generateUUID()

		self.__client.execute("""
				INSERT INTO visitors_info (*) 
				Values ('{0}', '{1}', '{2}', now64(3, 'Europe/Moscow'), '{3}', '{4}')
				""".format(note_id, resource_id, visitor_ip, country, city))
		return note_id


	'''ВЛОЖЕННЫЕ КЛАССЫ'''	
	

	class UsersInfo:
		''' Класс для работы с таблицей "users_info" '''
		def __init__(self, table_name, client, functions):
			self.__table = table_name
			self.__client = client
			# Передача функций во вложенный класс
			self.__drop_function = functions[0]
			self.__clear_function = functions[1]
			self.__print_function = functions[2]
			self.__append_from_file_function = functions[3]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console"):
			if (output == "console"):
				self.__print_function(self.__table)
			else:
				self.__print_function(self.__table, output)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', '{3}', parseDateTimeBestEffortOrNull('{4}'))"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Создание таблицы
		def create(self):
			self.__client.execute("""
				CREATE TABLE IF NOT EXISTS {0} 
				(
					user_id UUID,
					ip IPv4,
					username String,
					password String,
					registration_date DateTime64(3, 'Europe/Moscow')
				)
				ENGINE = MergeTree()
				PRIMARY KEY (user_id, username)

				TTL toDateTime(registration_date) + INTERVAL 1 MONTH DELETE 
				WHERE (empty(username) AND empty(password))
				""".format(self.__table))

	class UrlsInfo:
		''' Класс для работы с таблицей "users_info" '''
		def __init__(self, table_name, client, functions):
			self.__table = table_name
			self.__client = client
			# Передача функция во вложенный класс
			self.__drop_function = functions[0]
			self.__clear_function = functions[1]
			self.__print_function = functions[2]
			self.__append_from_file_function = functions[3]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console"):
			if (output == "console"):
				self.__print_function(self.__table)
			else:
				self.__print_function(self.__table, output)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', '{3}', '{4}', parseDateTimeBestEffortOrNull('{5}'))"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Создание таблицы
		def create(self):
			self.__client.execute("""
				CREATE TABLE IF NOT EXISTS {0} 
				(
					url_id UUID,
			 		owner_id UUID,
			 		short_url String,
			 		url String,
			 		data_collection Bool,
			 		creation_date DateTime64(3, 'Europe/Moscow')
				)
				ENGINE = MergeTree()
				PRIMARY KEY (url_id, owner_id, short_url, url)

				TTL toDateTime(creation_date) + INTERVAL 1 MONTH DELETE
				WHERE (data_collection = False)
					""".format(self.__table))

	class VisitorsInfo:
		''' Класс для работы с таблицей "visitors_info" '''
		def __init__(self, table_name, client, functions):
			self.__table = table_name
			self.__client = client
			self.__drop_function = functions[0]
			self.__clear_function = functions[1]
			self.__print_function = functions[2]
			self.__append_from_file_function = functions[3]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console"):
			if (output == "console"):
				self.__print_function(self.__table)
			else:
				self.__print_function(self.__table, output)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', parseDateTimeBestEffortOrNull('{3}'), '{4}', '{5}')"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Создание таблицы
		def create(self):
			self.__client.execute("""
				CREATE TABLE IF NOT EXISTS {0} 
				(	
					note_id UUID,
					resource_id UUID,
					visitor_ip IPv4,
					visit_date DateTime64(3, 'Europe/Moscow'),
					country String,
					city String
				)
				ENGINE = MergeTree()
				PRIMARY KEY (note_id, resource_id, visitor_ip)

				TTL toDateTime(visit_date) + INTERVAL 1 MONTH DELETE 
				""".format(self.__table))

db = DB()
# db.users_info.clear()
# db.urls_info.clear()
# db.visitors_info.clear()
# db.users_info.append_from_file("db_test_files/users_info.csv")
# db.urls_info.append_from_file("db_test_files/urls_info.csv")
# db.visitors_info.append_from_file("db_test_files/visitors_info.csv")
db.delete(by.USER_ID("6dbf4440-2394-486d-b6fe-fc931ce83657"))

#print(db.create_visitor_note("410bef63-35ed-4bd0-9f73-2c757f9a7da0"))
#db.get(column.USER_ID, by.USERNAME("kukaracha"))
#print(column.USER_ID, by.USERNAME("kukaracha"))
# db.users_info.get(column.USER_ID, by.USERNAME("kukaracha"))
# print(By.USERNAME("kukaracha"))

# db.users_info.create()
# db.users_info.drop()
# db.urls_info.create()
# db.urls_info.drop()
# db.visitors_info.create()
# db.visitors_info.drop()