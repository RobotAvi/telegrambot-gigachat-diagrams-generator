#!/usr/bin/env python3
"""
Базовый тест компонентов без API ключей
"""

import asyncio
import tempfile
import os
from pathlib import Path

def test_imports():
    """Тест импортов всех необходимых модулей"""
    print("🔍 Тест импортов...")
    
    try:
        # Тест импорта основных зависимостей
        import aiogram
        print("✅ aiogram импортирован успешно")
        
        import aiohttp
        print("✅ aiohttp импортирован успешно")
        
        import diagrams
        print("✅ diagrams импортирован успешно")
        
        # Тест импорта наших модулей
        import config
        print("✅ config импортирован успешно")
        
        import gigachat_client
        print("✅ gigachat_client импортирован успешно")
        
        import diagram_generator
        print("✅ diagram_generator импортирован успешно")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False


def test_diagrams_basic():
    """Тест базовой функциональности diagrams"""
    print("\n📊 Тест библиотеки diagrams...")
    
    try:
        from diagrams import Diagram
        from diagrams.aws.compute import EC2
        from diagrams.aws.network import ELB
        
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Создаем простую диаграмму
                with Diagram("Test Diagram", show=False, filename="test"):
                    lb = ELB("Load Balancer")
                    web = EC2("Web Server")
                    lb >> web
                
                # Проверяем что файл создался
                if os.path.exists("test.png"):
                    print("✅ Диаграмма создана успешно")
                    file_size = os.path.getsize("test.png")
                    print(f"✅ Размер файла: {file_size} байт")
                    return True
                else:
                    print("❌ Файл диаграммы не создан")
                    return False
                    
            finally:
                os.chdir(old_cwd)
                
    except Exception as e:
        print(f"❌ Ошибка создания диаграммы: {e}")
        return False


def test_diagram_generator():
    """Тест генератора диаграмм"""
    print("\n🔨 Тест генератора диаграмм...")
    
    try:
        from diagram_generator import DiagramGenerator
        
        generator = DiagramGenerator()
        
        # Тест валидации кода
        valid_code = '''
from diagrams import Diagram
from diagrams.aws.compute import EC2

with Diagram("Test", show=False, filename="output"):
    ec2 = EC2("Instance")
'''
        
        invalid_code = '''
import os
os.system("rm -rf /")
'''
        
        if generator._validate_code(valid_code):
            print("✅ Валидация корректного кода прошла")
        else:
            print("❌ Валидация корректного кода не прошла")
            return False
            
        if not generator._validate_code(invalid_code):
            print("✅ Валидация опасного кода отклонена")
        else:
            print("❌ Валидация опасного кода пропущена")
            return False
            
        print("✅ Генератор диаграмм работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования генератора: {e}")
        return False


def test_gigachat_client():
    """Тест клиента GigaChat"""
    print("\n🤖 Тест клиента GigaChat...")
    
    try:
        from gigachat_client import GigaChatClient
        
        client = GigaChatClient()
        
        # Тест установки учетных данных
        client.set_credentials("test_secret")
        
        if client.client_secret == "test_secret":
            print("✅ Установка учетных данных работает")
        else:
            print("❌ Установка учетных данных не работает")
            return False
            
        print("✅ Клиент GigaChat инициализирован корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования клиента: {e}")
        return False


def test_config():
    """Тест конфигурации"""
    print("\n⚙️ Тест конфигурации...")
    
    try:
        import config
        
        # Проверяем основные константы
        assert hasattr(config, 'GIGACHAT_BASE_URL')
        assert hasattr(config, 'GIGACHAT_AUTH_URL')
        assert hasattr(config, 'GIGACHAT_SYSTEM_PROMPT')
        assert hasattr(config, 'MAX_CODE_LENGTH')
        assert hasattr(config, 'TEMP_DIR')
        assert hasattr(config, 'DIAGRAMS_DIR')
        
        print("✅ Все конфигурационные константы присутствуют")
        print(f"✅ Системный промпт длиной {len(config.GIGACHAT_SYSTEM_PROMPT)} символов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        return False


async def main():
    """Главная функция тестирования"""
    print("🧪 Базовое тестирование Diagram Generator Bot")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_gigachat_client,
        test_diagram_generator,
        test_diagrams_basic,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
            results.append(False)
    
    # Итоги
    print("\n" + "=" * 50)
    print("📋 Результаты тестирования:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Система готова к работе.")
        print("\n📝 Для запуска бота:")
        print("1. Получите токен бота у @BotFather")
        print("2. Добавьте BOT_TOKEN в .env файл")
        print("3. Запустите: python main.py")
        print("4. Получите API ключ GigaChat и введите в боте")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте ошибки выше.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())