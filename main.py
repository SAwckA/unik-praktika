import pygame
import sys
from config import *
from collections import defaultdict

from pygame.rect import Rect


class TextObject:
    def __init__(self,
                 x,
                 y,
                 text_func,
                 color,
                 font_name,
                 font_size):
        self.space = "menu"
        self.pos = (x, y)
        self.text_func = text_func
        self.color = color
        self.font = pygame.font.SysFont(font_name, font_size)
        self.bounds = self.get_surface(text_func())

    def draw(self, surface, centralized=False, pos=None):
        text_surface, self.bounds = \
            self.get_surface(self.text_func())
        if centralized:
            pos = (self.pos[0] - self.bounds.width // 2,
                   self.pos[1])
        else:
            if pos is None:
                pos = self.pos
            else:
                pos = pos
        surface.blit(text_surface, pos)

    def get_surface(self, text):
        text_surface = self.font.render(text,
                                        False,
                                        self.color)
        return text_surface, text_surface.get_rect()

    def update(self):
        pass


class GameObject:
    def __init__(self, x, y, w, h, speed=(0, 0)):
        self.bounds = Rect(x, y, w, h)
        self.speed = speed
        self.space = "game"

    @property
    def left(self):
        return self.bounds.left

    @property
    def right(self):
        return self.bounds.right

    @property
    def top(self):
        return self.bounds.top

    @property
    def bottom(self):
        return self.bounds.bottom

    @property
    def width(self):
        return self.bounds.width

    @property
    def height(self):
        return self.bounds.height

    @property
    def center(self):
        return self.bounds.center

    @property
    def centerx(self):
        return self.bounds.centerx

    @property
    def centery(self):
        return self.bounds.centery

    def draw(self, surface):
        pass

    def move(self, dx, dy):
        self.bounds = self.bounds.move(dx, dy)

    def update(self):
        if self.speed == [0, 0]:
            return

        self.move(*self.speed)


class Game:
    def __init__(self,
                 caption: str,
                 width: int,
                 height: int,
                 # back_image_filename,
                 frame_rate: int):
        self.width = width
        self.height = height
        self.background_image = \
            pygame.image.load(BACKGROUND_IMAGE)
        self.frame_rate = frame_rate
        self.game_over = False
        self.objects = []
        self.pause = False
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.keydown_handlers = defaultdict(list)
        self.keyup_handlers = defaultdict(list)
        self.mouse_handlers: list[callable] = []

    def update(self):
        for o in self.objects:
            if self.pause and o.space != 'menu':
                continue
            if isinstance(o, Unit):
                if o.life <= 0:
                    self.remove_object(o)
            o.update()

    def draw(self):
        for o in self.objects:
            if self.pause and o.space != 'menu':
                continue
            o.draw(self.surface)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                for handler in self.keydown_handlers[event.key]:
                    handler(event.key)
            elif event.type == pygame.KEYUP:
                for handler in self.keydown_handlers[event.key]:
                    handler(event.key)
            elif event.type in (pygame.MOUSEBUTTONDOWN,
                                pygame.MOUSEBUTTONUP,
                                pygame.MOUSEMOTION):
                for handler in self.mouse_handlers:
                    handler(event.type, event.pos)

    def append_object(self, obj: object):
        self.objects.append(obj)

    def append_mouse_handler(self, handler: callable):
        self.mouse_handlers.append(handler)

    def remove_object(self, obj: object):
        try:
            self.objects.remove(obj)

        except Exception as e:
            print(e)

    def run(self):
        while not self.game_over:
            self.surface.blit(self.background_image, (0, 0))

            self.handle_events()
            self.update()
            self.draw()

            pygame.display.update()
            self.clock.tick(self.frame_rate)


