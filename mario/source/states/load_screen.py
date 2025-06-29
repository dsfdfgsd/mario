import pygame
from .. import constants as C
from ..components import info
from .. import tools


class LoadScreen:
    def start(self, game_info):
        self.game_info = game_info
        self.finished = False
        self.next = 'level'
        self.duration = 2000
        self.timer = 0
        self.info = info.Info('load_screen', self.game_info)

    def update(self, surface, keys):
        self.draw(surface)
        if self.timer == 0:
            self.timer = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - self.timer > 2000:
            self.finished = True
            self.timer = 0


    def draw(self, surface):
        surface.fill((0, 0, 0))
        self.info.draw(surface)

class GameOver(LoadScreen):
    def start(self, game_info):
        """游戏结束场景初始化方法"""
        self.game_info = game_info    # 继承游戏数据
        self.finished = False         # 场景未完成标记
        self.next = 'main_menu'       # 下一场景为主菜单
        self.duration = 4000          # 场景持续4秒(毫秒)
        self.timer = 0                # 场景计时器清零
        self.info = info.Info('game_over', self.game_info)

