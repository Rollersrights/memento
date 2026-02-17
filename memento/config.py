#!/usr/bin/env python3
"""
Memento Configuration System
Handles loading, validation, and access to configuration settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# Default Paths - Unified location under .openclaw
DEFAULT_HOME = Path.home() / ".openclaw" / "memento"
DEFAULT_CONFIG_PATH = DEFAULT_HOME / "config.yaml"
SYSTEM_CONFIG_PATH = Path("/etc/memento/config.yaml")

@dataclass
class StorageConfig:
    db_path: str = str(DEFAULT_HOME / "memory.db")
    collection_table: str = "memories"
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"

@dataclass
class EmbedConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    cache_dir: str = str(DEFAULT_HOME / "models")
    use_quantized: bool = True
    batch_size: int = 32
    cache_size: int = 1000  # LRU cache size

@dataclass
class SearchConfig:
    default_topk: int = 5
    hybrid_alpha: float = 0.5  # Weight for vector vs keyword (future use)
    timeout_ms: int = 5000

@dataclass
class MementoConfig:
    storage: StorageConfig = field(default_factory=StorageConfig)
    embed: EmbedConfig = field(default_factory=EmbedConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    debug: bool = False
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'MementoConfig':
        """
        Load configuration from YAML files with override hierarchy:
        1. Defaults
        2. System config (/etc/memento/config.yaml)
        3. User config (~/.memento/config.yaml)
        4. Env vars (MEMENTO_*)
        """
        # Start with defaults
        config_data = {}
        
        # Load System
        if SYSTEM_CONFIG_PATH.exists():
            config_data = cls._merge(config_data, cls._load_yaml(SYSTEM_CONFIG_PATH))
            
        # Load User
        user_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        if user_path.exists():
            config_data = cls._merge(config_data, cls._load_yaml(user_path))
            
        # Parse into dataclass (simple mapping for now)
        # In a real system, use dacite or pydantic for robust parsing
        cfg = cls()
        
        # Storage overrides
        if 'storage' in config_data:
            s = config_data['storage']
            if 'db_path' in s: cfg.storage.db_path = os.path.expanduser(s['db_path'])
            if 'journal_mode' in s: cfg.storage.journal_mode = s['journal_mode']
            
        # Embed overrides
        if 'embed' in config_data:
            e = config_data['embed']
            if 'model_name' in e: cfg.embed.model_name = e['model_name']
            if 'cache_size' in e: cfg.embed.cache_size = int(e['cache_size'])
            
        # Env var overrides (highest priority)
        if os.environ.get("MEMENTO_DB_PATH"):
            cfg.storage.db_path = os.environ["MEMENTO_DB_PATH"]
            
        if os.environ.get("MEMENTO_DEBUG"):
            cfg.debug = os.environ["MEMENTO_DEBUG"].lower() in ("1", "true", "yes")
            
        return cfg

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            return {}

    @staticmethod
    def _merge(base: Dict, update: Dict) -> Dict:
        """Recursive merge of dictionaries."""
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                base[k] = MementoConfig._merge(base[k], v)
            else:
                base[k] = v
        return base

# Singleton instance
_config_instance = None

def get_config(reload: bool = False) -> MementoConfig:
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = MementoConfig.load()
    return _config_instance
