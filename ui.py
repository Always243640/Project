from typing import Dict, Optional, Tuple
import cv2
import numpy as np
import pygame
from fonts import FontLibrary
from state import HP_MAX, MP_MAX, RAGE_MAX, PlayerState, skill_name

def draw_bars(screen, fonts: FontLibrary, player: PlayerState, pos: Tuple[int, int]):
    x, y = pos
    font_small = fonts.small()
    pygame.draw.rect(screen, (60, 60, 60), (x, y, 260, 20))
    pygame.draw.rect(screen, (200, 60, 60), (x, y, int(260 * player.hp / HP_MAX), 20))
    screen.blit(font_small.render(f"HP: {player.hp}/{HP_MAX}", True, (255, 255, 255)), (x + 5, y))

    pygame.draw.rect(screen, (60, 60, 60), (x, y + 25, 260, 18))
    pygame.draw.rect(screen, (60, 120, 220), (x, y + 25, int(260 * player.mp / MP_MAX), 18))
    screen.blit(font_small.render(f"MP: {player.mp}/{MP_MAX}", True, (255, 255, 255)), (x + 5, y + 23))

    pygame.draw.rect(screen, (60, 60, 60), (x, y + 48, 260, 16))
    pygame.draw.rect(screen, (220, 160, 60), (x, y + 48, int(260 * player.rage / RAGE_MAX), 16))
    screen.blit(font_small.render(f"Rage: {player.rage}/{RAGE_MAX}", True, (255, 255, 255)), (x + 5, y + 45))

    if player.shield > 0:
        shield_text = font_small.render(f"护盾:{player.shield}", True, (100, 220, 255))
        screen.blit(shield_text, (x + 200, y + 65))
    if player.debuff_attack > 0:
        debuff_text = font_small.render(f"减攻:{player.debuff_attack}", True, (255, 120, 0))
        screen.blit(debuff_text, (x + 120, y + 65))


def draw_skills_area(screen, fonts: FontLibrary, is_left: bool, selected: Optional[int]):
    base_x = 30 if is_left else screen.get_width() - 290
    base_y = screen.get_height() - 140
    labels = ["普", "回血", "火焰", "屏障", "大招"]
    font_small = fonts.small()
    for i, name in enumerate(labels, start=1):
        rect = pygame.Rect(base_x + (i - 1) * 50, base_y, 48, 60)
        color = (120, 120, 120)
        if selected == i:
            color = (60, 200, 120)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        screen.blit(font_small.render(str(i), True, (0, 0, 0)), (rect.x + 18, rect.y + 5))
        text = font_small.render(name, True, (0, 0, 0))
        screen.blit(text, (rect.x + 5, rect.y + 28))


def render_hand_views(screen, fonts: FontLibrary, crops: Dict[str, np.ndarray]):
    placeholders = {
        "Left": (20, 20),
        "Right": (screen.get_width() - 280, 20),
    }
    font_small = fonts.small()
    for label, pos in placeholders.items():
        frame = crops.get(label)
        if frame is not None and frame.size > 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(np.rot90(rgb))
            surface = pygame.transform.scale(surface, (260, 180))
            screen.blit(surface, pos)
        else:
            pygame.draw.rect(screen, (40, 40, 40), (*pos, 260, 180))
            hint = "Player 1" if label == "Left" else "Player 2"
            screen.blit(font_small.render(hint, True, (200, 200, 200)), (pos[0] + 60, pos[1] + 80))


def draw_skill_labels(screen, fonts: FontLibrary, left_skill: Optional[int], right_skill: Optional[int], left_rect, right_rect):
    font_medium = fonts.medium()
    if left_skill is not None:
        left_skill_text = font_medium.render(skill_name(left_skill), True, (0, 255, 180))
        screen.blit(left_skill_text, (left_rect.centerx - 40, left_rect.top - 30))
    if right_skill is not None:
        right_skill_text = font_medium.render(skill_name(right_skill), True, (0, 255, 180))
        screen.blit(right_skill_text, (right_rect.centerx - 40, right_rect.top - 30))


def draw_center_text(screen, fonts: FontLibrary, text: str, y: int, color=(255, 255, 255)):
    font_large = fonts.large()
    rendered = font_large.render(text, True, color)
    screen.blit(rendered, (screen.get_width() // 2 - rendered.get_width() // 2, y))
