
class column:
	"""
	синтаксис: [название колонки, название таблицы, 
				название ключа связанного со второй таблицей (первичный поисковый), 
 			  	название колонки во второй таблице с которым этот ключ связан]
	"""	
	__USERS_INFO_DIFFERENCES = ["users_info", "user_id", "owner_id"]
	__URLS_INFO_DIFFERENCES = ["urls_info", "url_id", "url_id"]
	__VISITORS_INFO_DIFFERENCES = ["visitors_info", "resource_id", "url_id"]

	USER_ID = ["user_id"] + __USERS_INFO_DIFFERENCES
	IP = ["ip"] + __USERS_INFO_DIFFERENCES
	USERNAME = ["username"] + __USERS_INFO_DIFFERENCES
	PASSWORD = ["password"] + __USERS_INFO_DIFFERENCES
	REGISTRATION_DATE = ["registration_date"] + __USERS_INFO_DIFFERENCES

	URL_ID = ["url_id"] + __URLS_INFO_DIFFERENCES
	OWNER_ID = ["owner_id"] + __URLS_INFO_DIFFERENCES
	SHORT_URL = ["short_url"] + __URLS_INFO_DIFFERENCES
	URL = ["url"] + __URLS_INFO_DIFFERENCES
	DATA_COLLECTION = ["data_collection"] + __URLS_INFO_DIFFERENCES
	CREATION_DATE = ["creation_date"] + __URLS_INFO_DIFFERENCES

	NOTE_ID = ["note_id"] + __VISITORS_INFO_DIFFERENCES
	RESOURCE_ID = ["resource_id"] + __VISITORS_INFO_DIFFERENCES
	VISITOR_IP = ["visitor_ip"] + __VISITORS_INFO_DIFFERENCES
	VISIT_DATE = ["visit_date"] + __VISITORS_INFO_DIFFERENCES
	COUNTRY = ["country"] + __VISITORS_INFO_DIFFERENCES
	CITY = ["city"] + __VISITORS_INFO_DIFFERENCES


class by:
	# синтаксис: [значения для поиска, .....поля класса column.....]

	def USER_ID(value): return [value] + column.USER_ID
	def IP(value): return [value] + column.IP
	def USERNAME(value): return [value] + column.USERNAME
	def PASSWORD(value): return [value] + column.PASSWORD
	def REGISTRATION_DATE(value): return [value] + column.REGISTRATION_DATE

	def URL_ID(value): return [value] + column.URL_ID
	def OWNER_ID(value): return [value] + column.OWNER_ID
	def SHORT_URL(value): return [value] + column.SHORT_URL
	def URL(value): return [value] + column.URL
	def DATA_COLLECTION(value): return [value] + column.DATA_COLLECTION
	def CREATION_DATE(value): return [value] + column.CREATION_DATE

	def RESOURCE_ID(value): return [value] + column.RESOURCE_ID
	def VISITOR_IP(value): return [value] + column.VISITOR_IP
	def VISIT_DATE(value): return [value] + column.VISIT_DATE
	def COUNTRY(value): return [value] + column.COUNTRY
	def CITY(value): return [value] + column.CITY
