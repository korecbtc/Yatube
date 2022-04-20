from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    now = datetime.now()
    return {
        'year': int(now.strftime("%Y"))
    }
