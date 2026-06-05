import requests
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

# --- Задание 2: Получение данных из API ---
API_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 55.75,
    "longitude": 37.62,
    "daily": "temperature_2m_max,temperature_2m_min",
    "timezone": "Europe/Moscow",
    "past_days": 7
}


def fetch_weather_data():
    """Выполняет GET-запрос к API и возвращает распарсенный JSON."""
    response = requests.get(API_URL, params=PARAMS)
    response.raise_for_status()
    return response.json()


# --- Задание 3: Сохранение данных в SQLite ---
DB_NAME = "../weather.db"


def create_table():
    """Создает таблицу weather_log, если она не существует."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_log (
            date TEXT PRIMARY KEY,
            temp_max REAL,
            temp_min REAL
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(weather_data):
    """Сохраняет данные из JSON в таблицу weather_log."""
    dates = weather_data["daily"]["time"]
    temps_max = weather_data["daily"]["temperature_2m_max"]
    temps_min = weather_data["daily"]["temperature_2m_min"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for date, tmax, tmin in zip(dates, temps_max, temps_min):
        cursor.execute("""
            INSERT OR REPLACE INTO weather_log (date, temp_max, temp_min)
            VALUES (?, ?, ?)
        """, (date, tmax, tmin))

    conn.commit()
    conn.close()


# --- Задание 4: Расчет метрик ---
def calculate_metrics():
    """Вычисляет аналитические метрики на основе данных из БД."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Средние значения
    cursor.execute("SELECT AVG(temp_max), AVG(temp_min) FROM weather_log;")
    avg_max, avg_min = cursor.fetchone()

    # 2. Самый тёплый день
    cursor.execute("SELECT date, temp_max FROM weather_log ORDER BY temp_max DESC LIMIT 1;")
    warmest_date, warmest_temp = cursor.fetchone()

    # 3. Самый холодный день
    cursor.execute("SELECT date, temp_min FROM weather_log ORDER BY temp_min ASC LIMIT 1;")
    coldest_date, coldest_temp = cursor.fetchone()

    # 4. Размах температур
    cursor.execute("SELECT MAX(temp_max) - MIN(temp_min) FROM weather_log;")
    temp_range = cursor.fetchone()[0]

    conn.close()

    return {
        "avg_max": avg_max,
        "avg_min": avg_min,
        "warmest_day": {"date": warmest_date, "temp": warmest_temp},
        "coldest_day": {"date": coldest_date, "temp": coldest_temp},
        "temp_range": temp_range
    }


# --- Задание 5: Визуализация результатов ---
def visualize_data():
    """Строит и показывает график изменения температур."""

    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT date, temp_max, temp_min FROM weather_log ORDER BY date;
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    plt.figure(figsize=(10, 6))

    plt.plot(df['date'], df['temp_max'], marker='o', color='red', label='Макс. температура')
    plt.plot(df['date'], df['temp_min'], marker='o', color='blue', label='Мин. температура')

    plt.title('Прогноз погоды в Москве (макс/мин температура за 7 дней)')
    plt.xlabel('Дата')
    plt.ylabel('Температура (°C)')

    plt.grid(True)

    plt.legend()

    plt.gcf().autofmt_xdate()

    plt.show()


if __name__ == "__main__":

    print("1. Получение данных из API...")
    data = fetch_weather_data()

    print("2. Создание таблицы в SQLite...")
    create_table()

    print("3. Сохранение данных в базу...")
    save_to_db(data)

    print("4. Расчет метрик...")
    metrics = calculate_metrics()

    print("\n--- Аналитический отчет ---")
    print(f"Средняя максимальная температура: {metrics['avg_max']:.1f} °C")
    print(f"Средняя минимальная температура: {metrics['avg_min']:.1f} °C")
    print(f"Самый теплый день: {metrics['warmest_day']['date']} ({metrics['warmest_day']['temp']} °C)")
    print(f"Самый холодный день: {metrics['coldest_day']['date']} ({metrics['coldest_day']['temp']} °C)")
    print(f"Размах температур: {metrics['temp_range']:.1f} °C")
    print("-------------------------\n")

    print("5. Визуализация данных: ...")
    visualize_data()
