import os
import sys
import pygame as pg

from constant import WATER_KILL, WATER_DOOR, FIRE_KILL, FIRE_DOOR, ELEVATOR_DIS_ACTIEVE, ELEVATOT_ACTIVATE, \
    LEVEL_ARM_ACTIVATE, ELEVATOR_SPEED, BTN_CONST_OPEN, BTN_CONST_CLOSE, SPEED_CONST, JUMP_HEIGHT, MAX_ANIM_COUNT, \
    MIN_ANIM_COUNT, STEP_ANIM_COUNT, RIGHT, LEFT, NO, BEFORE, AFTER, DURING

pg.init()
flag = True
door_water = False
door_fire = False
elevator_is_actieve = False
level_arm_is_actieve = False
player_update = True
new_lvl_count = 1

clock = pg.time.Clock()


class Player(pg.sprite.Sprite):
    def __init__(self, pos_x, pos_y, img, group, const_kill, const_door, group_liq, group_door, cris_group,
                 walk_right, walk_left, btn_left, btn_right, btn_up):
        super().__init__(group, all_sprites)
        self.group = group
        self.img = img
        self.btn_left = btn_left
        self.btn_right = btn_right
        self.btn_up = btn_up
        self.walk_right = walk_right
        self.walk_left = walk_left
        self.cris_group = cris_group
        self.group_liq = group_liq
        self.group_door = group_door
        self.const_kill = const_kill
        self.const_door = const_door
        self.image = player_images[img]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.want_jump = False
        self.jump_count = JUMP_HEIGHT
        self.anim_count = MIN_ANIM_COUNT
        self.speed = SPEED_CONST
        self.last_move = RIGHT
        self.before_jump_sprites_pol = []
        self.state = BEFORE

    def update(self, *args, **kwargs):
        if pg.sprite.spritecollideany(self, self.cris_group):
            for c in self.cris_group:
                if pg.sprite.collide_mask(self, c):
                    c.image = images['dark']
        if pg.sprite.spritecollideany(self, self.group_liq):
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.const_kill}))
        if pg.sprite.spritecollideany(self, self.group_door):
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.const_door}))
        if pg.sprite.spritecollideany(self, door_group):
            self.is_move = False
        keys = pg.key.get_pressed()
        if keys[self.btn_left]:
            if self.rect.x - self.speed >= 0:
                self.rect.x -= self.speed
                self.last_move = LEFT
        elif keys[self.btn_right]:
            if self.rect.x + self.speed < WIDTH - self.rect.width:
                self.rect.x += self.speed
                self.last_move = RIGHT
        else:
            self.last_move = NO
            self.anim_count = MIN_ANIM_COUNT
        if self.state == BEFORE:
            if keys[self.btn_up]:
                self.want_jump = True
        else:
            if self.jump_count >= -JUMP_HEIGHT and self.state != AFTER:
                if self.jump_count <= 0:
                    self.rect.y += (self.jump_count ** 2) // 3
                else:
                    self.rect.y -= (self.jump_count ** 2) // 3
                self.jump_count -= 1
            else:
                self.want_jump = False
                self.jump_count = JUMP_HEIGHT
                self.state = BEFORE
        if self.want_jump:
            self.before_jump_sprites_pol = []
            for s in pg.sprite.spritecollide(self, all_sprites, False):
                if s.rect.y >= self.rect.y + (self.rect.height // 2):
                    self.before_jump_sprites_pol.append(s)
            self.state = DURING
            self.want_jump = False
        if self.state == DURING:
            for t in pg.sprite.spritecollide(self, tiles_light_group, False):
                if t not in self.before_jump_sprites_pol:
                    self.state = AFTER
        pol = []
        for s in pg.sprite.spritecollide(self, tiles_light_group, False):
            if s.rect.y >= self.rect.y + (self.rect.height // 2):
                pol.append(s)
        if not pol and self.state != DURING:
            self.rect.y += 5
        if self.anim_count + 1 >= MAX_ANIM_COUNT:
            self.anim_count = MIN_ANIM_COUNT
        if self.last_move == LEFT:
            self.image = self.walk_left[self.anim_count // 5]
            self.anim_count += STEP_ANIM_COUNT
        elif self.last_move == RIGHT:
            self.image = self.walk_right[self.anim_count // 5]
            self.anim_count += STEP_ANIM_COUNT
        else:
            self.image = player_images[self.img]
        screen.blit(self.image, (self.rect.x, self.rect.y))


class FixedObject(pg.sprite.Sprite):
    def __init__(self, pos_x, pos_y, img, group):
        super().__init__(group, all_sprites)
        self.image = images[img]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Tile(FixedObject):
    def __init__(self, pos_x, pos_y, img, group):
        super().__init__(pos_x, pos_y, img, group)
        if pos_y % 2 == 0:
            self.rect = self.image.get_rect().move(
                tile_width * pos_x, tile_height * pos_y)
        else:
            self.rect = self.image.get_rect().move(
                tile_width * pos_x - tile_width // 2, tile_height * pos_y)


class Cristal(FixedObject):
    def __init__(self, pos_x, pos_y, img, group):
        super().__init__(pos_x, pos_y, img, group)
        self.mask = pg.mask.from_surface(self.image)


class Button(FixedObject):
    def __init__(self, pos_x, pos_y, img, group, const_open, const_close):
        super().__init__(pos_x, pos_y, img, group)
        self.const_open = const_open
        self.mask = pg.mask.from_surface(self.image)
        self.is_pushed = False
        self.const_close = const_close

    def update(self, *args, **kwargs) -> None:
        if pg.sprite.spritecollideany(self, water_group) \
                or pg.sprite.spritecollideany(self, fire_group):
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.const_open}))
            self.is_pushed = True
        else:
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.const_close}))


