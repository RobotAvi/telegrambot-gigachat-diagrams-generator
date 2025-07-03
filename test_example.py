#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы компонентов бота без Telegram
"""

import asyncio
import os
from gigachat_client import gigachat_client
from diagram_generator import diagram_generator


async def test_gigachat_connection():
    """Тест подключения к GigaChat"""
    print("🔍 Тест подключения к GigaChat...")
    
    # Запрашиваем API ключ у пользователя
    api_key = input("Введите ваш API ключ GigaChat: ").strip()
    
    try:
        gigachat_client.set_credentials(api_key)
        is_valid = await gigachat_client.check_credentials()
        
        if is_valid:
            print("✅ Подключение к GigaChat успешно!")
            return True
        else:
            print("❌ Неверный API ключ")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


async def test_diagram_generation():
    """Тест генерации диаграммы"""
    print("\n📊 Тест генерации диаграммы...")
    
    # Простой тестовый запрос
    request = "Создай простую диаграмму веб-сервиса с базой данных"
    
    try:
        # Генерируем код
        print("🤖 Генерация кода...")
        code = await gigachat_client.generate_diagram_code(request)
        print(f"Сгенерированный код:\n{code}\n")
        
        # Создаем диаграмму
        print("🔨 Создание диаграммы...")
        diagram_path = await diagram_generator.generate_diagram(code, 12345)
        
        if diagram_path and os.path.exists(diagram_path):
            print(f"✅ Диаграмма создана: {diagram_path}")
            print(f"Размер файла: {os.path.getsize(diagram_path)} байт")
            return True
        else:
            print("❌ Диаграмма не создана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование Diagram Generator Bot")
    print("====================================")
    
    # Тест подключения к GigaChat
    gigachat_ok = await test_gigachat_connection()
    
    if not gigachat_ok:
        print("\n❌ Тестирование прервано - проблемы с GigaChat")
        return
    
    # Тест генерации диаграммы
    diagram_ok = await test_diagram_generation()
    
    # Итоги
    print("\n📋 Результаты тестирования:")
    print(f"GigaChat подключение: {'✅' if gigachat_ok else '❌'}")
    print(f"Генерация диаграмм: {'✅' if diagram_ok else '❌'}")
    
    if gigachat_ok and diagram_ok:
        print("\n🎉 Все тесты пройдены! Бот готов к работе.")
    else:
        print("\n⚠️ Обнаружены проблемы. Проверьте настройки.")


if __name__ == "__main__":
    asyncio.run(main())