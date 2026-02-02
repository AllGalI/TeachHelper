import hashlib


def get_email_hash(email: str) -> str:
    """
    Хэширует email адрес для безопасного хранения в базе данных.
    Используется для отслеживания подписок по email, даже если пользователь удалил аккаунт.
    
    Args:
        email: Email адрес для хэширования
        
    Returns:
        SHA256 хэш email в виде hex строки
    """
    # Приводим email к нижнему регистру для консистентности
    email_normalized = email.lower().strip()
    # Создаём SHA256 хэш
    hash_object = hashlib.sha256(email_normalized.encode('utf-8'))
    return hash_object.hexdigest()