class Door(FixedObject):
    def __init__(self, pos_x, pos_y, img, group):
        super().__init__(pos_x, pos_y, img, group)
        self.x = tile_width * pos_x + tile_width // 4
        self.y = tile_height * pos_y

    def update(self, open) -> None:
        if open:
            self.rect.y = -45
        else:
            checking = 0
            for b in btns_group:
                if b.is_pushed:
                    checking += 1
            if checking == 2:
                self.rect.x = self.x
                self.rect.y = self.y
                for b in btns_group:
                    b.is_pushed = False


class LevelArm(FixedObject):
    def __init__(self, pos_x, pos_y, img, group, active_elev, active_la):
        super().__init__(pos_x, pos_y, img, group)
        self.active_elev = active_elev
        self.active_la = active_la
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + tile_width // 4, tile_height * pos_y)
        self.is_active = False
        self.mask = pg.mask.from_surface(self.image)

    def update(self):
        if (pg.sprite.spritecollideany(self, water_group) or
            pg.sprite.spritecollideany(self, fire_group)):
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.active_la}))
            self.is_active = True
        else:
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.active_elev}))
        if self.is_active:
            self.image = images['rl']
        else:
            self.image = images['rr']


class Elevator(FixedObject):
    def __init__(self, pos_x, pos_y, img, group, speed, dis_act_const):
        super().__init__(pos_x, pos_y, img, group)
        self.speed = speed
        self.p = None
        self.dis_act_const = dis_act_const
        self.mask = pg.mask.from_surface(self.image)

    def update(self, actieve) -> None:
        if not actieve:
            return
        if self.rect.y == 4 * tile_height:
            pg.event.post(pg.event.Event(pg.USEREVENT, {'data': self.dis_act_const}))

        if pg.sprite.spritecollideany(self, water_group):
            for w in water_group:
                if pg.sprite.collide_mask(self, w) and self.p is None:
                    self.p = w
        if pg.sprite.spritecollideany(self, fire_group):
            for f in fire_group:
                if pg.sprite.collide_mask(self, f):
                    self.p = f

        self.rect.y -= self.speed
        self.p.rect.y -= self.speed


def load_image(name, colorkey=None):
    fullname = os.path.join('img', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pg.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image

def terminate():
    pg.quit()
    sys.exit()

def load_level(filename):
    if new_lvl_count > 3:
        return
    filename = "levels/" + filename + str(new_lvl_count)
    if not os.path.isfile(filename):
        print(f"Файл '{filename}' не найден")
        sys.exit()
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))

