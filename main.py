from ClientWrapper import *

db = DB()

# db.users_info.print(rows=2)
# db.urls_info.print(rows=2)
# db.visitors_info.print(rows=2)

#db.users_info.clear()
db.users_info.append_from_file("db_test_files/users_info.csv")