class Button(GameObject):
    def __init__(self,
                 x,
                 y,
                 w,
                 h,
                 text,
                 on_click=lambda x: None,
                 font_size: int = FONT_SIZE,
                 padding=0):
        super().__init__(x, y, w, h)
        self.state = 'normal'
        self.on_click = on_click
        self.space = "menu"
        self.text = TextObject(x + padding,
                               y + padding, lambda: text,
                               BUTTON_TEXT_COLOR,
                               FONT_NAME,
                               font_size)

    def draw(self, surface):
        pygame.draw.rect(surface,
                         self.back_color,
                         self.bounds)
        self.text.draw(surface)

    @property
    def back_color(self):
        return dict(normal=BUTTON_NORMAL_COLOR,
                    hover=BUTTON_HOVER_COLOR,
                    pressed=BUTTON_PRESSED_COLOR)[self.state]

    def handle_mouse_event(self, type_, pos):
        if type_ == pygame.MOUSEMOTION:
            self.handle_mouse_move(pos)
        elif type_ == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_down(pos)
        elif type_ == pygame.MOUSEBUTTONUP:
            self.handle_mouse_up(pos)

    def handle_mouse_move(self, pos):
        if self.bounds.collidepoint(pos):
            if self.state != 'pressed':
                self.state = 'hover'
        else:
            self.state = 'normal'

    def handle_mouse_down(self, pos):
        if self.bounds.collidepoint(pos):
            self.state = 'pressed'

    def handle_mouse_up(self, _):
        if self.state == 'pressed':
            self.on_click(self)
            self.state = 'hover'


class Ground(pygame.sprite.Sprite):

    def __init__(self, x):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/gound.png')
        self.rect = self.image.get_rect(center=(x, 680))
        self.space = "game"

    def draw(self, sc):
        sc.blit(self.image, self.rect)


class Unit(pygame.sprite.Sprite):
    def __init__(self,
                 image,
                 life,
                 scale_size: tuple,
                 move_speed=1,
                 xpos=100,
                 attack_range=10,
                 side='right',
                 damage=1.0):

        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image)
        self.scaled_image = pygame.transform.scale(self.image, scale_size)
        self.rect = self.scaled_image.get_rect(center=(xpos, 590))
        self.movex = move_speed
        self.life = life
        self.space = 'game'
        self.state = 'walk'
        self.hp_bar = TextObject(xpos, 590 - 100, self.get_life_text, COLORS.BLACK, 'Arial Bold', 20)
        self.scale_size = scale_size
        self.attack_range = attack_range
        self.side = side
        self.target = None
        self.damage = damage

    @property
    def hit_box_rect(self):
        return pygame.rect.Rect(*self.hit_box)

    @property
    def attack_box_rect(self):
        return pygame.rect.Rect(*self.attack_box)

    @property
    def hit_box(self):
        return self.rect.x, self.rect.y, *self.scale_size

    @property
    def attack_box(self):
        end_x, end_y = self.scale_size
        start_x = self.rect.x
        match self.side:
            case 'right':
                start_x -= self.attack_range
                end_x += self.attack_range
            case 'left':
                end_x += self.attack_range

        return start_x, self.rect.y, end_x, end_y

    def get_life_text(self):
        return f'HP: {to_fixed(self.life, 1)}'

    def draw(self, sc: pygame.surface.Surface):
        sc.blit(self.scaled_image, self.rect)

        if SHOW_DEBUG_BOXES:
            pygame.draw.rect(sc, (255, 0, 0), self.attack_box, 4)
            pygame.draw.rect(sc, (0, 255, 0), self.hit_box, 2)

        self.hp_bar.draw(sc, pos=(30 + self.rect.x, 590 - 100))

    def update(self, *args, **kwargs) -> None:
        self.hp_bar.update()
        if self.target is not None:
            self.target.life -= self.damage
            if self.target.life <= 0:
                self.target = None
        if self.target is None:
            self.state = 'walk'
        if self.state == 'walk':
            self.rect.x = self.rect.x + self.movex


