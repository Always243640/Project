import pygame
from dataclasses import dataclass
from typing import List
def _find_chinese_font(candidates: List[str]):
    for name in candidates:
        matched = pygame.font.match_font(name)
        if matched:
            return matched
    return None
def build_fonts():
    candidates = ["SimHei", "Noto Sans CJK SC", "WenQuanYi Zen Hei", "Microsoft YaHei", "PingFang"]
    font_path = _find_chinese_font(candidates)
    return FontLibrary(font_path)
@dataclass
class FontLibrary:
    font_path: str
    def small(self):
        return pygame.font.Font(self.font_path, 24) if self.font_path else pygame.font.Font(None, 24)
    def medium(self):
        return pygame.font.Font(self.font_path, 32) if self.font_path else pygame.font.Font(None, 32)
    def large(self):
        return pygame.font.Font(self.font_path, 48) if self.font_path else pygame.font.Font(None, 48)