def generate_level(level):
    x, y = None, None
    w = f = None
    y_cf = x_cf = y_cw = x_cw = x_dw = y_dw = None
    x_df = y_df = x_w = y_w = x_f = y_f = None
    x_wl = x_fl = x_wc = x_fc = x_wr = x_fr = None
    y_wl = y_fl = y_wc = y_fc = y_wr = y_fr = None
    x_b1 = x_b2 = y_b1 = y_b2 = x_d = y_d = None
    x_e = y_e = x_la = y_la = None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Tile(x, y, 'light', tiles_light_group)
            elif level[y][x] == '.':
                Tile(x, y, 'dark', tiles_dark_group)
            elif level[y][x] == '@':
                Tile(x, y, 'dark', tiles_dark_group)
                x_w = x
                y_w = y
            elif level[y][x] == '%':
                Tile(x, y, 'dark', tiles_dark_group)
                x_f = x
                y_f = y
            elif level[y][x] == '(':
                Tile(x, y, 'dark', tiles_dark_group)
                x_df = x
                y_df = y
            elif level[y][x] == ')':
                Tile(x, y, 'dark', tiles_dark_group)
                x_dw = x
                y_dw = y
            elif level[y][x] == ':':
                Tile(x, y, 'dark', tiles_dark_group)
                x_cw = x
                y_cw = y
            elif level[y][x] == ';':
                Tile(x, y, 'dark', tiles_dark_group)
                x_cf = x
                y_cf = y
            elif level[y][x] == '1':
                Tile(x, y, 'light', tiles_light_group)
                x_wl = x
                y_wl = y
            elif level[y][x] == '4':
                Tile(x, y, 'light', tiles_light_group)
                x_fl = x
                y_fl = y
            elif level[y][x] == '2':
                Tile(x, y, 'light', tiles_light_group)
                x_wc = x
                y_wc = y
            elif level[y][x] == '5':
                Tile(x, y, 'light', tiles_light_group)
                x_fc = x
                y_fc = y
            elif level[y][x] == '3':
                Tile(x, y, 'light', tiles_light_group)
                x_wr = x
                y_wr = y
            elif level[y][x] == '6':
                Tile(x, y, 'light', tiles_light_group)
                x_fr = x
                y_fr = y
            elif level[y][x] == '+':
                Tile(x, y, 'light', tiles_light_group)
                if x_b1 is None:
                    x_b1 = x
                    y_b1 = y
                else:
                    x_b2 = x
                    y_b2 = y
            elif level[y][x] == '$':
                Tile(x, y, 'dark', tiles_dark_group)
                x_d = x
                y_d = y
            elif level[y][x] == '*':
                Tile(x, y, 'dark', tiles_dark_group)
                x_e = x
                y_e = y
            elif level[y][x] == '^':
                Tile(x, y, 'dark', tiles_dark_group)
                x_la = x
                y_la = y
    FixedObject(x_df, y_df, 'f_door', door_fire_group)
    FixedObject(x_dw, y_dw, 'w_door', door_water_group)
    if x_wl is not None:
        FixedObject(x_wl, y_wl, 'w_l', liq_water_group)
    if x_fl is not None:
        FixedObject(x_fl, y_fl, 'f_l', liq_fire_group)
    if x_wc is not None:
        FixedObject(x_wc, y_wc, 'w_c', liq_water_group)
    if x_fc is not None:
        FixedObject(x_fc, y_fc, 'f_c', liq_fire_group)
    if x_wr is not None:
        FixedObject(x_wr, y_wr, 'w_r', liq_water_group)
    if x_fr is not None:
        FixedObject(x_fr, y_fr, 'f_r', liq_fire_group)
    if x_cf is not None:
        Cristal(x_cf, y_cf, 'f_cris', cris_fire_group)
    if x_cw is not None:
        Cristal(x_cw, y_cw, 'w_cris', cris_water_group)
    if x_b1 is not None:
        Button(x_b1, y_b1, 'btn', btns_group, BTN_CONST_OPEN, BTN_CONST_CLOSE)
    if x_b2 is not None:
        Button(x_b2, y_b2, 'btn', btns_group, BTN_CONST_OPEN, BTN_CONST_CLOSE)
    if x_d is not None:
        Door(x_d, y_d, 'door', door_group)
    if x_e is not None:
        Elevator(x_e, y_e, 'el', elevator_group, ELEVATOR_SPEED, ELEVATOR_DIS_ACTIEVE)
    if x_la is not None:
        LevelArm(x_la, y_la, 'rr', level_arm_group, ELEVATOT_ACTIVATE, LEVEL_ARM_ACTIVATE)
    w = Player(x_w, y_w, 'girl', water_group, WATER_KILL, WATER_DOOR, liq_fire_group, door_water_group, cris_water_group,
               water_walk_images_right, water_walk_images_left, pg.K_a, pg.K_d, pg.K_w)
    f = Player(x_f, y_f, 'boy', fire_group, FIRE_KILL, FIRE_DOOR, liq_water_group, door_fire_group, cris_fire_group,
               fire_walk_images_right, fire_walk_images_left, pg.K_LEFT, pg.K_RIGHT, pg.K_UP)
    return w, f, x, y

def draw():
    screen.fill((0, 0, 0))
    all_sprites.draw(screen)

def game_over(img):
    screen.fill((0, 0, 0))
    for s in all_sprites:
        s.kill()
    img = images[img]
    fon = pg.transform.scale(img, (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))

