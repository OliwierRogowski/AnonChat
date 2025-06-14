import bcrypt

password = "Admin"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode())  # To wrzucasz do bazy