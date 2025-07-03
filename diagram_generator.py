import os
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import Optional
from config import TEMP_DIR, DIAGRAMS_DIR, MAX_CODE_LENGTH


class DiagramGenerator:
    def __init__(self):
        self.temp_dir = Path(TEMP_DIR)
        self.diagrams_dir = Path(DIAGRAMS_DIR)
        self.temp_dir.mkdir(exist_ok=True)
        self.diagrams_dir.mkdir(exist_ok=True)
    
    def _validate_code(self, code: str) -> bool:
        """Проверяет безопасность кода"""
        if len(code) > MAX_CODE_LENGTH:
            return False
            
        # Запрещенные импорты и функции
        forbidden_patterns = [
            'import os',
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
        
        import time
        timestamp = int(time.time())
        code_file = self.temp_dir / f"diagram_code_{user_id}_{timestamp}.py"
        png_file = self.temp_dir / f"output.png"
        print(f"[DEBUG] code_file: {code_file.resolve()}")
        print(f"[DEBUG] png_file (ожидаемый PNG): {png_file.resolve()}")
        print(f"[DEBUG] diagrams_dir (куда копируем): {self.diagrams_dir.resolve()}")
        print(f"[DEBUG] cwd процесса: {self.temp_dir.resolve()}")
        try:
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.temp_dir)
            process = await asyncio.create_subprocess_exec(
                sys.executable, code_file.name,
                cwd=str(self.temp_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                print(f"[DEBUG] diagrams process stderr: {error_msg}")
                raise Exception(f"Ошибка выполнения кода:\n{error_msg}")
            # Проверяем, что PNG создан
            if not png_file.exists():
                print(f"[DEBUG] PNG не найден по пути: {png_file.resolve()}")
                raise Exception("Диаграмма не была создана. Проверьте код.")
            # Копируем PNG в diagrams/
            output_file = self.diagrams_dir / f"diagram_{user_id}_{timestamp}.png"
            import shutil
            shutil.copy2(png_file, output_file)
            print(f"[DEBUG] PNG успешно скопирован в: {output_file.resolve()}")
            return str(output_file)
        except asyncio.TimeoutError:
            raise Exception("Превышено время выполнения кода (30 секунд)")
        except Exception as e:
            raise Exception(f"Ошибка генерации диаграммы: {str(e)}")
        finally:
            try:
                if Path(code_file).exists():
                    Path(code_file).unlink()
            except:
                pass


# Глобальный экземпляр генератора
diagram_generator = DiagramGenerator()

async def generate_diagram_with_retries(code: str, user_id: int, gigachat_client, max_attempts: int = 3):
    """
    Пытается сгенерировать диаграмму до max_attempts раз, отправляя ошибку и код в gigachat_client.fix_code при неудаче.
    Возвращает путь к диаграмме или (None, последний_код, последняя_ошибка) если не удалось.
    """
    last_error = None
    last_code = code
    for attempt in range(max_attempts):
        try:
            path = await diagram_generator.generate_diagram(last_code, user_id)
            return path
        except Exception as e:
            last_error = str(e)
            if attempt < max_attempts - 1:
                # Просим Гигачат исправить код
                try:
                    last_code = await gigachat_client.fix_code(last_code, last_error)
                except Exception as fix_e:
                    last_error += f"\nОшибка при обращении к Гигачату для исправления: {fix_e}"
                    break
    return None, last_code, last_error