def intro():
    intro_text = ["Игра Огонь и Вода", 'Чтобы перейти к игре нажмите', 'на любую клавишу мыши, ',
                  'вода управдяется клавишами', 'asdw, огонь - стрелками', 'Цель игры - дойти до двери',
                  'своего цвета.', 'Персонаж не должен касаться', 'жидкости не своего цвета']
    fon = pg.transform.scale(load_image('fon1.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pg.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pg.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

def start_screen(flag, door_fire, door_water):
    global new_lvl_count, elevator_is_actieve, level_arm_is_actieve, player_update
    intro()
    while True:
        pg.time.delay(10)
        if new_lvl_count > 3:
            game_over('win')
            new_lvl_count = 1
        for event in pg.event.get():
            if event.type == pg.QUIT:
                terminate()
            if event.type == pg.USEREVENT:
                if event.data == WATER_KILL:
                    flag = True
                    door_water = False
                    door_fire = False
                    game_over('fall')
                elif event.data == FIRE_KILL:
                    door_water = False
                    door_fire = False
                    flag = True
                    game_over('fall')
                elif event.data == WATER_DOOR:
                    door_water = True
                elif event.data == FIRE_DOOR:
                    door_fire = True
                elif event.data == LEVEL_ARM_ACTIVATE:
                    level_arm_is_actieve = True
                elif event.data == ELEVATOT_ACTIVATE and level_arm_is_actieve:
                    elevator_is_actieve = True
                    player_update = False
                elif event.data == ELEVATOR_DIS_ACTIEVE:
                    player_update = True
                    elevator_is_actieve = False
                    level_arm_is_actieve = False
                elif event.data == BTN_CONST_OPEN:
                    door_group.update(True)
                elif event.data == BTN_CONST_CLOSE:
                    if not pg.sprite.spritecollideany(water, btns_group) \
                            and not pg.sprite.spritecollideany(fire, btns_group):
                        door_group.update(False)
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_DOWN or event.key == pg.K_UP or event.key == pg.K_LEFT \
                        or event.key == pg.K_RIGHT:
                    fire_group.update()
                elif event.key == pg.K_a or event.key == pg.K_s \
                        or event.key == pg.K_d or event.key == pg.K_w:
                    water_group.update()
            if event.type == pg.MOUSEBUTTONDOWN:
                water, fire, level_x, level_y = generate_level(load_level('map'))
                flag = False
            if door_water and door_fire:
                door_water = False
                door_fire = False
                new_lvl_count += 1
                screen.fill((0, 0, 0))
                flag = True
                for s in all_sprites:
                    s.kill()
                game_over('game_over')
        if not flag:
            draw()
        if player_update:
            fire_group.update()
            water_group.update()
        btns_group.update()
        level_arm_group.update()
        elevator_group.update(elevator_is_actieve)
        pg.display.flip()
        clock.tick(FPS)

FPS = 50
WIDTH = HEIGHT = 350
size = (WIDTH, HEIGHT)
water, fire = None, None
all_sprites = pg.sprite.Group()
tiles_light_group = pg.sprite.Group()
tiles_dark_group = pg.sprite.Group()
door_fire_group = pg.sprite.Group()
door_water_group = pg.sprite.Group()
water_group = pg.sprite.Group()
fire_group = pg.sprite.Group()
liq_water_group = pg.sprite.Group()
liq_fire_group = pg.sprite.Group()
cris_water_group = pg.sprite.Group()
cris_fire_group = pg.sprite.Group()
liq_group = pg.sprite.Group()
btns_group = pg.sprite.Group()
door_group = pg.sprite.Group()
elevator_group = pg.sprite.Group()
level_arm_group = pg.sprite.Group()
pg.init()
screen = pg.display.set_mode(size)

player_images = {'girl': load_image('girl.png'), 'boy': load_image('boy.png')}
fire_walk_images_right = [load_image('boy-r1.png'), load_image('boy-r2.png')]
fire_walk_images_left = [load_image('boy-l1.png'), load_image('boy-l2.png')]
water_walk_images_right = [load_image('girl-r1.png'), load_image('girl-r2.png')]
water_walk_images_left = [load_image('girl-l1.png'), load_image('girl-l2.png')]

images = {'w_door': load_image('door-g.png'), 'f_door': load_image('door-b.png'),
          'w_r': load_image('b-w-r.png'), 'w_c': load_image('b-w-c.png'),
          'w_l': load_image('b-w-l.png'), 'f_r': load_image('r-w-r.png'),
          'f_c': load_image('r-w-c.png'), 'f_l': load_image('r-w-l.png'),
          'door': load_image('door.png'), 'btn': load_image('btn.png'),
          'el': load_image('elev.png'), 'rr': load_image('sw-r-2.png'),
          'rl': load_image('sw-l-2.png'), 'game_over': load_image('fon.jpg'),
          'fall': load_image('game-over.png'), 'win': load_image('win.jpg'),
          'w_cris': load_image('blue-diam.png'), 'f_cris': load_image('red-diam.png'),
          'light': load_image('break-light.png'), 'dark': load_image('break-dark.png')}
tile_width = 40
tile_height = 20
start_screen(flag, door_fire, door_water)
pg.quit()