import sys, time, random, math, pygame
from pygame.locals import *


class MySprite(pygame.sprite.Sprite):
    def __init__(self, target):
        pygame.sprite.Sprite.__init__(self)  # extend the base Sprite class
        self.master_image = None
        self.frame = 0
        self.old_frame = -1
        self.frame_width = 1
        self.frame_height = 1
        self.first_frame = 0
        self.last_frame = 0
        self.columns = 1
        self.last_time = 0
        self.image = None  # 初始化image属性

    # X property
    def _getx(self):
        return self.rect.x

    def _setx(self, value):
        self.rect.x = value

    X = property(_getx, _setx)

    # Y property
    def _gety(self):
        return self.rect.y

    def _sety(self, value):
        self.rect.y = value

    Y = property(_gety, _sety)

    # position property
    def _getpos(self):
        return self.rect.topleft

    def _setpos(self, pos):
        self.rect.topleft = pos

    position = property(_getpos, _setpos)

    def load(self, filename, width, height, columns):
        try:
            self.master_image = pygame.image.load(filename).convert_alpha()
            self.frame_width = width
            self.frame_height = height
            self.rect = Rect(0, 0, width, height)
            self.columns = columns

            # 计算总帧数
            rect = self.master_image.get_rect()
            total_frames = (rect.width // width) * (rect.height // height)
            self.last_frame = max(total_frames - 1, 0)

            # 初始图像
            self.update_frame()

        except Exception as e:
            print(f"Error loading {filename}: {e}")
            # 创建一个替代图像
            self.master_image = pygame.Surface((width, height))
            self.master_image.fill((255, 0, 255))  # 品红色表示错误
            self.rect = Rect(0, 0, width, height)
            self.image = self.master_image

    def update_frame(self):
        """安全地更新当前帧的图像"""
        if self.master_image is None:
            return

        image_width, image_height = self.master_image.get_size()

        # 确保frame在合法范围内
        if self.frame < self.first_frame:
            self.frame = self.first_frame
        if self.frame > self.last_frame:
            self.frame = self.last_frame

        # 计算帧位置
        frame_x = (self.frame % self.columns) * self.frame_width
        frame_y = (self.frame // self.columns) * self.frame_height

        # 检查边界
        if (frame_x + self.frame_width > image_width or
                frame_y + self.frame_height > image_height):
            # 如果超出边界，使用第一帧
            frame_x = 0
            frame_y = 0
            self.frame = self.first_frame

        # 创建子表面
        rect = pygame.Rect(frame_x, frame_y, self.frame_width, self.frame_height)
        try:
            self.image = self.master_image.subsurface(rect)
            self.old_frame = self.frame
        except:
            # 如果失败，使用整个图像
            self.image = self.master_image

    def update(self, current_time, rate=30):
        # 更新动画帧
        if current_time > self.last_time + rate:
            self.frame += 1
            if self.frame > self.last_frame:
                self.frame = self.first_frame
            self.last_time = current_time

        # 如果帧改变了，更新图像
        if self.frame != self.old_frame:
            self.update_frame()


def print_text(font, x, y, text, color=(255, 255, 255)):
    imgText = font.render(text, True, color)
    screen.blit(imgText, (x, y))


def reset_arrow():
    y = random.randint(250, 350)
    arrow.position = 800, y

# 初始化游戏
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Escape Dragon")
font = pygame.font.Font(None, 18)
framerate = pygame.time.Clock()

# 加载背景
try:
    bg = pygame.image.load('bg.png').convert_alpha()
except:
    bg = pygame.Surface((800, 600))
    bg.fill((0, 100, 200))  # 蓝色背景

group = pygame.sprite.Group()

# 创建龙精灵
dragon = MySprite(screen)
dragon.load("left.png", 260, 150, 3)
dragon.position = 100, 230
group.add(dragon)

# 创建玩家精灵
player = MySprite(screen)
player.load("right.png", 50, 64, 8)
player.first_frame = 1
player.last_frame = 7
player.position = 400, 303
group.add(player)

# 创建箭精灵
arrow = MySprite(screen)
arrow.load("flame.png", 40, 16, 1)
arrow.position = 800, 320
group.add(arrow)

# 游戏变量
arrow_vel = 8.0
game_over = False
you_win = False
player_jumping = False
jump_vel = 0.0
player_start_y = player.Y

# 主游戏循环
while True:
    framerate.tick(30)
    ticks = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()
    elif keys[pygame.K_SPACE]:
        if not player_jumping:
            player_jumping = True
            jump_vel = -8.0

    if not game_over:
        arrow.X -= arrow_vel
        if arrow.X < 40:
            reset_arrow()

    if pygame.sprite.collide_rect(arrow, player):
        reset_arrow()
        player.X -= 10

    if pygame.sprite.collide_rect(arrow, dragon):
        reset_arrow()
        dragon.X -= 10

    if pygame.sprite.collide_rect(player, dragon):
        game_over = True

    if dragon.X < -100:
        you_win = True
        game_over = True

    if player_jumping:
        player.Y += jump_vel
        jump_vel += 0.5
        if player.Y > player_start_y:
            player_jumping = False
            player.Y = player_start_y
            jump_vel = 0.0

    screen.blit(bg, (0, 0))

    if not game_over:
        group.update(ticks, 50)

    group.draw(screen)

    print_text(font, 350, 360, "Press SPACE to jump!")

    if game_over:
        print_text(font, 360, 100, "G A M E O V E R")
        if you_win:
            print_text(font, 330, 130, "YOU BEAT THE DRAGON")
        else:
            print_text(font, 330, 130, "THE DRAGON GOT YOU")

    pygame.display.update()