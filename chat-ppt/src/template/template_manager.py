from pptx import Presentation

import os


def get_app_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    return root_dir


# 加载一个ppt模板
def load_template(template_path: str) -> Presentation:
    template_local_path = os.path.join(get_app_dir(), 'resources',template_path)
    prs = Presentation(template_local_path)
    return prs


def get_layout_mapping(prs: Presentation) -> dict:
    layout_mapping = {}
    for idx, layout in enumerate(prs.slide_layouts):
        layout_mapping[layout.name] = idx
    return layout_mapping


def print_layouts(prs: Presentation) -> None:
    for idx, layout in enumerate(prs.slide_layouts):
        print(f"Layout {idx}: {layout.name}")


if __name__ == '__main__':
    print(get_app_dir())
