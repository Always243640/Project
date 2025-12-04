import sys
import time
from typing import Optional

import cv2
import pygame

from skills import (
    FlameAttackEffect,
    HealEffect,
    NormalAttackEffect,
    ShieldEffect,
    UltimateEffect,
)

from fonts import build_fonts
from gestures import detect_gestures
from state import (
    ROUND_LIMIT,
    SELECTION_TIME,
    PlayerState,
    RoundState,
    apply_round_damage,
    execute_skill,
)
from ui import draw_bars, draw_center_text, draw_skill_labels, draw_skills_area, render_hand_views

WIDTH, HEIGHT = 1280, 720
PLAYER_WIDTH, PLAYER_HEIGHT = 220, 320


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("双人PK游戏")
    clock = pygame.time.Clock()
    fonts = build_fonts()

    bg = pygame.image.load("bg.png")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    left_player_img = pygame.transform.scale(pygame.image.load("left.png"), (PLAYER_WIDTH, PLAYER_HEIGHT))
    right_player_img = pygame.transform.scale(pygame.image.load("right.png"), (PLAYER_WIDTH, PLAYER_HEIGHT))
    left_rect = left_player_img.get_rect()
    right_rect = right_player_img.get_rect()
    left_rect.midbottom = (WIDTH // 4, HEIGHT - 120)
    right_rect.midbottom = (WIDTH * 3 // 4-100, HEIGHT - 120)

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
    selection_prompt = "比OK开始游戏！"

    effects = []

    def spawn_effect(skill_id: int, actor_rect: pygame.Rect, target_rect: pygame.Rect, is_left: bool):
        if skill_id == 1:
            effects.append(
                NormalAttackEffect(
                    actor_rect.centerx,
                    actor_rect.centery - 40,
                    target_rect.centerx,
                    target_rect.centery - 40,
                    is_player1=is_left,
                )
            )
        elif skill_id == 2:
            effects.append(HealEffect(actor_rect.centerx, actor_rect.centery - 30))
        elif skill_id == 3:
            effects.append(
                FlameAttackEffect(
                    actor_rect.centerx,
                    actor_rect.centery - 50,
                    target_rect.centerx,
                    target_rect.centery - 50,
                )
            )
        elif skill_id == 4:
            effects.append(ShieldEffect(actor_rect.centerx, actor_rect.centery, is_left))
        elif skill_id == 5:
            effects.append(
                UltimateEffect(
                    actor_rect.centerx,
                    actor_rect.centery - 40,
                    is_player1=is_left,
                    target_x=target_rect.centerx,
                    target_y=target_rect.centery - 40,
                )
            )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        ret, frame = cap.read()
        if not ret:
            continue

        gestures, _annotated_frame, crops = detect_gestures(frame)

        screen.blit(bg, (0, 0))
        screen.blit(left_player_img, left_rect)
        screen.blit(right_player_img, right_rect)
        render_hand_views(screen, fonts, crops)

        if not started:
            draw_center_text(screen, fonts, selection_prompt, 10, color=(255, 255, 0))
            left_ok = any(g.is_ok and g.side == "Left" for g in gestures)
            right_ok = any(g.is_ok and g.side == "Right" for g in gestures)
            if left_ok and right_ok:
                started = True
                round_state.selection_start = time.time()
            pygame.display.flip()
            clock.tick(30)
            continue

        if game_over:
            draw_center_text(screen, fonts, f"{winner} 获胜!", HEIGHT // 2 - 40, color=(255, 200, 0))
            pygame.display.flip()
            clock.tick(30)
            continue

        if round_state.phase == "select":
            time_elapsed = time.time() - round_state.selection_start
            countdown = max(0, SELECTION_TIME - int(time_elapsed))
            draw_center_text(screen, fonts, f"第{round_state.round_index}回合", 20)
            draw_center_text(screen, fonts, f"倒计时: {countdown}s", 60, color=(255, 220, 120))
            for g in gestures:
                if g.side == "Left":
                    round_state.left_choice = g.gesture or round_state.left_choice
                elif g.side == "Right":
                    round_state.right_choice = g.gesture or round_state.right_choice
            draw_skills_area(screen, fonts, True, round_state.left_choice)
            draw_skills_area(screen, fonts, False, round_state.right_choice)

            if time_elapsed >= SELECTION_TIME:
                if round_state.left_choice is None:
                    winner = player_right.name
                    game_over = True
                elif round_state.right_choice is None:
                    winner = player_left.name
                    game_over = True
                else:
                    round_state.phase = "execute_left"
                    round_state.phase_time = time.time()
                    round_state.left_resolved = False
                    round_state.right_resolved = False
        elif round_state.phase == "execute_left":
            draw_skills_area(screen, fonts, True, round_state.left_choice)
            draw_skills_area(screen, fonts, False, None)
            draw_skill_labels(screen, fonts, round_state.left_choice, None, left_rect, right_rect)

            if not round_state.left_resolved:
                execute_skill(round_state.left_choice, player_left, player_right)
                spawn_effect(round_state.left_choice, left_rect, right_rect, True)
                apply_round_damage(player_right, decrement_cooldown=False)
                round_state.left_resolved = True
                round_state.phase_time = time.time()

                if player_right.hp <= 0:
                    winner = player_left.name
                    game_over = True

            if not game_over and time.time() - round_state.phase_time >= 2:
                round_state.phase = "execute_right"
                round_state.phase_time = time.time()
        elif round_state.phase == "execute_right":
            draw_skills_area(screen, fonts, True, None)
            draw_skills_area(screen, fonts, False, round_state.right_choice)
            draw_skill_labels(screen, fonts, None, round_state.right_choice, left_rect, right_rect)

            if not round_state.right_resolved:
                execute_skill(round_state.right_choice, player_right, player_left)
                spawn_effect(round_state.right_choice, right_rect, left_rect, False)
                apply_round_damage(player_left, decrement_cooldown=False)
                round_state.right_resolved = True
                round_state.phase_time = time.time()

                if player_left.hp <= 0:
                    winner = player_right.name
                    game_over = True

            if not game_over and time.time() - round_state.phase_time >= 2:
                apply_round_damage(player_left)
                apply_round_damage(player_right)
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
                    round_state.phase = "announce"
                    round_state.phase_time = time.time()
        elif round_state.phase == "announce":
            draw_center_text(screen, fonts, f"Round {round_state.round_index}", HEIGHT // 2 - 40)
            if time.time() - round_state.phase_time >= 1:
                round_state.reset_for_selection()

        for eff in effects[:]:
            eff.update()
            eff.draw(screen)
            if eff.is_done():
                effects.remove(eff)

        draw_bars(screen, fonts, player_left, (40, HEIGHT - 220))
        draw_bars(screen, fonts, player_right, (WIDTH - 320, HEIGHT - 220))

        pygame.display.flip()
        clock.tick(30)

    cap.release()
    pygame.quit()
