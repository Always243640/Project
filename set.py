import sys
import time
import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import pygame

# 初始化 pygame
pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("双人PK游戏")
clock = pygame.time.Clock()
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 32)
FONT_LARGE = pygame.font.Font(None, 48)

# 资源加载
bg = pygame.image.load("bg.png")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
left_player_img = pygame.image.load("left.png")
right_player_img = pygame.image.load("right.png")
PLAYER_WIDTH, PLAYER_HEIGHT = 220, 320
left_player_img = pygame.transform.scale(left_player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
right_player_img = pygame.transform.scale(right_player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

left_rect = left_player_img.get_rect()
right_rect = right_player_img.get_rect()
left_rect.midbottom = (WIDTH // 4, HEIGHT - 40)
right_rect.midbottom = (WIDTH * 3 // 4, HEIGHT - 40)

# Mediapipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands_detector = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5,
                                min_tracking_confidence=0.5)

# 规则参数
ROUND_LIMIT = 30
SELECTION_TIME = 5


@dataclass
class PlayerState:
    name: str
    is_left: bool
    hp: int = 100
    mp: int = 50
    rage: int = 0
    shield: int = 0
    debuff_attack: int = 0
    heal_cooldown: int = 0
    last_skill: Optional[int] = None
    pending_damage: int = 0

    def apply_damage(self, dmg: int):
        if self.shield > 0:
            absorbed = min(self.shield, dmg)
            self.shield -= absorbed
            dmg -= absorbed
        self.hp = max(0, self.hp - dmg)
        if dmg > 0:
            self.rage = min(100, self.rage + (dmg // 10))

    def restore_mana(self, amount: int):
        self.mp = min(100, self.mp + amount)

    def use_mana(self, amount: int) -> bool:
        if self.mp >= amount:
            self.mp -= amount
            return True
        return False

    def heal(self, amount: int):
        self.hp = min(100, self.hp + amount)


@dataclass
class RoundState:
    round_index: int = 1
    selecting: bool = True
    selection_start: float = field(default_factory=time.time)
    left_choice: Optional[int] = None
    right_choice: Optional[int] = None
    executing: bool = False
    execute_time: float = 0.0


@dataclass
class GestureResult:
    gesture: Optional[int]
    is_ok: bool
    handedness: str


def count_fingers(hand_landmarks, handedness: str) -> int:
    """简易手指数算法，返回1-5之间的数字。"""
    tips = [4, 8, 12, 16, 20]
    fingers = []
    # 手的左右会影响拇指判断方向
    if handedness == "Right":
        fingers.append(hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x)
    else:
        fingers.append(hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 1].x)
    for idx in range(1, 5):
        fingers.append(hand_landmarks.landmark[tips[idx]].y < hand_landmarks.landmark[tips[idx] - 2].y)
    return sum(fingers)


def detect_ok(hand_landmarks) -> bool:
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    return dist < 0.05


def detect_gestures(frame) -> Tuple[list, np.ndarray]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands_detector.process(rgb)
    gestures = []
    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label
            gesture_num = count_fingers(hand_landmarks, label)
            gestures.append(GestureResult(gesture=gesture_num if 1 <= gesture_num <= 5 else None,
                                          is_ok=detect_ok(hand_landmarks),
                                          handedness=label))
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    return gestures, frame


def draw_bars(player: PlayerState, pos: Tuple[int, int]):
    x, y = pos
    pygame.draw.rect(screen, (60, 60, 60), (x, y, 260, 20))
    pygame.draw.rect(screen, (200, 60, 60), (x, y, int(260 * player.hp / 100), 20))
    screen.blit(FONT_SMALL.render(f"HP: {player.hp}/100", True, (255, 255, 255)), (x + 5, y))

    pygame.draw.rect(screen, (60, 60, 60), (x, y + 25, 260, 18))
    pygame.draw.rect(screen, (60, 120, 220), (x, y + 25, int(260 * player.mp / 100), 18))
    screen.blit(FONT_SMALL.render(f"MP: {player.mp}/100", True, (255, 255, 255)), (x + 5, y + 23))

    pygame.draw.rect(screen, (60, 60, 60), (x, y + 48, 260, 16))
    pygame.draw.rect(screen, (220, 160, 60), (x, y + 48, int(260 * player.rage / 100), 16))
    screen.blit(FONT_SMALL.render(f"Rage: {player.rage}/100", True, (255, 255, 255)), (x + 5, y + 45))

    if player.shield > 0:
        shield_text = FONT_SMALL.render(f"护盾:{player.shield}", True, (100, 220, 255))
        screen.blit(shield_text, (x + 200, y + 65))
    if player.debuff_attack > 0:
        debuff_text = FONT_SMALL.render(f"减攻:{player.debuff_attack}", True, (255, 120, 0))
        screen.blit(debuff_text, (x + 120, y + 65))


def draw_skills_area(is_left: bool, selected: Optional[int]):
    base_x = 30 if is_left else WIDTH - 290
    base_y = HEIGHT - 140
    labels = ["普攻", "回血", "火焰", "屏障", "大招"]
    for i, name in enumerate(labels, start=1):
        rect = pygame.Rect(base_x + (i - 1) * 50, base_y, 48, 60)
        color = (120, 120, 120)
        if selected == i:
            color = (60, 200, 120)
        pygame.draw.rect(screen, color, rect, border_radius=6)
        screen.blit(FONT_SMALL.render(str(i), True, (0, 0, 0)), (rect.x + 18, rect.y + 5))
        text = FONT_SMALL.render(name, True, (0, 0, 0))
        screen.blit(text, (rect.x + 5, rect.y + 28))


def skill_name(skill_id: Optional[int]) -> str:
    mapping = {1: "普攻", 2: "回血", 3: "火焰", 4: "屏障", 5: "大招"}
    return mapping.get(skill_id, "未选择")


def execute_skill(skill_id: int, actor: PlayerState, target: PlayerState):
    dmg_pending = 0
    if skill_id == 1:  # 普攻
        damage = 10
        if actor.debuff_attack > 0:
            damage = max(0, damage - actor.debuff_attack)
            actor.debuff_attack = 0
        dmg_pending = damage
        actor.restore_mana(5)
    elif skill_id == 2:  # 回血
        if actor.heal_cooldown == 0:
            actor.heal(20)
            actor.heal_cooldown = 1
            actor.restore_mana(5)
        else:
            dmg_pending = 0
    elif skill_id == 3:  # 火焰
        if actor.use_mana(20):
            damage = 50
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            target.debuff_attack = 10
        else:
            actor.last_skill = None
    elif skill_id == 4:  # 防御屏障
        if actor.use_mana(15):
            actor.shield = max(actor.shield, 30)
        else:
            actor.last_skill = None
    elif skill_id == 5:  # 大招
        if actor.rage >= 50 and actor.use_mana(50):
            damage = 100
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            actor.heal(30)
            actor.rage = 0
        else:
            actor.last_skill = None

    target.pending_damage += dmg_pending


def apply_round_damage(player: PlayerState):
    if player.pending_damage > 0:
        player.apply_damage(player.pending_damage)
        player.pending_damage = 0
    if player.heal_cooldown > 0:
        player.heal_cooldown -= 1


def render_camera(frame, topleft: Tuple[int, int]):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    surface = pygame.surfarray.make_surface(frame)
    surface = pygame.transform.scale(surface, (260, 180))
    screen.blit(surface, topleft)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    player_left = PlayerState("玩家1", True)
    player_right = PlayerState("玩家2", False)
    round_state = RoundState()
    started = False
    game_over = False
    winner: Optional[str] = None
    selection_prompt = "比ok开始游戏！"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        ret, frame = cap.read()
        if not ret:
            continue

        gestures, annotated_frame = detect_gestures(frame)

        screen.blit(bg, (0, 0))
        screen.blit(left_player_img, left_rect)
        screen.blit(right_player_img, right_rect)

        render_camera(annotated_frame, (20, 20))
        render_camera(annotated_frame, (WIDTH - 280, 20))

        if not started:
            screen.blit(FONT_LARGE.render(selection_prompt, True, (255, 255, 0)), (WIDTH // 2 - 160, 10))
            left_ok = any(g.is_ok and g.handedness == "Left" for g in gestures)
            right_ok = any(g.is_ok and g.handedness == "Right" for g in gestures)
            if left_ok and right_ok:
                started = True
                round_state.selection_start = time.time()
            pygame.display.flip()
            clock.tick(30)
            continue

        if game_over:
            over_text = FONT_LARGE.render(f"{winner} 获胜!", True, (255, 200, 0))
            screen.blit(over_text, (WIDTH // 2 - 100, HEIGHT // 2 - 40))
            pygame.display.flip()
            clock.tick(30)
            continue

        time_elapsed = time.time() - round_state.selection_start
        countdown = max(0, SELECTION_TIME - int(time_elapsed))

        screen.blit(FONT_MEDIUM.render(f"第{round_state.round_index}回合", True, (255, 255, 255)), (WIDTH // 2 - 60, 20))
        screen.blit(FONT_MEDIUM.render(f"倒计时: {countdown}s", True, (255, 220, 120)), (WIDTH // 2 - 70, 50))

        if round_state.selecting:
            for g in gestures:
                if g.handedness == "Left":
                    round_state.left_choice = g.gesture or round_state.left_choice
                else:
                    round_state.right_choice = g.gesture or round_state.right_choice

            draw_skills_area(True, round_state.left_choice)
            draw_skills_area(False, round_state.right_choice)

            if time_elapsed >= SELECTION_TIME:
                if round_state.left_choice is None:
                    winner = player_right.name
                    game_over = True
                elif round_state.right_choice is None:
                    winner = player_left.name
                    game_over = True
                else:
                    round_state.selecting = False
                    round_state.execute_time = time.time()
        else:
            draw_skills_area(True, round_state.left_choice)
            draw_skills_area(False, round_state.right_choice)
            left_skill_text = FONT_MEDIUM.render(f"{skill_name(round_state.left_choice)}", True, (0, 255, 180))
            right_skill_text = FONT_MEDIUM.render(f"{skill_name(round_state.right_choice)}", True, (0, 255, 180))
            screen.blit(left_skill_text, (left_rect.centerx - 40, left_rect.top - 30))
            screen.blit(right_skill_text, (right_rect.centerx - 40, right_rect.top - 30))

            if time.time() - round_state.execute_time >= 1:
                execute_skill(round_state.left_choice, player_left, player_right)
                execute_skill(round_state.right_choice, player_right, player_left)
                apply_round_damage(player_left)
                apply_round_damage(player_right)

                if player_left.hp <= 0:
                    winner = player_right.name
                    game_over = True
                elif player_right.hp <= 0:
                    winner = player_left.name
                    game_over = True
                else:
                    round_state.round_index += 1
                    if round_state.round_index > ROUND_LIMIT:
                        if player_left.hp > player_right.hp:
                            winner = player_left.name
                        elif player_right.hp > player_left.hp:
                            winner = player_right.name
                        else:
                            winner = "平局"
                        game_over = True
                    else:
                        round_state = RoundState(round_index=round_state.round_index,
                                                selection_start=time.time())

        draw_bars(player_left, (40, HEIGHT - 220))
        draw_bars(player_right, (WIDTH - 320, HEIGHT - 220))

        pygame.display.flip()
        clock.tick(30)

    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()
