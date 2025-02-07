
import json
import logging
import sys

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --------------------------
# ПАРАМЕТРЫ ДЛЯ ПРИМЕРА
# --------------------------
# URL вашего сервера Syrve.
IIKO_HOST = ""

# Учетные данные (логин/пароль, где пароль - SHA1 hash)
LOGIN = ""
PASSWORD_SHA1 = ""

# Параметры запроса техкарт
DATE_FROM = "2024-12-01"  # Начальный учетный день
DATE_TO = "2025-01-29"    # Конечный учетный день
INCLUDE_DELETED_PRODUCTS = True
INCLUDE_PREPARED_CHARTS = True  # Устанавливаем True, чтобы сервер вернул "preparedCharts".


# --------------------------
# ФУНКЦИИ ЛОГИНА И ЛОГАУТА
# --------------------------
def login(session: requests.Session) -> str:
    """
    Авторизация на сервере:
      - отправляем POST на /resto/api/auth
      - получаем токен (строка в теле ответа)
      - Сервер >=4.3 может автоматически добавлять cookie key
    Возвращаем сам токен (на всякий случай).
    """
    auth_url = f"{IIKO_HOST}/resto/api/auth"
    payload = {"login": LOGIN, "pass": PASSWORD_SHA1}

    try:
        response = session.post(auth_url, data=payload, timeout=10)
        response.raise_for_status()

        token = response.text.strip()  # Токен в ответе — просто строка
        logging.info(f"Успешная авторизация. Получен токен: {token}")
        return token
    except requests.exceptions.RequestException as exc:
        logging.error("Ошибка при авторизации: %s", exc)
        sys.exit(1)


def logout(session: requests.Session, token: str):
    """
    Разлогиниваемся, чтобы освободить занятую лицензию.
    """
    logout_url = f"{IIKO_HOST}/resto/api/logout"
    payload = {"key": token}

    try:
        response = session.post(logout_url, data=payload, timeout=10)
        if response.status_code == 200:
            logging.info("Успешный logout. Лицензия освобождена.")
        else:
            logging.warning(f"Logout вернул статус {response.status_code}.")
    except requests.exceptions.RequestException as exc:
        logging.warning("Ошибка при logout: %s", exc)


# --------------------------
# ФУНКЦИИ ПОЛУЧЕНИЯ ТЕХКАРТ
# --------------------------
def get_all_assembly_charts(session: requests.Session, token: str):
    """
    Пример запроса к эндпоинту /resto/api/v2/assemblyCharts/getAll,
    чтобы получить полный список техкарт за заданный период.
    """
    url = f"{IIKO_HOST}/resto/api/v2/assemblyCharts/getAll"
    params = {
        "dateFrom": DATE_FROM,
        "dateTo": DATE_TO,
        "includeDeletedProducts": str(INCLUDE_DELETED_PRODUCTS).lower(),   # true/false
        "includePreparedCharts": str(INCLUDE_PREPARED_CHARTS).lower()
        # Если нужно явно передать ключ в URL (на старых версиях):
        # "key": token
    }

    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        logging.info("Технологические карты (getAll) получены успешно.")
        return data
    except requests.exceptions.RequestException as exc:
        logging.error("Ошибка при получении техкарт: %s", exc)
        sys.exit(1)


# ----------------------------
# ФУНКЦИИ ДЛЯ КРАСИВОГО ВЫВОДА
# ----------------------------
def pretty_print_assembly_charts(assembly_charts: list):
    """
    КЛЯСИВА печатает список технологических карт (AssemblyChartDto).
    """
    if not assembly_charts:
        print("Нет данных по исходным техкартам (assemblyCharts).")
        return

    print(f"Всего исходных техкарт: {len(assembly_charts)}")
    for i, chart in enumerate(assembly_charts, start=1):
        print(f"\n--- [Исходная техкарта] №{i} ---")
        print(f"UUID техкарты:             {chart.get('id')}")
        print(f"UUID продукта (блюда):     {chart.get('assembledProductId')}")
        print(f"Дата начала действия:      {chart.get('dateFrom')}")
        print(f"Дата окончания действия:   {chart.get('dateTo')}")
        print(f"Норма закладки блюда:      {chart.get('assembledAmount')}")
        print(f"Метод списания продукта:   {chart.get('productWriteoffStrategy')}")
        print(f"Стратегия размеров блюда:  {chart.get('productSizeAssemblyStrategy')}")

        items = chart.get('items', [])
        print(f"Количество ингредиентов: {len(items)}")
        for idx, item in enumerate(items, start=1):
            print(f"  [{idx}] Ингредиент UUID={item.get('productId')}")
            print(f"       Брутто:  {item.get('amountIn')}")
            print(f"       Нетто:   {item.get('amountMiddle')}")
            print(f"       Выход:   {item.get('amountOut')}")

        tech_desc = chart.get('technologyDescription', '')
        if tech_desc:
            print(f"Технология приготовления: {tech_desc}")

        description = chart.get('description', '')
        if description:
            print(f"Описание:                {description}")

        # ... по желанию можно пойти нахуй и добавить appearance, organoleptic, и т.п.


def pretty_print_prepared_charts(prepared_charts: list):
    """
    КЛАСИВА печатает список "разложенных" техкарт (PreparedChartDto).
    """
    if not prepared_charts:
        print("Нет данных по разложенным техкартам (preparedCharts).")
        return

    print(f"Всего разложенных техкарт: {len(prepared_charts)}")
    for i, chart in enumerate(prepared_charts, start=1):
        print(f"\n--- [Разложенная техкарта] №{i} ---")
        print(f"UUID техкарты:             {chart.get('id')}")
        print(f"UUID продукта (блюда):     {chart.get('assembledProductId')}")
        print(f"Дата начала действия:      {chart.get('dateFrom')}")
        print(f"Дата окончания действия:   {chart.get('dateTo')}")
        print(f"Стратегия размеров блюда:  {chart.get('productSizeAssemblyStrategy')}")

        items = chart.get('items', [])
        print(f"Количество конечных ингредиентов: {len(items)}")
        for idx, item in enumerate(items, start=1):
            print(f"  [{idx}] Ингредиент UUID={item.get('productId')}")
            print(f"       Количество (amount): {item.get('amount')}")

        # Тут также можно пойти нахуй и допечатать прочие поля при желании


# --------------------------
# ОСНОВНОЙ БЛОК СКРИПТА
# --------------------------
def main():
    with requests.Session() as session:
        # Если сертификат самоподписанный, можно отключить проверку:
        # session.verify = False

        token = login(session)

        # Получаем все техкарты (assembly + prepared)
        charts_data = get_all_assembly_charts(session, token)

        # 1) Печатаем полный JSON КЛАСИВА
        print("=== Полный JSON-ответ (pretty) ===")
        print(json.dumps(charts_data, indent=2, ensure_ascii=False))

        # 2) Отдельно выводим поля assemblyCharts
        print("\n=== Исходные техкарты (Assembly) ===")
        assembly_charts = charts_data.get("assemblyCharts")
        pretty_print_assembly_charts(assembly_charts)

        # 3) Отдельно выводим поля preparedCharts
        print("\n=== Разложенные техкарты (Prepared) ===")
        prepared_charts = charts_data.get("preparedCharts")
        pretty_print_prepared_charts(prepared_charts)

        # Освобождаем лицензию
        logout(session, token)


if __name__ == "__main__":
    main()
