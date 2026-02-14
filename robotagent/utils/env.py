import os
from dotenv import load_dotenv

def load_env(
    env_path: str = None
) -> bool:
    return load_dotenv(
       dotenv_path=env_path
    )

def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

def get_int_env(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        msg = (
            f"Invalid integer value for {name}: {value}.\n"
            f"Using default value: {default}."
        )
        print(msg)
        return default

def get_float_env(name: str, default: float = 0.0) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value.strip())
    except ValueError:
        msg = (
            f"Invalid float value for {name}: {value}.\n"
            f"Using default value: {default}."
        )
        print(msg)
        return default

def get_str_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip()

