import json
import os
from pathlib import Path

if __name__ == '__main__':
    app_dir = Path(__file__).parent.parent.parent
    config_file: str = 'config.json'
    config_json_file = os.path.join(app_dir, 'resources', config_file)
    print(os.path.exists(config_json_file))


class Config:
    def __init__(self, config_file: str = 'config.json'):
        app_dir = Path(__file__).parent.parent.parent
        config_json_file = os.path.join(app_dir, 'resources', config_file)
        self.config_file = config_json_file
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file '{self.config_file}' not found.")

        with open(self.config_file, 'r') as f:
            config = json.load(f)

            # 加载 ChatPPT 运行模式（默认文本模态）
            self.input_mode = config.get('input_mode', "text")

            # 加载 PPT 默认模板
            self.ppt_template = config.get('ppt_template', "templates/MasterTemplate.pptx")

            # 加载布局映射
            self.layout_mapping = config.get('layout_mapping', {})
