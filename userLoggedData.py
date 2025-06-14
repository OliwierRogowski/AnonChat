class User:
    def __init__(self, username, isAdmin, user_id):
        self.username = username
        self.isAdmin = True if isAdmin == "admin" else False
        self.user_id = user_id