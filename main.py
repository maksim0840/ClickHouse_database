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
	if (username == "non-registered" or password == "non-registered"):
		client.execute('''
			INSERT INTO users_info (* EXCEPT(username, password)) 
			Values (generateUUIDv4(), '{0}', now64(3, 'Europe/Moscow'))
		'''.format(ip))
	else:
		client.execute('''
			INSERT INTO users_info (*) 
			Values (generateUUIDv4(), '{0}', '{1}', '{2}', now64(3, 'Europe/Moscow'))
		'''.format(ip, username, password))


create_new_user('100.253.40.133', 'стёпа', 'стёпа1015')


# client.execute('''DROP TABLE users_info''')
# res = client.execute('''
# 	CREATE TABLE users_info 
# 	(
# 		user_id UUID NOT NULL,
# 		ip IPv4,
# 		username String,
# 		password String,
# 		registration_date DateTime64(3, 'Europe/Moscow') NOT NULL
# 	)
# 	ENGINE = MergeTree()
# 	PRIMARY KEY (user_id, username)
# 	''')
# print(res)

# def 