class Warrior(Unit):
    def __init__(self, team):
        match team:
            case 'ally':
                image = 'img/Warrior.png'
                super().__init__(image, 100, (100, 150), side='left', attack_range=10)
            case 'enemy':
                image = 'img/Warrior_enemy.png'
                super().__init__(image, 100, (100, 150), move_speed=-1, xpos=1180, side='right', attack_range=10)
        self.team = team


class Ranger(Unit):
    def __init__(self, team):
        match team:
            case 'ally':
                image = 'img/Ranger.png'
                super().__init__(image, 70, (100, 150),
                                 side='left',
                                 attack_range=300,
                                 damage=0.3)
            case 'enemy':
                image = 'img/Ranger_enemy.png'
                super().__init__(image, 100, (100, 150),
                                 move_speed=-1,
                                 xpos=1180,
                                 side='right',
                                 attack_range=300,
                                 damage=0.3)
        self.team = team


class Town(Unit):
    def __init__(self, team):
        self.team = team
        image = 'img/Town.webp'

        match team:
            case 'ally':
                super().__init__(image, 100, (200, 250), move_speed=0, xpos=50, side='left', attack_range=0)
            case 'enemy':
                super().__init__(image, 100, (200, 250), move_speed=0, xpos=1280 - 50, side='right', attack_range=0)


