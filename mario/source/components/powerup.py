import pygame
from .. import setup, tools
from .. import constants as C

def create_powerup(centerx, centery, type):

    return Fireflower(centerx, centery)

class Powerup(pygame.sprite.Sprite):
    def __init__(self, centerx, centery, frame_rects):
        pygame.sprite.Sprite.__init__(self)

        self.frames = []
        self.frame_index = 0
        for frame_rect in frame_rects:
            self.frames.append(tools.get_image(
                setup.GRAPHICS['item_objects'],
                *frame_rect,
                (0, 0, 0),
                2.5
            ))
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.centerx = centerx
        self.rect.centery = centery
        self.origin_y = centery - self.rect.height/2


        self.x_vel = 0  # 水平速度设为0
        self.direction = 1  # 方向设为1（向右）
        self.y_vel = -1  # 垂直速度设为-1（向上）
        self.gravity = 1  # 重力值设为1
        self.max_y_vel = 8  # 最大垂直速度设为8

    def update_position(self,level):
        self.rect.x += self.x_vel
        self.check_x_collisions(level)
        self.rect.y += self.y_vel
        self.check_y_collisions(level)

        if self.rect.x < 0 or self.rect.y >C.SCREEN_H:
            self.kill()

    def check_x_collisions(self, level):
        sprite = pygame.sprite.spritecollideany(self, level.ground_items_group)

        if sprite:
            if self.direction:  # 向右
                self.direction = 0
                self.rect.right = sprite.rect.left
            else:
                self.direction = 1
                self.rect.left = sprite.rect.right
            self.x_vel *= -1



    def check_y_collisions(self, level):
        check_group = pygame.sprite.Group(level.ground_items_group, level.box_group, level.brick_group)
        sprite = pygame.sprite.spritecollideany(self, check_group)
        if sprite:
            if self.rect.top < sprite.rect.top:
                self.rect.bottom = sprite.rect.top
                self.y_vel = 0
                self.state = 'walk'
        level.check_will_fall(self)


class Mushroom(Powerup):
    def __init__(self, centerx, centery):
        Powerup.__init__(self, centerx, centery, [(0, 0, 16, 16)])
        self.x_vel = 2
        self.state = 'grow'
        self.name = 'mushroom'

    def update(self, level):
        if self.state == 'grow':
            self.rect.y += self.y_vel
            if self.rect.bottom < self.origin_y:
                self.state = 'walk'
        elif self.state == 'walk':
            pass
        elif self.state == 'fall':
            if self.y_vel < self.max_y_vel:
                self.y_vel += self.gravity

        if self.state != 'grow':
            self.update_position(level)


class Fireflower(Powerup):
    """火焰花道具类，继承自基础道具类"""

    def __init__(self, centerx, centery):
        # 动画帧矩形区域定义 (x, y, width, height)
        frame_rects = [
            (0, 32, 16, 16),
            (16, 32, 16, 16),
            (32, 32, 16, 16),
            (48, 32, 16, 16)
        ]
        # 调用父类初始化方法
        Powerup.__init__(self, centerx, centery, frame_rects)

        # 初始化属性
        self.x_vel = 2  # 水平移动速度
        self.state = 'grow'  # 初始状态（生长动画）
        self.name = 'fireflower'  # 道具标识
        self.timer = 0  # 动画计时器
        # self.origin_y = centery  # 记录初始垂直位置

    def update(self, level):
        """每帧更新逻辑"""
        # 生长状态处理
        if self.state == 'grow':
            self.rect.y += self.y_vel
            # 生长到预定高度后切换状态
            if self.rect.bottom < self.origin_y:
                self.state = 'rest'

        # 动画帧更新
        self.current_time = pygame.time.get_ticks()
        if self.timer == 0:
            self.timer = self.current_time
        # 每30毫秒切换一帧
        if self.current_time - self.timer > 30:
            self.frame_index += 1
            self.frame_index %= len(self.frames)
            self.timer = self.current_time
            self.image = self.frames[self.frame_index]


class Fireball(Powerup):
    def __init__(self, centerx, centery, direction):
        frame_rects = [
            (96, 144, 8, 8),
            (104, 144, 8, 8),
            (96, 152, 8, 8),
            (104, 152, 8, 8),  # 旋转
            (112, 144, 16, 16),
            (112, 160, 16, 16),
            (112, 176, 16, 16)  # 爆炸
        ]

        Powerup.__init__(self, centerx, centery, frame_rects)
        self.name = 'fireball'
        self.state = 'fly'
        self.direction = direction
        self.x_vel = 10 if self.direction else -10
        self.y_vel = 10
        self.gravity = 1
        self.timer = 0

    def update(self, level):
        self.current_time = pygame.time.get_ticks()
        if self.state == 'fly':
            self.y_vel += self.gravity
            if self.current_time - self.timer > 200:
                self.frame_index += 1
                self.frame_index %= 4
                self.timer = self.current_time
                self.image = self.frames[self.frame_index]
            self.update_position(level)
        elif self.state == 'boom':
            if self.current_time - self.timer > 50:
                if self.frame_index < 6:
                    self.frame_index += 1
                    self.timer = self.current_time
                    self.image = self.frames[self.frame_index]
                else:
                    self.kill()



    def update_position(self,level):
        self.rect.x += self.x_vel
        self.check_x_collisions(level)
        self.rect.y += self.y_vel
        self.check_y_collisions(level)

        if self.rect.x < 0 or self.rect.y >C.SCREEN_H:
            self.kill()

    def check_x_collisions(self, level):
        sprite = pygame.sprite.spritecollideany(self, level.ground_items_group)

        if sprite:
            self.frame_index = 4
            self.state = 'boom'

    def check_y_collisions(self, level):
        check_group = pygame.sprite.Group(level.ground_items_group, level.box_group, level.brick_group)
        sprite = pygame.sprite.spritecollideany(self, check_group)
        if sprite:
            if self.rect.top < sprite.rect.top:
                self.rect.bottom = sprite.rect.top
                self.y_vel = -10
