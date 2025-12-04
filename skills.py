import pygame
import random
import math
import numpy as np

# 初始化Pygame混合模式
pygame.init()


class Particle:
    """基础粒子类"""

    def __init__(self, x, y, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(1.0, 3.0)
        self.speed_x = random.uniform(-2.0, 2.0)
        self.speed_y = random.uniform(-2.0, 2.0)
        self.life = random.randint(20, 60)
        self.max_life = self.life
        self.gravity = random.uniform(0.05, 0.2)
        self.decay = random.uniform(0.05, 0.1)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        self.life -= 1
        self.size = max(0, self.size - self.decay)
        return self.life > 0

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            temp_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (*self.color, alpha),
                               (int(self.size), int(self.size)), int(self.size))
            surface.blit(temp_surface, (int(self.x - self.size), int(self.y - self.size)))


class NormalAttackEffect:
    """普通攻击特效"""

    def __init__(self, start_x, start_y, target_x, target_y, is_player1=True):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.current_pos = list(self.start_pos)
        self.progress = 0
        self.speed = 0.15
        self.color = (255, 255, 100) if is_player1 else (100, 255, 255)  # 金色/青色
        self.particles = []
        self.hit_effect = False
        self.hit_particles = []
        self.is_hit = False

    def update(self):
        if not self.is_hit:
            self.progress += self.speed

            # 计算当前位置
            self.current_pos[0] = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * self.progress
            self.current_pos[1] = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * self.progress

            # 创建轨迹粒子
            if random.random() < 0.5:
                particle_color = (255, 255, 200) if self.color == (255, 255, 100) else (200, 255, 255)
                self.particles.append(Particle(self.current_pos[0], self.current_pos[1], particle_color))

            # 更新粒子
            for particle in self.particles[:]:
                if not particle.update():
                    self.particles.remove(particle)

            # 检查是否击中目标
            if self.progress >= 1:
                self.create_hit_effect()
                self.is_hit = True
        else:
            # 更新击中粒子
            for particle in self.hit_particles[:]:
                if not particle.update():
                    self.hit_particles.remove(particle)

    def create_hit_effect(self):
        """创建击中特效"""
        # 创建击中光晕
        for i in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            color = (255, 255, 150) if self.color == (255, 255, 100) else (150, 255, 255)
            particle = Particle(self.target_pos[0], self.target_pos[1], color)
            particle.speed_x = math.cos(angle) * speed
            particle.speed_y = math.sin(angle) * speed
            particle.size = random.uniform(2, 4)
            particle.life = random.randint(15, 30)
            particle.max_life = particle.life
            self.hit_particles.append(particle)

        # 创建数字"10"的粒子效果（伤害数值）
        for i in range(10):
            particle = Particle(self.target_pos[0], self.target_pos[1] - 30, (255, 255, 255))
            particle.speed_y = -random.uniform(1, 2)
            particle.size = 2
            particle.life = 30
            particle.max_life = 30
            self.hit_particles.append(particle)

    def draw(self, surface):
        if not self.is_hit:
            # 绘制攻击轨迹
            if self.particles:
                for particle in self.particles:
                    particle.draw(surface)

            # 绘制攻击主体（光球）
            size = 8
            pygame.draw.circle(surface, self.color, (int(self.current_pos[0]), int(self.current_pos[1])), size)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.current_pos[0]), int(self.current_pos[1])), size - 2)

            # 绘制轨迹线
            pygame.draw.line(surface, (*self.color, 100),
                             self.start_pos, (int(self.current_pos[0]), int(self.current_pos[1])), 2)
        else:
            # 绘制击中特效
            for particle in self.hit_particles:
                particle.draw(surface)

            # 绘制伤害数字
            if len(self.hit_particles) > 10:  # 确保还有粒子显示数字
                font = pygame.font.Font(None, 24)
                text = font.render("10", True, (255, 255, 255))
                surface.blit(text, (self.target_pos[0] - 8, self.target_pos[1] - 40))

    def is_done(self):
        return self.is_hit and len(self.hit_particles) == 0


