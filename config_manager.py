import os
import json
from typing import Dict, Optional


class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.templates_file = os.path.join(self.config_dir, "templates.json")
        self.last_input_file = os.path.join(self.config_dir, "last_input.json")

    def save_template(self, name: str, subject: str, content: str, content_type: str = "html"):
        templates = self._load_templates()
        templates[name] = {
            "subject": subject,
            "content": content,
            "content_type": content_type
        }
        self._save_templates(templates)

    def get_template(self, name: str) -> Optional[Dict]:
        templates = self._load_templates()
        return templates.get(name)

    def delete_template(self, name: str):
        templates = self._load_templates()
        if name in templates:
            del templates[name]
            self._save_templates(templates)

    def list_templates(self) -> Dict:
        return self._load_templates()

    def save_last_input(self, tab: str, data: Dict):
        inputs = self._load_last_input()
        inputs[tab] = data
        self._save_last_input(inputs)

    def get_last_input(self, tab: str) -> Optional[Dict]:
        inputs = self._load_last_input()
        return inputs.get(tab)

    def _load_templates(self) -> Dict:
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_templates(self, templates: Dict):
        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    def _load_last_input(self) -> Dict:
        if os.path.exists(self.last_input_file):
            try:
                with open(self.last_input_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_last_input(self, inputs: Dict):
        with open(self.last_input_file, "w", encoding="utf-8") as f:
            json.dump(inputs, f, ensure_ascii=False, indent=2)
