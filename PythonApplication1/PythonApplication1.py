#!/usr/bin/env python3
"""
Программа автоматического полива растений на Raspberry Pi.
Использует датчик влажности почвы (через ADS1115) и реле для управления помпой.
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

# ========== НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ ==========
MOISTURE_DRY = 25000   # Значение датчика в СУХОЙ почве (калибровать!)
MOISTURE_WET = 15000   # Значение датчика в МОКРОЙ почве (калибровать!)
THRESHOLD_PERCENT = 40 # Порог срабатывания (полив при влажности ниже 40%)
PUMP_TIME_SEC = 3.0    # Время работы помпы в секундах
CHECK_INTERVAL_SEC = 60 # Интервал проверки в секундах (1 минута)

RELAY_PIN = 17  # GPIO пин для управления реле
# =============================================

def setup():
    """Инициализация всех компонентов системы."""
    print("Инициализация системы автоматического полива...")
    
    # Настройка GPIO для реле
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Реле выключено (HIGH для активного LOW)
    
    # Инициализация I2C и ADS1115
    global i2c, ads, channel
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, gain=1)
    channel = AnalogIn(ads, ADS.P0)  # Датчик подключен к каналу A0
    
    print("Система готова к работе!")
    print(f"Конфигурация: порог {THRESHOLD_PERCENT}%, время полива {PUMP_TIME_SEC}с")
    print("-" * 40)

def read_moisture_percentage():
    """
    Чтение влажности в процентах.
    0% - полностью сухая почва, 100% - полностью мокрая.
    """
    raw_value = channel.value
    
    # Преобразование сырого значения в проценты
    if raw_value >= MOISTURE_DRY:
        return 0.0
    elif raw_value <= MOISTURE_WET:
        return 100.0
    else:
        percentage = ((MOISTURE_DRY - raw_value) / 
                     (MOISTURE_DRY - MOISTURE_WET)) * 100
        return max(0.0, min(100.0, percentage))  # Ограничиваем 0-100%

def control_pump(state, duration=0):
    """
    Управление помпой через реле.
    :param state: True - включить, False - выключить
    :param duration: время работы в секундах (если state=True)
    """
    if state:
        print(f"[ПОЛИВ] Включение помпы на {duration} секунд...")
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Включить реле
        time.sleep(duration)
        GPIO.output(RELAY_PIN, GPIO.HIGH) # Выключить реле
        print("[ПОЛИВ] Помпа выключена.")
    else:
        GPIO.output(RELAY_PIN, GPIO.HIGH)

def main_loop():
    """Основной цикл программы."""
    try:
        while True:
            # Чтение текущей влажности
            moisture = read_moisture_percentage()
            raw_value = channel.value
            
            # Вывод текущих значений
            print(f"[{time.strftime('%H:%M:%S')}] "
                  f"Влажность: {moisture:.1f}% | "
                  f"Сырое значение: {raw_value}")
            
            # Проверка условия полива
            if moisture < THRESHOLD_PERCENT:
                print(f"  -> Влажность ниже порога ({THRESHOLD_PERCENT}%), "
                      f"начинаю полив...")
                control_pump(True, PUMP_TIME_SEC)
            else:
                print(f"  -> Влажность в норме, полив не требуется.")
            
            # Пауза до следующей проверки
            print(f"  -> Следующая проверка через {CHECK_INTERVAL_SEC} сек.")
            print("-" * 40)
            time.sleep(CHECK_INTERVAL_SEC)
            
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
    finally:
        cleanup()

def cleanup():
    """Корректное завершение работы."""
    print("Очистка ресурсов...")
    control_pump(False)  # Гарантированно выключаем помпу
    GPIO.cleanup()
    print("Завершение работы. Все ресурсы освобождены.")

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    setup()
    main_loop()
