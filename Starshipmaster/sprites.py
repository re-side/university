import pygame
import random
from settings import *
from assets import get_asset

class PlayerCharacter(pygame.sprite.Sprite):
    def __init__(self, initial_pos_x, initial_pos_y, world_rect):
        super().__init__()
        self.frames = get_asset('player_frames')
        self.game_world_rect = world_rect
        self.move_speed = 220
        self.anim_speed_ms = 120

        self.walk_anim_r = [self.frames[i] for i in range(PLAYER_WALK_ROW * PLAYER_SPRITESHEET_COLS, (PLAYER_WALK_ROW + 1) * PLAYER_SPRITESHEET_COLS)]
        self.walk_anim_l = [pygame.transform.flip(frame, True, False) for frame in self.walk_anim_r]
        self.idle_anim_r = [self.frames[i] for i in range(PLAYER_IDLE_ROW * PLAYER_SPRITESHEET_COLS, (PLAYER_IDLE_ROW + 1) * PLAYER_SPRITESHEET_COLS)]
        self.idle_anim_l = [pygame.transform.flip(frame, True, False) for frame in self.idle_anim_r]

        # отслеживаем анимации
        self.current_anim_list = self.idle_anim_r
        self.image = self.current_anim_list[0]
        self.rect = self.image.get_rect(center=(initial_pos_x, initial_pos_y))
        
        self.true_x, self.true_y = float(self.rect.x), float(self.rect.y)
        self.is_moving = False
        self.is_facing_right = True
        self.last_anim_update = 0
        self.frame_index = 0
        self.active_repair_system = None
        self.current_tool = None
        self.tool_image = None

        self.footsteps_sound = get_asset('sound_footsteps')
        self.footsteps_channel = pygame.mixer.Channel(0)

    def update(self, dt_sec, game):
    
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if not self.active_repair_system:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071

            self.is_moving = (dx != 0 or dy != 0)
            if dx > 0: self.is_facing_right = True
            elif dx < 0: self.is_facing_right = False

            self.true_x += dx * self.move_speed * dt_sec
            self.true_y += dy * self.move_speed * dt_sec
            self.rect.x = int(self.true_x)
            self.rect.y = int(self.true_y)
            self.rect.clamp_ip(self.game_world_rect)
            self.true_x, self.true_y = float(self.rect.x), float(self.rect.y)
        
        if self.active_repair_system and keys[pygame.K_e]:
            self.work_on_fix(dt_sec)
        
        # вызов
        self._animate()
        self._handle_sounds()

    def _animate(self):
        # логика анимации
        now = pygame.time.get_ticks()
        
        #активный
        new_anim_list = None
        if self.is_moving:
            new_anim_list = self.walk_anim_r if self.is_facing_right else self.walk_anim_l
        else:
            new_anim_list = self.idle_anim_r if self.is_facing_right else self.idle_anim_l

        if new_anim_list != self.current_anim_list:
            self.current_anim_list = new_anim_list
            self.frame_index = 0

        if now - self.last_anim_update > self.anim_speed_ms:
            self.last_anim_update = now
            self.frame_index = (self.frame_index + 1) % len(self.current_anim_list)
            self.image = self.current_anim_list[self.frame_index]

    def _handle_sounds(self):
        if self.footsteps_channel and self.footsteps_sound:
            if self.is_moving and not self.footsteps_channel.get_busy():
                self.footsteps_channel.play(self.footsteps_sound, loops=-1, fade_ms=200)
            elif not self.is_moving and self.footsteps_channel.get_busy():
                self.footsteps_channel.fadeout(200)

    def stop_sounds(self):
         if self.footsteps_channel:
            self.footsteps_channel.stop()

    def start_fixing(self, systems_group, add_msg_func):
        if self.active_repair_system: return
        interaction_rect = self.rect.inflate(30, 30)
        for system in systems_group:
            if interaction_rect.colliderect(system.rect) and system.is_broken:
                if self.current_tool == system.required_tool:
                    self.active_repair_system = system
                    system.start_repair()
                    self.is_moving = False
                else:
                    tool_name = "Гаечный ключ" if system.required_tool == 'wrench' else 'Лейка'
                    add_msg_func(f"Необходим: {tool_name}", UI_WARN_COLOR)
                return

    def equip_tool(self, tool_name):
        self.current_tool = tool_name
        self.tool_image = get_asset(tool_name)
        if self.tool_image:
            self.tool_image = pygame.transform.scale(self.tool_image, (32,32))

    def stop_fixing(self):
        if self.active_repair_system:
            self.active_repair_system.stop_repair()
            self.active_repair_system = None
            
    def work_on_fix(self, dt_sec):
        if self.active_repair_system:
            self.active_repair_system.advance_repair(dt_sec)
            if not self.active_repair_system.is_broken:
                self.active_repair_system = None