class TheBATE(Game):

    def __init__(self, caption, width, height, fps):
        super().__init__(caption=caption, width=width, height=height, frame_rate=fps)
        self.cooldown: dict = {}
        self.reset_cooldown()
        self.enemy_town = None
        self.ally_town = None

    def reset_cooldown(self):
        self.cooldown = dict(
            warrior=0,
            ranger=0,
            tank=0
        )

    def update_cooldown(self):
        if self.pause is False:
            for T, value in self.cooldown.items():
                if value <= 0:
                    continue

                self.cooldown[T] -= 1

    def handle_box_collisions(self):
        for issuer in self.objects:
            if not isinstance(issuer, Unit):
                continue
            for consumer in self.objects:
                if consumer == issuer or not isinstance(consumer, Unit):
                    continue
                if consumer.team == issuer.team:  # noqa
                    continue

                collide = issuer.attack_box_rect.colliderect(consumer.hit_box_rect)
                if collide:
                    issuer.state = 'fight'
                    if issuer.target is None:
                        issuer.target = consumer

    def show_win_message(self):
        self.enemy_town = None
        self.ally_town = None
        main_menu_btn = Button(self.width // 2 - 20 * 16, self.height // 2 - 6 * 9, 40 * 16, 12 * 9,
                               'ПОБЕДА!', on_click=self.show_menu, font_size=102)
        self.objects.insert(0, main_menu_btn)
        self.mouse_handlers.insert(0, main_menu_btn.handle_mouse_event)

    def show_lose_message(self):
        self.enemy_town = None
        self.ally_town = None
        main_menu_btn = Button(self.width // 2 - 20 * 16, self.height // 2 - 6 * 9, 40 * 16, 12 * 9,
                               'ПОРАЖЕНИЕ!', on_click=self.show_menu, font_size=102)
        self.objects.insert(0, main_menu_btn)
        self.mouse_handlers.insert(0, main_menu_btn.handle_mouse_event)

    def update(self):
        self.handle_box_collisions()
        self.update_cooldown()

        if self.enemy_town is not None and self.ally_town is not None:
            if self.enemy_town.life <= 0:
                self.show_win_message()
                self.pause = True
                return

            if self.ally_town.life <= 0:
                self.show_lose_message()
                self.pause = True
                return

        for o in self.objects:
            if self.pause and o.space != 'menu':
                continue
            if isinstance(o, Unit):
                if o.life <= 0:
                    self.remove_object(o)
            o.update()

    def switch_pause(self, _=None):
        self.pause = not self.pause

    def display_pause_menu(self, obj: Button):
        print(self.objects, obj)
        self.objects.remove(obj)
        self.mouse_handlers.remove(obj.handle_mouse_event)
        self.pause = True
        main_menu_btn = Button(self.width // 2 - 16 * 10, self.height // 2 - 9 * 5, 16 * 20, 9 * 10,
                               'Главное меню', on_click=self.show_menu)
        self.objects.insert(0, main_menu_btn)
        self.mouse_handlers.insert(0, main_menu_btn.handle_mouse_event)

        resume_btn = Button(self.width // 2 - 16 * 10, self.height // 2 + 9 * 5 + 10, 16 * 20, 9 * 10,
                            'Продолжить', on_click=self.resume_game)
        self.objects.insert(0, resume_btn)
        self.mouse_handlers.insert(0, resume_btn.handle_mouse_event)

    def resume_game(self, obj: Button):
        self.pause = False
        self.objects.remove(obj)
        self.objects.pop(0)
        self.mouse_handlers.remove(obj.handle_mouse_event)
        self.mouse_handlers.pop(0)

        pause_btn = Button(1170, 10, 100, 100, 'II', padding=100 // 2 - FONT_SIZE, font_size=72,
                           on_click=self.display_pause_menu)
        self.objects.append(pause_btn)
        self.mouse_handlers.append(pause_btn.handle_mouse_event)

    def start_game(self, _=None):
        self.reset_cooldown()
        self.pause = False
        self.objects = []
        self.mouse_handlers = []
        self.objects.append(Ground(self.width // 2))
        pause_btn = Button(1170, 10, 100, 100, 'II', padding=100 // 2 - FONT_SIZE, font_size=72,
                           on_click=self.display_pause_menu)

        warrior_btn = Button(10, 10, 100, 100, 'W 10', font_size=72, on_click=self.spawn_warrior)
        self.append_object(warrior_btn)
        self.append_mouse_handler(warrior_btn.handle_mouse_event)

        ranger_btn = Button(120, 10, 100, 100, 'R 5', font_size=72, on_click=self.spawn_ranger)
        self.append_object(ranger_btn)
        self.append_mouse_handler(ranger_btn.handle_mouse_event)

        self.ally_town = Town('ally')
        self.append_object(self.ally_town)

        self.enemy_town = Town('enemy')
        self.append_object(self.enemy_town)

        self.objects.append(pause_btn)
        self.mouse_handlers.append(pause_btn.handle_mouse_event)

    def set_global_cooldown(self):
        for T, value in self.cooldown.items():
            if self.cooldown[T] >= 30 * 1:
                continue
            self.cooldown[T] = 30 * 2

    def spawn_warrior(self, _, team='ally'):
        if self.cooldown["warrior"] > 0:
            return

        warrior = Warrior(team)
        self.cooldown["warrior"] = 30 * 3
        self.append_object(warrior)

        warrior = Ranger('enemy')
        self.append_object(warrior)

        self.set_global_cooldown()

    def spawn_ranger(self, _, team='ally'):

        if self.cooldown["ranger"] > 0:
            return

        ranger = Ranger(team)
        self.cooldown["ranger"] = 30 * 3
        self.append_object(ranger)

        ranger = Warrior('enemy')
        self.append_object(ranger)

        self.set_global_cooldown()

    def stop_game(self, _=None):
        self.game_over = True

    def show_menu(self, _=None):
        self.objects = []
        self.mouse_handlers = []
        start_btn = Button(100, 100, 250, 100, 'Start', padding=100 // 2 - FONT_SIZE, on_click=self.start_game)
        exit_btn = Button(100, 210, 250, 100, 'Exit', padding=100 // 2 - FONT_SIZE, on_click=self.stop_game)
        self.objects.append(start_btn)
        self.objects.append(exit_btn)

        self.mouse_handlers.append(start_btn.handle_mouse_event)
        self.mouse_handlers.append(exit_btn.handle_mouse_event)


if __name__ == "__main__":
    game = TheBATE("THE B.A.T.E", 1280, 720, 30)
    game.show_menu()
    game.run()
