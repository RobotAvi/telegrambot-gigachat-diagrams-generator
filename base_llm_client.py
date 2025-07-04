from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_diagram_code(self, user_request: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fix_code(self, code_with_error: str, error_message: str) -> str:
        raise NotImplementedError 