class ShipSystem(pygame.sprite.Sprite):
    def __init__(self, x, y, name, system_type, add_msg_func, repair_time):
        super().__init__()
        self.name, self.system_type, self.add_msg_func, self.repair_time = name, system_type, add_msg_func, repair_time
        self.is_broken, self.is_under_repair, self.repair_progress = False, False, 0.0
        self.is_boosted, self.boost_end_time = False, 0
        self.time_to_next_break, self.time_broken_start = self._get_random_break_time(), 0
        
        if self.system_type == "plant":
            self.ok_images = [pygame.transform.scale(img, (50, 50)) for img in get_asset('plants_ok')]
            self.broken_image = pygame.transform.scale(get_asset('plant_broken'), (50, 50))
            self.image, self.required_tool = random.choice(self.ok_images), 'watering_can'
        elif self.system_type == "engine":
            self.ok_image = pygame.transform.scale(get_asset('engine_ok'), (100, 120))
            self.broken_image = self.ok_image.copy()
            self.broken_image.fill((80, 40, 40), special_flags=pygame.BLEND_RGB_MULT)
            self.image, self.required_tool = self.ok_image, 'wrench'
        elif self.system_type == "shield":
            self.ok_image = pygame.transform.scale(get_asset('shield_ok'), (80, 80))
            self.broken_image = self.ok_image.copy()
            self.broken_image.set_alpha(100)
            self.image, self.required_tool = self.ok_image, 'wrench'
            
        self.rect = self.image.get_rect(center=(x, y))
        self.snd_alarm, self.snd_repair_loop, self.snd_repair_done = get_asset('sound_alarm'), get_asset('sound_repair_loop'), get_asset('sound_repair_done')
        if self.snd_repair_loop: self.snd_repair_loop.set_volume(0.6)

    def update(self, dt_sec, game):
        now = pygame.time.get_ticks()
        if self.is_boosted and now > self.boost_end_time:
            self.is_boosted = False
            self.add_msg_func(f"Усиление {self.name} закончилось.", UI_WARN_COLOR)

        if not self.is_broken and not self.is_under_repair:
            self.time_to_next_break -= dt_sec * game.break_time_mod
            if self.time_to_next_break <= 0 and not self.is_boosted:
                self.trigger_breakdown(game)
        elif self.is_broken and self.system_type == "plant" and not self.is_under_repair:
            if (now - self.time_broken_start) / 1000.0 >= game.life_support_time:
                pygame.event.post(pygame.event.Event(LOSE_LIFE_EVENT, {"reason": f"Отказ жизнеобеспечения: {self.name}!"}))
                self.complete_repair(silent=True)

        base_image = self.broken_image if self.is_broken else (getattr(self, 'ok_image', self.image))
        if self.system_type == "plant" and not self.is_broken:
             base_image = self.image #рэнплан
        
        if self.is_boosted and int(now / 200) % 2 == 0:
            boost_overlay = base_image.copy()
            boost_overlay.fill(UI_BOOST_COLOR, special_flags=pygame.BLEND_RGB_ADD)
            self.image = boost_overlay
        else:
            self.image = base_image

    def trigger_breakdown(self, game, forced=False):
        if self.is_broken: return
        self.is_broken = True
        self.add_msg_func(f"ОТКАЗ: {self.name}!", RED)
        # выделканал
        if self.snd_alarm and not game.alarm_channel.get_busy():
            game.alarm_channel.play(self.snd_alarm)
        if self.system_type == "plant":
            self.time_broken_start = pygame.time.get_ticks()
        if not forced:
            self.time_to_next_break = self._get_random_break_time()
            
    def _get_random_break_time(self):
        multiplier = 2.0 if self.system_type != 'plant' else 1.0
        return random.uniform(BASE_MIN_TIME_BETWEEN_BREAKS_SEC * multiplier, BASE_MAX_TIME_BETWEEN_BREAKS_SEC * multiplier)

    def boost(self, duration_ms):
        if not self.is_broken:
            self.is_boosted = True
            self.boost_end_time = pygame.time.get_ticks() + duration_ms
            self.add_msg_func(f"Система {self.name} усилена!", UI_BOOST_COLOR)

    def start_repair(self):
        self.is_under_repair = True
        self.repair_progress = 0.0
        if self.snd_repair_loop: self.snd_repair_loop.play(loops=-1)
        
    def stop_repair(self):
        self.is_under_repair = False
        if self.snd_repair_loop: self.snd_repair_loop.stop()

    def advance_repair(self, dt_sec):
        if self.is_under_repair:
            self.repair_progress += dt_sec / self.repair_time
        if self.repair_progress >= 1.0:
            self.complete_repair()

    def complete_repair(self, silent=False):
        self.is_broken, self.is_under_repair, self.repair_progress = False, False, 0.0
        self.time_broken_start, self.time_to_next_break = 0, self._get_random_break_time()
        if self.snd_repair_loop: self.snd_repair_loop.stop()
        if not silent:
            self.add_msg_func(f"ПОЧИНЕНО: {self.name}!", GREEN)
            if self.snd_repair_done: self.snd_repair_done.play()
        if self.system_type == "plant":
            self.image = random.choice(self.ok_images)
        elif hasattr(self, 'ok_image'):
            self.image = self.ok_image

