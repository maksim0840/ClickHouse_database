from clickhouse_driver import Client
from secret import client_host, client_user, client_password

client = Client(host=client_host,
                user=client_user,
                password=client_password,
                port=9440,
                secure=True,
                verify=True,
                ca_certs='/usr/local/share/ca-certificates/Yandex/RootCA.crt')


def create_new_user(ip, username="non-registered", password="non-registered"):
	# генерация нового UUID (Universally Unique Identifier)
	user_id = client.execute('''
		SELECT generateUUIDv4()
		''')[0][0]

	if ((username == "non-registered" or password == "non-registered")\):
		client.execute('''
			INSERT INTO users_info (* EXCEPT(username, password)) 
			Values ('{0}', '{1}', now64(3, 'Europe/Moscow'))
			'''.format(user_id, ip))
	else:
		if (user_id_by_username(username) != None):
			return None # пользователь с таким ником уже зарегестрирован

		client.execute('''
			INSERT INTO users_info (*) 
			Values ('{0}', '{1}', '{2}', '{3}', now64(3, 'Europe/Moscow'))
			'''.format(user_id, ip, username, password))
	return user_id

def log_in_confirmation(username, password):
	user_id = client.execute('''
		SELECT user_id FROM users_info
		WHERE (username = '{0}') AND (password = '{1}')
		'''.format(username, password))

	if (len(user_id) != 0):
		return user_id[0][0]
	return None

def user_id_by_username(username):
	user_id = client.execute('''
		SELECT user_id FROM users_info
		WHERE (username = '{0}')
		'''.format(username))

	if (len(user_id) != 0):
		return user_id[0][0]
	return None

print(create_new_user('100.253.40.133'))
#print(create_new_user('100.253.40.133', 'bob2', 'random1222321'))
# print(create_new_user('100.253.40.133', 'asd', 'ads'))
# print(create_new_user('100.253.40.212'))
#print(log_in_confirmation("стёпа", "стёпа1015"))


# client.execute('''DROP TABLE users_info''')
# res = client.execute('''
# 	CREATE TABLE users_info 
# 	(
# 		user_id UUID,
# 		ip IPv4,
# 		username String,
# 		password String,
# 		registration_date DateTime64(3, 'Europe/Moscow')
# 	)
# 	ENGINE = MergeTree()
# 	PRIMARY KEY (user_id, username)

# 	TTL toDateTime(registration_date) + INTERVAL 1 MONTH DELETE 
# 	WHERE (empty(username) AND empty(password))
# 	''')
# print(res)
