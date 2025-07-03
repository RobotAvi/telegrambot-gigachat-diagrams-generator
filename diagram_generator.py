import os
import sys
import tempfile
import subprocess
import asyncio
from pathlib import Path
from typing import Optional
from config import TEMP_DIR, DIAGRAMS_DIR, MAX_CODE_LENGTH


class DiagramGenerator:
    def __init__(self):
        self.temp_dir = Path(TEMP_DIR)
        self.diagrams_dir = Path(DIAGRAMS_DIR)
        
        # Создаем необходимые директории
        self.temp_dir.mkdir(exist_ok=True)
        self.diagrams_dir.mkdir(exist_ok=True)
    
    def _validate_code(self, code: str) -> bool:
        """Проверяет безопасность кода"""
        if len(code) > MAX_CODE_LENGTH:
            return False
            
        # Запрещенные импорты и функции
        forbidden_patterns = [
            'import sys', 
            'import subprocess',
            'import shutil',
            'import glob',
            'from os',
            'from sys',
            'from subprocess',
            'from shutil',
            'from glob',
            '__import__',
            'eval(',
            'exec(',
            'open(',
            'file(',
            'input(',
            'raw_input(',
            'compile(',
            'reload(',
            'vars(',
            'dir(',
            'getattr(',
            'setattr(',
            'delattr(',
            'hasattr(',
        ]
        
        code_lower = code.lower()
        for pattern in forbidden_patterns:
            if pattern in code_lower:
                return False
                
        # Должен содержать импорт diagrams
        if 'from diagrams' not in code and 'import diagrams' not in code:
            return False
            
        return True
    
    async def generate_diagram(self, code: str, user_id: int) -> Optional[str]:
        """Генерирует диаграмму из кода и возвращает путь к файлу"""
        if not self._validate_code(code):
            raise ValueError("Небезопасный или некорректный код")
        
        # Создаем уникальную временную директорию для пользователя
        user_temp_dir = self.temp_dir / f"user_{user_id}_{int(asyncio.get_event_loop().time())}"
        user_temp_dir.mkdir(exist_ok=True)
        
        try:
            # Записываем код в файл
            code_file = user_temp_dir / "diagram_code.py"
            
            # Убираем смену директории - она уже установлена через cwd
            # Код будет выполняться в правильной директории автоматически
            
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Выполняем код в изолированной среде
            env = os.environ.copy()
            env['PYTHONPATH'] = str(user_temp_dir)
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(code_file),
                cwd=str(user_temp_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise Exception(f"Ошибка выполнения кода: {error_msg}")
            
            # Ищем созданные PNG файлы
            png_files = list(user_temp_dir.glob("*.png"))
            if not png_files:
                raise Exception("Диаграмма не была создана. Проверьте код.")
            
            # Берем первый найденный PNG файл
            diagram_file = png_files[0]
            
            # Копируем файл в постоянную директорию
            output_file = self.diagrams_dir / f"diagram_{user_id}_{int(asyncio.get_event_loop().time())}.png"
            
            import shutil
            shutil.copy2(diagram_file, output_file)
            
            return str(output_file)
            
        except asyncio.TimeoutError:
            raise Exception("Превышено время выполнения кода (30 секунд)")
        except Exception as e:
            raise Exception(f"Ошибка генерации диаграммы: {str(e)}")
        finally:
            # Очищаем временную директорию
            try:
                import shutil
                shutil.rmtree(user_temp_dir, ignore_errors=True)
            except:
                pass


# Глобальный экземпляр генератора
diagram_generator = DiagramGenerator()