class Toolbox(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(get_asset('toolbox'), (64, 50))
        self.rect = self.image.get_rect(center=(x,y))
    def update(self, dt_sec, game):
        pass

class ComputerTerminal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image_orig = pygame.transform.scale(get_asset('terminal'), (50, 70))
        self.image = self.image_orig
        self.rect = self.image.get_rect(center=(x, y))
        self.cooldown = 30 * 1000
        self.last_use_time = -self.cooldown

    def update(self, dt_sec, game):
        now = pygame.time.get_ticks()
        if now < self.last_use_time + self.cooldown:
            self.image = self.image_orig.copy()
            self.image.fill((80,80,80), special_flags=pygame.BLEND_RGB_MULT)
        else:
            self.image = self.image_orig

    def use(self, systems, add_msg_func):
        now = pygame.time.get_ticks()
        if now > self.last_use_time + self.cooldown:
            working_systems = [s for s in systems if not s.is_broken and not s.is_boosted]
            if not working_systems:
                add_msg_func("Нет доступных систем для усиления.", UI_WARN_COLOR)
                return False

            target = next((s for s in working_systems if s.system_type == 'shield'), None) or \
                     next((s for s in working_systems if s.system_type == 'engine'), None) or \
                     random.choice([s for s in working_systems if s.system_type == 'plant'] or [None])
                     
            if target:
                target.boost(15 * 1000)
                self.last_use_time = now
                return True
        else:
            cooldown_left = (self.last_use_time + self.cooldown - now) / 1000
            add_msg_func(f"Терминал на перезарядке... {int(cooldown_left)}с", UI_WARN_COLOR)

        return False

class ReactorCore(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image_orig = pygame.transform.scale(get_asset('reactor_core'), (64, 64))
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.is_overloaded, self.overload_end_time, self.time_to_meltdown = False, 0, 0
    
    def update(self, dt_sec, game):
        if self.is_overloaded:
            self.time_to_meltdown -= dt_sec
            if int(pygame.time.get_ticks() / 150) % 2 == 0:
                self.image = self.image_orig.copy()
                self.image.fill(RED, special_flags=pygame.BLEND_RGB_ADD)
            else:
                self.image = self.image_orig
                
            if self.time_to_meltdown <= 0:
                game.add_message("РАСПЛАВЛЕНИЕ РЕАКТОРА!", RED)
                pygame.event.post(pygame.event.Event(LOSE_LIFE_EVENT, {"reason": "Расплавление реактора!"}))
                pygame.event.post(pygame.event.Event(LOSE_LIFE_EVENT, {"reason": "Расплавление реактора!"}))
                self.stabilize() # Стабилизируем, чтобы не спамить событием
    
    def trigger_overload(self, duration_sec, meltdown_sec):
        if self.is_overloaded: return
        self.is_overloaded = True
        self.time_to_meltdown = float(meltdown_sec)
    
    def stabilize(self):
        self.is_overloaded = False
        self.image = self.image_orig.copy()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, world_w, world_h):
        super().__init__()
        self.image_orig = pygame.transform.scale(get_asset('meteor'), (40, 55))
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'left': self.pos = pygame.math.Vector2(-100, random.randrange(0, world_h))
        elif edge == 'right': self.pos = pygame.math.Vector2(world_w + 100, random.randrange(0, world_h))
        elif edge == 'top': self.pos = pygame.math.Vector2(random.randrange(0, world_w), -100)
        else: self.pos = pygame.math.Vector2(random.randrange(0, world_w), world_h + 100)
        
        target_pos = pygame.math.Vector2(random.randrange(world_w // 4, world_w * 3 // 4), random.randrange(world_h // 4, world_h * 3 // 4))
        self.velocity = (target_pos - self.pos).normalize()
        self.angle = self.velocity.angle_to(pygame.math.Vector2(0, -1))
        self.image = pygame.transform.rotate(self.image_orig, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.world_w, self.world_h = world_w, world_h

    def update(self, dt_sec, game):
        self.pos += self.velocity * METEOR_SPEED_PIX_PER_SEC * dt_sec
        self.rect.center = self.pos
        if not self.rect.colliderect(pygame.Rect(-200, -200, self.world_w + 400, self.world_h + 400)):
            self.kill()

class SmokeEffect(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.frames = get_asset('smoke_frames')
        self.anim_speed_ms = 100
        self.last_update = pygame.time.get_ticks()
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
    
    def update(self, dt_sec, game):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.anim_speed_ms:
            self.last_update = now
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.frames[self.frame_index]
                self.rect = self.image.get_rect(center=center)

class StarParticle(pygame.sprite.Sprite):
    def __init__(self, screen_w, screen_h):
        super().__init__()
        size = random.randint(1, 3)
        self.image = pygame.Surface((size, size))
        self.image.fill(tuple(random.randint(100, 200) for _ in range(3)))
        self.rect = self.image.get_rect(center=(random.randrange(screen_w), random.randrange(screen_h)))
        self.speed = random.uniform(20, 80)
        self.true_y = float(self.rect.y)
        self.screen_h = screen_h
        self.screen_w = screen_w

    def update(self, dt_sec, is_engine_ok):
        if is_engine_ok:
            self.true_y += self.speed * dt_sec
            self.rect.y = int(self.true_y)
            if self.rect.top > self.screen_h:
                self.true_y = -self.rect.height
                self.rect.x = random.randrange(self.screen_w)