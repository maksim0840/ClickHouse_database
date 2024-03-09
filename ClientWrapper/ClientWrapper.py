from .containers import Column, By
from .secret import client_host, client_user, client_password, client_ca_certs
import clickhouse_driver

class DB:
	''' Позволяет управлять базой данных и делать к ней запросы '''

	def __init__(self):
		# Клиент для отправки запросов
		self.__client = self.__get_db_client(client_host, client_user, client_password, client_ca_certs)
		# Создание экземлпяров классов (доступные таблицы в базе данных)
		self.__functions = [self.__drop, self.__clear, self.__print, self.__append_from_file, self.get]
		self.users_info = self.UsersInfo("users_info", self.__client, self.__functions)
		self.urls_info = self.UrlsInfo("urls_info", self.__client, self.__functions)
		self.visitors_info = self.VisitorsInfo("visitors_info", self.__client, self.__functions)


	''' PRIVAT МЕТОДЫ '''


	# Создаёт клиент для отправки запросов базе данных
	def __get_db_client(self, db_host, db_user, db_password, db_ca_certs):
		client = clickhouse_driver.Client(
			host=db_host,
            user=db_user,
            password=db_password,
            port=9440,
            secure=True,
            verify=True,
            ca_certs=db_ca_certs)
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

	# Вывод инофрмации из таблицы
	def __print(self, table_name, output="console", rows=-1):
		data = self.__client.execute("""
			SELECT * FROM {0}
			""".format(table_name))
		if (rows > -1):
			rows = min(rows, len(data))
		else:
			rows = len(data)
		output = str(output)

		for i in range(rows):
			data[i] = list(map(str, data[i]))

		if (output == "console"): # вывод в консоль
			for i in range(rows):
				print(data[i])
		elif (output == "variable"): # вывод в переменную
			return data
		else: # вывод в файл
			with open(output, 'a') as file:
				for i in range(rows):
					file.write(';'.join(data[i]) + '\n')

	# Добавить в таблицу данные из файлав
	def __append_from_file(self, table_name, file_name, input_format):
		with open(file_name, 'r') as file:
			data = file.read().split('\n')
			if (data[-1] == ''):
				data = data[:-1]

			request = ""
			for row in data:
				row = row.split(';')
				request += "{0},".format(input_format.format(*row))

			self.__client.execute("""
					INSERT INTO {0} (*)
					Values {1}
					""".format(table_name, request))

			
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
				SELECT {target_column} FROM {target_table} WHERE {key_connect} IN
				(SELECT {key_primary} FROM {key_table} WHERE {key_column}='{key_value}')
				"""

		response = self.__client.execute(request)
		response = list(map(list, response))
		return response

	# Удаление информации из таблицы
	def delete(self, by):
		key_value, key_column, key_table, key_primary, key_connect = by

		if (key_table == "users_info"): # удаление из двух последних таблиц
			self.__client.execute("""
				ALTER TABLE visitors_info DELETE WHERE resource_id IN
				(SELECT url_id FROM urls_info WHERE owner_id IN
				(SELECT user_id FROM users_info WHERE {0}='{1}'))
				""".format(key_column, key_value))
			self.__client.execute("""
				ALTER TABLE urls_info DELETE WHERE owner_id IN
				(SELECT user_id FROM users_info WHERE {0}='{1}')
				""".format(key_column, key_value))
		elif (key_table == "urls_info"): # удаление из последней таблицы
			self.__client.execute("""
				ALTER TABLE visitors_info DELETE WHERE resource_id IN
				(SELECT url_id FROM urls_info WHERE {0}='{1}')
				""".format(key_column, key_value))

		# Удаление из переданной таблицы
		self.__client.execute("""
			ALTER TABLE {0} DELETE WHERE {1}='{2}'
			""".format(key_table, key_column, key_value))

	# Проверить авторизацию пользователя
	def check_auth(self, username, password):
		password_from_db = self.get(Column.PASSWORD, By.USERNAME(username))
		if (password_from_db == []):
			return None # пользователя с таким ником не существует
		elif (password_from_db[0][0] != password):
			return False # пароль неверный
		return True # пароль верный


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
			if (self.get(Column.USER_ID, By.USERNAME(username)) != []):
				return None # username занят другим пользователем

			self.__client.execute("""
				INSERT INTO users_info (*) 
				Values ('{0}', '{1}', '{2}', '{3}', now64(3, 'Europe/Moscow'))
				""".format(user_id, ip, username, password))
		return user_id

	# Добавить информацию о новой ссылке
	def create_new_url(self, owner_id, short_url="", url=""):
		# Существует ли пользователь (проверка СУЩЕСТВОВАНИЯ поля)
		if (self.get(Column.USER_ID, By.USER_ID(owner_id)) == []):
			return None # пользователя с таким id не существует

		url_id = self.__generateUUID()
		# Индикатор, зарегестрирован пользователь на сайте или нет (проверка на ПУСТОТУ поля)
		data_collection = (self.get(Column.USERNAME, By.USER_ID(owner_id)) != [[""]])

		self.__client.execute("""
				INSERT INTO urls_info (*) 
				Values ('{0}', '{1}', '{2}', '{3}', '{4}', now64(3, 'Europe/Moscow'))
				""".format(url_id, owner_id, short_url, url, data_collection))
		return url_id

	# Добавить информафию о переходе по ссылке
	def create_visitor_note(self, resource_id, visitor_ip="0.0.0.0", country="", city=""):
		# Существует ли ссылка (проверка СУЩЕСТВОВАНИЯ полей и СООТВЕТСТВИЯ требованиям)
		if ((self.get(Column.URL_ID, By.URL_ID(resource_id)) == []) or
			(self.get(Column.DATA_COLLECTION, By.URL_ID(resource_id)) == [[False]])):
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
			self.__get_function = functions[4]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console", rows=-1):
			return self.__print_function(self.__table, output, rows)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', '{3}', parseDateTimeBestEffortOrNull('{4}'))"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Вывести все столбцы таблицы по параметру by	
		def get_all(self, by):
			column = Column.USER_ID
			column[0] = "*"
			return self.__get_function(column, by)

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
			self.__get_function = functions[4]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console", rows=-1):
			return self.__print_function(self.__table, output, rows)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', '{3}', '{4}', parseDateTimeBestEffortOrNull('{5}'))"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Вывести все столбцы таблицы по параметру by	
		def get_all(self, by):
			column = Column.URL_ID
			column[0] = "*"
			return self.__get_function(column, by)

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
			self.__get_function = functions[4]

		# Переданная функция, удалаяющая таблицу, если она существует
		def drop(self):
			self.__drop_function(self.__table)

		# Переданная функция, удающая данные из таблицы, если она существует
		def clear(self):
			self.__clear_function(self.__table)

		# Переданная функция, выводящая информацию из таблицы на экран или в файл
		def print(self, output="console", rows=-1):
			return self.__print_function(self.__table, output, rows)

		# Переданная функция, записывающая информацию в таблицу из файла
		def append_from_file(self, file_name):
			input_format = "('{0}', '{1}', '{2}', parseDateTimeBestEffortOrNull('{3}'), '{4}', '{5}')"
			self.__append_from_file_function(self.__table, file_name, input_format)

		# Вывести все столбцы таблицы по параметру by	
		def get_all(self, by):
			column = Column.NOTE_ID
			column[0] = "*"
			return self.__get_function(column, by)

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