import keyring

SERVICE = "anonChatSecure"

def save_password(user, password):
    keyring.set_password('anonChatSecure', user, password)

def load_password(user):
    return keyring.get_password('anonChatSecure', user)