class HealEffect:
    """回血技能特效"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = 40
        self.growing = True
        self.heal_particles = []
        self.number_particles = []
        self.life = 60
        self.max_life = self.life

    def update(self):
        # 更新光环大小
        if self.growing:
            self.radius += 1
            if self.radius >= self.max_radius:
                self.growing = False
        else:
            self.radius = max(0, self.radius - 0.5)

        self.life -= 1

        # 创建治疗粒子（绿色向上飘）
        if random.random() < 0.4 and self.life > 20:
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(0, self.radius)
            px = self.x + math.cos(angle) * distance
            py = self.y + math.sin(angle) * distance

            particle = Particle(px, py, (100, 255, 100))
            particle.speed_x = random.uniform(-0.3, 0.3)
            particle.speed_y = random.uniform(-2, -1.5)
            particle.size = random.uniform(3, 6)
            particle.life = random.randint(30, 50)
            particle.max_life = particle.life
            particle.gravity = -0.03
            self.heal_particles.append(particle)

        # 创建数字"15"的粒子效果
        if self.life == 50:  # 在特定时间创建数字粒子
            for i in range(15):
                particle = Particle(self.x, self.y - 20, (150, 255, 150))
                particle.speed_y = -random.uniform(1, 1.5)
                particle.speed_x = random.uniform(-0.5, 0.5)
                particle.size = 1.5
                particle.life = 40
                particle.max_life = 40
                self.number_particles.append(particle)

        # 更新粒子
        for particle in self.heal_particles[:] + self.number_particles[:]:
            if isinstance(particle, Particle) and not particle.update():
                if particle in self.heal_particles:
                    self.heal_particles.remove(particle)
                else:
                    self.number_particles.remove(particle)

    def draw(self, surface):
        if self.life > 0:
            # 绘制治疗光环
            alpha = int(255 * (self.life / self.max_life))

            # 绘制多层同心圆
            for i in range(3):
                radius = self.radius - i * 5
                if radius > 0:
                    circle_alpha = alpha - i * 40
                    if circle_alpha > 0:
                        temp_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                        pygame.draw.circle(temp_surface, (100, 255, 100, circle_alpha),
                                           (int(radius), int(radius)), int(radius))
                        pygame.draw.circle(temp_surface, (200, 255, 200, circle_alpha),
                                           (int(radius), int(radius)), int(radius), 2)
                        surface.blit(temp_surface, (int(self.x - radius), int(self.y - radius)))

            # 绘制治疗粒子
            for particle in self.heal_particles:
                particle.draw(surface)

            # 绘制数字粒子
            for particle in self.number_particles:
                particle.draw(surface)

            # 绘制治疗符号（加号）
            if self.life > 40:
                cross_alpha = int(255 * ((self.life - 40) / 20))
                temp_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
                # 绘制加号
                pygame.draw.line(temp_surface, (200, 255, 200, cross_alpha),
                                 (5, 15), (25, 15), 4)
                pygame.draw.line(temp_surface, (200, 255, 200, cross_alpha),
                                 (15, 5), (15, 25), 4)
                surface.blit(temp_surface, (int(self.x - 15), int(self.y - 15)))

            # 绘制回血数字
            if 30 < self.life < 50:
                font = pygame.font.Font(None, 28)
                text = font.render("+15", True, (100, 255, 100))
                text_rect = text.get_rect(center=(self.x, self.y - 50))
                surface.blit(text, text_rect)

    def is_done(self):
        return self.life <= 0


class FlameAttackEffect:
    """火焰攻击特效"""

    def __init__(self, start_x, start_y, target_x, target_y):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.fireballs = []
        self.explosions = []
        self.debuff_indicator = None
        self.create_fireballs()

    def create_fireballs(self):
        """创建多个火球"""
        for i in range(3):
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-20, 20)

            fireball = {
                'x': self.start_pos[0] + offset_x,
                'y': self.start_pos[1] + offset_y,
                'target_x': self.target_pos[0] + offset_x,
                'target_y': self.target_pos[1] + offset_y,
                'progress': 0,
                'speed': random.uniform(0.08, 0.12),
                'particles': [],
                'exploded': False
            }
            self.fireballs.append(fireball)

    def update(self):
        # 更新火球
        for fireball in self.fireballs[:]:
            if not fireball['exploded']:
                fireball['progress'] += fireball['speed']

                # 计算当前位置
                x1, y1 = self.start_pos[0], self.start_pos[1]
                x2, y2 = fireball['target_x'], fireball['target_y']

                fireball['x'] = x1 + (x2 - x1) * fireball['progress']
                fireball['y'] = y1 + (y2 - y1) * fireball['progress']

                # 创建火焰轨迹粒子
                if random.random() < 0.6:
                    color = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0)])
                    particle = Particle(fireball['x'], fireball['y'], color)
                    particle.speed_x = random.uniform(-1, 1)
                    particle.speed_y = random.uniform(-1, 1)
                    particle.size = random.uniform(2, 4)
                    fireball['particles'].append(particle)

                # 更新粒子
                for particle in fireball['particles'][:]:
                    if not particle.update():
                        fireball['particles'].remove(particle)

                # 检查是否击中
                if fireball['progress'] >= 1:
                    self.create_explosion(fireball['x'], fireball['y'])
                    fireball['exploded'] = True

                    # 创建减益效果指示器
                    if self.debuff_indicator is None:
                        self.debuff_indicator = {
                            'x': fireball['target_x'],
                            'y': fireball['target_y'],
                            'timer': 0,
                            'max_timer': 60  # 持续1秒（假设60FPS）
                        }

        # 更新爆炸效果
        for explosion in self.explosions[:]:
            explosion['timer'] += 1
            explosion['radius'] += 0.5
            if explosion['timer'] > explosion['duration']:
                self.explosions.remove(explosion)

        # 更新减益指示器
        if self.debuff_indicator:
            self.debuff_indicator['timer'] += 1

    def create_explosion(self, x, y):
        self.explosions.append({
            'x': x,
            'y': y,
            'radius': 10,
            'max_radius': 40,
            'timer': 0,
            'duration': 30,
            'particles': []
        })

        # 创建爆炸粒子
        for _ in range(25):
            color = random.choice([(255, 100, 0), (255, 150, 0), (255, 50, 0)])
            particle = Particle(x, y, color)
            particle.speed_x = random.uniform(-4, 4)
            particle.speed_y = random.uniform(-4, 4)
            particle.size = random.uniform(3, 6)
            particle.life = random.randint(20, 40)
            particle.max_life = particle.life
            self.explosions[-1]['particles'].append(particle)

    def draw(self, surface):
        # 绘制飞行中的火球
        for fireball in self.fireballs:
            if not fireball['exploded']:
                # 绘制火球
                size = 10
                pygame.draw.circle(surface, (255, 200, 0),
                                   (int(fireball['x']), int(fireball['y'])), size)
                pygame.draw.circle(surface, (255, 100, 0),
                                   (int(fireball['x']), int(fireball['y'])), size - 3)

                # 绘制火焰光环
                for i in range(2):
                    radius = size + i * 4
                    alpha = 150 - i * 50
                    temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surface, (255, 150, 0, alpha),
                                       (radius, radius), radius)
                    surface.blit(temp_surface, (int(fireball['x'] - radius), int(fireball['y'] - radius)))

                # 绘制轨迹粒子
                for particle in fireball['particles']:
                    particle.draw(surface)

        # 绘制爆炸效果
        for explosion in self.explosions:
            progress = explosion['timer'] / explosion['duration']
            radius = explosion['radius'] + (explosion['max_radius'] - explosion['radius']) * progress

            # 绘制爆炸光晕
            alpha = int(255 * (1 - progress))
            temp_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (255, 150, 0, alpha),
                               (int(radius), int(radius)), int(radius))
            surface.blit(temp_surface, (int(explosion['x'] - radius), int(explosion['y'] - radius)))

            # 绘制爆炸粒子
            for particle in explosion['particles']:
                particle.draw(surface)

            # 绘制伤害数字
            if progress < 0.5:
                font = pygame.font.Font(None, 32)
                text = font.render("40", True, (255, 100, 0))
                surface.blit(text, (explosion['x'] - 12, explosion['y'] - 50))

        # 绘制减益效果指示器
        if self.debuff_indicator and self.debuff_indicator['timer'] < self.debuff_indicator['max_timer']:
            x, y = self.debuff_indicator['x'], self.debuff_indicator['y']
            timer = self.debuff_indicator['timer']
            max_timer = self.debuff_indicator['max_timer']

            # 绘制减益光环
            alpha = int(255 * (1 - timer / max_timer))
            radius = 25 + math.sin(timer * 0.2) * 5  # 脉动效果

            temp_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (255, 100, 0, alpha),
                               (int(radius), int(radius)), int(radius), 3)
            surface.blit(temp_surface, (int(x - radius), int(y - radius)))

            # 绘制减益图标（向下的箭头）
            arrow_alpha = int(200 * (1 - timer / max_timer))
            arrow_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.polygon(arrow_surface, (255, 50, 0, arrow_alpha),
                                [(10, 5), (5, 15), (15, 15)])
            pygame.draw.line(arrow_surface, (255, 50, 0, arrow_alpha),
                             (10, 15), (10, 18), 2)
            surface.blit(arrow_surface, (x - 10, y - 10))

            # 绘制减益文字
            if timer < max_timer * 0.8:
                font = pygame.font.Font(None, 18)
                text = font.render("-8", True, (255, 100, 0))
                surface.blit(text, (x - 8, y - 35))

    def is_done(self):
        return all(fireball['exploded'] for fireball in self.fireballs) and \
            len(self.explosions) == 0 and \
            (self.debuff_indicator is None or self.debuff_indicator['timer'] >= self.debuff_indicator['max_timer'])


class ShieldEffect:
    """防御屏障特效"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.max_radius = 35
        self.angle = 0
        self.hexagons = []
        self.particles = []
        self.life = 90  # 持续1.5秒
        self.max_life = self.life
        self.create_hexagons()

    def create_hexagons(self):
        """创建六边形护盾段"""
        num_sides = 6
        for i in range(num_sides):
            angle = (i / num_sides) * math.pi * 2
            self.hexagons.append({
                'angle': angle,
                'distance': random.uniform(0.8, 1.2),
                'pulse_offset': random.uniform(0, math.pi * 2),
                'particles': []
            })

    def update(self):
        self.angle += 0.03
        self.life -= 1

        # 更新六边形位置和粒子
        for hexagon in self.hexagons:
            hexagon['pulse_offset'] += 0.1
            pulse = math.sin(hexagon['pulse_offset']) * 0.2 + 0.8

            # 创建护盾粒子
            if random.random() < 0.2 and self.life > 30:
                angle = hexagon['angle'] + self.angle
                distance = self.radius * hexagon['distance'] * pulse
                px = self.x + math.cos(angle) * distance
                py = self.y + math.sin(angle) * distance

                particle = Particle(px, py, (100, 200, 255))
                particle.speed_x = math.cos(angle + math.pi / 2) * 0.5
                particle.speed_y = math.sin(angle + math.pi / 2) * 0.5
                particle.size = random.uniform(2, 4)
                particle.life = random.randint(20, 40)
                particle.max_life = particle.life
                hexagon['particles'].append(particle)

            # 更新粒子
            for particle in hexagon['particles'][:]:
                if not particle.update():
                    hexagon['particles'].remove(particle)

        # 创建中心粒子
        if random.random() < 0.3 and self.life > 20:
            particle = Particle(self.x, self.y, (150, 220, 255))
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 2)
            particle.speed_x = math.cos(angle) * speed
            particle.speed_y = math.sin(angle) * speed
            particle.size = random.uniform(1, 3)
            particle.life = random.randint(15, 30)
            particle.max_life = particle.life
            self.particles.append(particle)

        # 更新中心粒子
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))

            # 绘制六边形护盾
            for hexagon in self.hexagons:
                pulse = math.sin(hexagon['pulse_offset']) * 0.2 + 0.8
                current_radius = self.radius * hexagon['distance'] * pulse
                angle = hexagon['angle'] + self.angle

                # 计算六边形顶点
                points = []
                for i in range(6):
                    vertex_angle = angle + (i / 6) * math.pi * 2
                    vx = self.x + math.cos(vertex_angle) * current_radius
                    vy = self.y + math.sin(vertex_angle) * current_radius
                    points.append((vx, vy))

                # 绘制六边形边框
                if len(points) >= 3:
                    for i in range(6):
                        x1, y1 = points[i]
                        x2, y2 = points[(i + 1) % 6]

                        line_alpha = int(alpha * (0.7 + pulse * 0.3))
                        temp_surface = pygame.Surface((abs(x2 - x1) + 6, abs(y2 - y1) + 6), pygame.SRCALPHA)
                        pygame.draw.line(temp_surface, (100, 200, 255, line_alpha),
                                         (3, 3), (abs(x2 - x1) + 3, abs(y2 - y1) + 3), 4)
                        surface.blit(temp_surface, (min(x1, x2) - 3, min(y1, y2) - 3))

                # 绘制六边形粒子
                for particle in hexagon['particles']:
                    particle.draw(surface)

            # 绘制多层护盾光环
            for i in range(3):
                ring_radius = self.max_radius + i * 8
                ring_alpha = alpha // (2 + i)
                temp_surface = pygame.Surface((int(ring_radius * 2), int(ring_radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (100, 200, 255, ring_alpha),
                                   (int(ring_radius), int(ring_radius)), int(ring_radius), 2)
                surface.blit(temp_surface, (int(self.x - ring_radius), int(self.y - ring_radius)))

            # 绘制中心粒子
            for particle in self.particles:
                particle.draw(surface)

            # 绘制护盾数值
            if self.life > 60:
                font = pygame.font.Font(None, 24)
                text = font.render("+20", True, (100, 200, 255))
                surface.blit(text, (self.x - 15, self.y - 45))

            # 绘制护盾图标（盾牌）
            if self.life > 40:
                icon_alpha = int(200 * (self.life / self.max_life))
                icon_surface = pygame.Surface((25, 25), pygame.SRCALPHA)

                # 绘制盾牌形状
                pygame.draw.polygon(icon_surface, (150, 220, 255, icon_alpha),
                                    [(12, 5), (5, 12), (12, 20), (19, 12)])
                pygame.draw.polygon(icon_surface, (100, 180, 255, icon_alpha),
                                    [(12, 5), (5, 12), (12, 20), (19, 12)], 2)
                surface.blit(icon_surface, (self.x - 12, self.y - 12))

    def is_done(self):
        return self.life <= 0


class UltimateEffect:
    """大招特效"""

    def __init__(self, x, y, is_player1=True):
        self.x = x
        self.y = y
        self.is_player1 = is_player1
        self.main_color = (255, 100, 100) if is_player1 else (100, 100, 255)  # 红色/蓝色
        self.secondary_color = (255, 200, 100) if is_player1 else (100, 200, 255)
        self.phase = 0  # 0:蓄力, 1:释放, 2:爆炸, 3:治疗
        self.timer = 0
        self.charge_particles = []
        self.explosion_particles = []
        self.heal_particles = []
        self.energy_lines = []

    def update(self):
        self.timer += 1

        if self.phase == 0:  # 蓄力阶段
            # 创建蓄力粒子
            if random.random() < 0.5:
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(30, 60)
                px = self.x + math.cos(angle) * distance
                py = self.y + math.sin(angle) * distance

                particle = Particle(px, py, self.secondary_color)
                # 粒子向中心移动
                dx = self.x - px
                dy = self.y - py
                dist = max(0.1, math.sqrt(dx * dx + dy * dy))
                particle.speed_x = (dx / dist) * 2
                particle.speed_y = (dy / dist) * 2
                particle.size = random.uniform(3, 6)
                particle.life = random.randint(30, 50)
                particle.max_life = particle.life
                self.charge_particles.append(particle)

            # 创建能量线
            if self.timer % 3 == 0:
                angle = random.uniform(0, math.pi * 2)
                start_x = self.x + math.cos(angle) * 80
                start_y = self.y + math.sin(angle) * 80
                self.energy_lines.append({
                    'start': (start_x, start_y),
                    'end': (self.x, self.y),
                    'progress': 0,
                    'speed': random.uniform(0.05, 0.1)
                })

            # 更新能量线
            for line in self.energy_lines[:]:
                line['progress'] += line['speed']
                if line['progress'] >= 1:
                    self.energy_lines.remove(line)

            if self.timer > 60:  # 蓄力1秒后进入释放阶段
                self.phase = 1
                self.timer = 0

        elif self.phase == 1:  # 释放阶段
            # 创建爆炸粒子
            if self.timer < 30:
                for _ in range(5):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(5, 10)
                    particle = Particle(self.x, self.y, self.main_color)
                    particle.speed_x = math.cos(angle) * speed
                    particle.speed_y = math.sin(angle) * speed
                    particle.size = random.uniform(4, 8)
                    particle.life = random.randint(40, 60)
                    particle.max_life = particle.life
                    self.explosion_particles.append(particle)

            if self.timer > 30:  # 0.5秒后进入治疗阶段
                self.phase = 2
                self.timer = 0

        elif self.phase == 2:  # 治疗阶段
            # 创建治疗粒子
            if self.timer < 30:
                heal_color = (100, 255, 100) if self.is_player1 else (100, 255, 200)
                for _ in range(3):
                    angle = random.uniform(0, math.pi * 2)
                    distance = random.uniform(20, 40)
                    px = self.x + math.cos(angle) * distance
                    py = self.y + math.sin(angle) * distance

                    particle = Particle(px, py, heal_color)
                    # 粒子向中心移动（治疗回流）
                    dx = self.x - px
                    dy = self.y - py
                    dist = max(0.1, math.sqrt(dx * dx + dy * dy))
                    particle.speed_x = (dx / dist) * 1.5
                    particle.speed_y = (dy / dist) * 1.5
                    particle.size = random.uniform(3, 5)
                    particle.life = random.randint(30, 50)
                    particle.max_life = particle.life
                    self.heal_particles.append(particle)

        # 更新所有粒子
        for particle in self.charge_particles[:] + self.explosion_particles[:] + self.heal_particles[:]:
            if not particle.update():
                if particle in self.charge_particles:
                    self.charge_particles.remove(particle)
                elif particle in self.explosion_particles:
                    self.explosion_particles.remove(particle)
                else:
                    self.heal_particles.remove(particle)

    def draw(self, surface):
        if self.phase == 0:  # 蓄力阶段
            # 绘制蓄力光环
            pulse = math.sin(self.timer * 0.1) * 0.2 + 0.8
            radius = 50 * pulse
            alpha = 150

            # 多层光环
            for i in range(3):
                ring_radius = radius + i * 15
                ring_alpha = alpha - i * 40
                temp_surface = pygame.Surface((int(ring_radius * 2), int(ring_radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (*self.secondary_color, ring_alpha),
                                   (int(ring_radius), int(ring_radius)), int(ring_radius), 3)
                surface.blit(temp_surface, (int(self.x - ring_radius), int(self.y - ring_radius)))

            # 绘制能量线
            for line in self.energy_lines:
                progress = line['progress']
                current_x = line['start'][0] + (line['end'][0] - line['start'][0]) * progress
                current_y = line['start'][1] + (line['end'][1] - line['start'][1]) * progress

                line_alpha = int(255 * (1 - progress))
                temp_surface = pygame.Surface((abs(current_x - line['start'][0]) + 4,
                                               abs(current_y - line['start'][1]) + 4), pygame.SRCALPHA)
                pygame.draw.line(temp_surface, (*self.main_color, line_alpha),
                                 (2, 2), (abs(current_x - line['start'][0]) + 2, abs(current_y - line['start'][1]) + 2),
                                 2)
                surface.blit(temp_surface, (min(current_x, line['start'][0]) - 2,
                                            min(current_y, line['start'][1]) - 2))

            # 绘制蓄力粒子
            for particle in self.charge_particles:
                particle.draw(surface)

            # 绘制蓄力文字
            font = pygame.font.Font(None, 28)
            text = font.render("蓄力中...", True, self.secondary_color)
            surface.blit(text, (self.x - 40, self.y - 80))

        elif self.phase == 1:  # 释放阶段
            # 绘制爆炸冲击波
            radius = self.timer * 3
            alpha = max(0, 255 - self.timer * 8)

            temp_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (*self.main_color, alpha),
                               (int(radius), int(radius)), int(radius))
            surface.blit(temp_surface, (int(self.x - radius), int(self.y - radius)))

            # 绘制爆炸粒子
            for particle in self.explosion_particles:
                particle.draw(surface)

            # 绘制伤害数字
            if self.timer < 30:
                font = pygame.font.Font(None, 36)
                text = font.render("90", True, self.main_color)
                text_shadow = font.render("90", True, (255, 255, 255))
                surface.blit(text_shadow, (self.x - 16, self.y - 55))
                surface.blit(text, (self.x - 18, self.y - 57))

        elif self.phase == 2:  # 治疗阶段
            # 绘制治疗光环
            radius = 30 + math.sin(self.timer * 0.2) * 10
            alpha = 200 - self.timer * 6

            temp_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (100, 255, 100, alpha),
                               (int(radius), int(radius)), int(radius))
            surface.blit(temp_surface, (int(self.x - radius), int(self.y - radius)))

            # 绘制治疗粒子
            for particle in self.heal_particles:
                particle.draw(surface)

            # 绘制治疗数字
            if self.timer < 30:
                font = pygame.font.Font(None, 28)
                text = font.render("+20", True, (100, 255, 100))
                surface.blit(text, (self.x - 15, self.y + 40))

        # 绘制大招图标（能量核心）
        core_size = 15 + math.sin(self.timer * 0.2) * 5
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(core_size))
        pygame.draw.circle(surface, self.main_color, (int(self.x), int(self.y)), int(core_size - 3))

    def is_done(self):
        return self.phase == 2 and self.timer > 60  # 治疗阶段持续1秒后结束