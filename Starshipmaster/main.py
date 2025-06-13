import pygame
import os
import random
from settings import *
from assets import preload_game_assets, get_asset
from camera import GameCamera
from sprites import PlayerCharacter, ShipSystem, StarParticle, Meteor, SmokeEffect, Toolbox, ComputerTerminal, ReactorCore

class EventManager:
    """Управляет случайными кризисными событиями."""
    def __init__(self, game):
        self.game = game
        self.events = [self.crisis_meteor_shower, self.crisis_power_surge, self.crisis_drought, self.crisis_reactor_overload]
        self.time_to_next_crisis = random.randint(30, 45) * 1000
        self.last_crisis_time = pygame.time.get_ticks()
        self.meteor_shower_active = False
        self.meteor_shower_end_time = 0

    def update(self):
        now = pygame.time.get_ticks()
        if self.game.game_state != "playing":
            return

        if now > self.last_crisis_time + self.time_to_next_crisis:
            random.choice(self.events)()
            self.last_crisis_time = now
            self.time_to_next_crisis = random.randint(30, 45) * 1000 * self.game.break_time_mod

        if self.meteor_shower_active and now > self.meteor_shower_end_time:
            self.meteor_shower_active = False
            self.game.next_meteor_spawn_modifier = 1.0
            self.game.add_message("Метеоритный дождь прекратился.", GREEN)

    def crisis_meteor_shower(self):
        self.game.add_message("КРИЗИС: Метеоритный дождь!", UI_WARN_COLOR)
        self.meteor_shower_active = True
        self.meteor_shower_end_time = pygame.time.get_ticks() + 20 * 1000
        self.game.next_meteor_spawn_modifier = 0.2

    def crisis_power_surge(self):
        self.game.add_message("КРИЗИС: Скачок напряжения!", UI_WARN_COLOR)
        core_systems = [s for s in self.game.all_systems if s.system_type in ['engine', 'shield'] and not s.is_broken]
        if core_systems:
            random.choice(core_systems).trigger_breakdown(self.game, forced=True)

    def crisis_drought(self):
        self.game.add_message("КРИЗИС: Засуха в оранжерее!", UI_WARN_COLOR)
        for system in self.game.all_systems:
            if system.system_type == 'plant' and not system.is_broken:
                system.trigger_breakdown(self.game, forced=True)
                
    def crisis_reactor_overload(self):
        if self.game.difficulty == 'easy' or self.game.reactor.is_overloaded:
            return
        self.game.add_message("КРИЗИС: Перегрузка реактора!", RED)
        self.game.reactor.trigger_overload(duration_sec=20, meltdown_sec=15)
        self.game.screen_shake = SCREEN_SHAKE_INTENSITY * 2

class Game:
    def __init__(self):
        pygame.init()
        # стабильная инициализация звука
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16) # Увеличим каналов на всякий случай

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Космический Аврал")
        self.clock = self.clock = pygame.time.Clock()
        self.is_running = True
        self.game_state = "menu"
        self.load_assets()
        
        self.menu_stars = pygame.sprite.Group()
        for _ in range(150):
            self.menu_stars.add(StarParticle(WIDTH, HEIGHT))
        
        self.current_music_path = None
        
        # Выделяем канал для тревоги, чтобы она не спамила
        self.alarm_channel = pygame.mixer.Channel(5)

        self.play_music('menu')

    def load_assets(self):
        preload_game_assets()
        self.font_small = pygame.font.Font(None, 28)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_large = pygame.font.Font(None, 72)
        self.bg_image = get_asset('ship_interior')
        self.world_rect = self.bg_image.get_rect(topleft=(0,0))
        self.ship_mask = pygame.mask.from_surface(self.bg_image, 128)
        self.tool_icons = {
            'wrench': pygame.transform.scale(get_asset('wrench'), (32, 32)),
            'watering_can': pygame.transform.scale(get_asset('watering_can'), (32, 32))
        }
        self.heart_full_img = pygame.transform.scale(get_asset('heart_full'), (32, 32))
        self.heart_empty_img = pygame.transform.scale(get_asset('heart_empty'), (32, 32))
        self.fog_surface = pygame.Surface((WIDTH, HEIGHT))
        self.fog_surface.fill(BLACK)
        self.fog_surface.set_colorkey(WHITE)

    def start_new_game(self, difficulty):
        self.difficulty = difficulty
        if difficulty == 'easy':
            params = (BASE_GAME_DURATION_SECONDS + 60, BASE_PLAYER_LIVES + 1, BASE_REPAIR_TIME_SECONDS - 0.5, BASE_LIFE_SUPPORT_CRITICAL_TIME_SEC + 10, 1.5, 1.5)
            self.play_music('normal')
        elif difficulty == 'hard':
            params = (BASE_GAME_DURATION_SECONDS - 30, BASE_PLAYER_LIVES - 1, BASE_REPAIR_TIME_SECONDS + 0.5, BASE_LIFE_SUPPORT_CRITICAL_TIME_SEC - 5, 0.7, 0.8)
            self.play_music('hard')
        else: # normal
            params = (BASE_GAME_DURATION_SECONDS, BASE_PLAYER_LIVES, BASE_REPAIR_TIME_SECONDS, BASE_LIFE_SUPPORT_CRITICAL_TIME_SEC, 1.0, 1.0)
            self.play_music('normal')
            
        self.game_duration, self.player_lives, self.repair_time, self.life_support_time, self.meteor_spawn_mod, self.break_time_mod = params

        self.all_sprites = pygame.sprite.Group()
        self.drawable_sprites = pygame.sprite.Group()
        self.systems = pygame.sprite.Group()
        self.stars = pygame.sprite.Group()
        self.meteors = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()

        self.camera = GameCamera(self.world_rect.width, self.world_rect.height)
        self.player = PlayerCharacter(self.world_rect.centerx, self.world_rect.centery, self.world_rect)
        
        self.toolbox = Toolbox(650, 520)
        self.engine = ShipSystem(800, 400, "Двигатель", "engine", self.add_message, self.repair_time)
        self.shield = ShipSystem(545, 170, "Щиты", "shield", self.add_message, self.repair_time)
        self.plant1 = ShipSystem(50, 300, "Ферма Альфа", "plant", self.add_message, self.repair_time)
        self.plant2 = ShipSystem(180, 300, "Ферма Бета", "plant", self.add_message, self.repair_time)
        self.terminal = ComputerTerminal(470, 290)
        self.reactor = ReactorCore(835, 310)
        
        self.all_systems = [self.engine, self.shield, self.plant1, self.plant2]
        
        self.all_sprites.add(self.player, self.toolbox, self.terminal, self.reactor, *self.all_systems)
        self.drawable_sprites.add(self.player, self.toolbox, self.terminal, self.reactor, *self.all_systems)
        self.systems.add(*self.all_systems)

        for _ in range(150): self.stars.add(StarParticle(WIDTH, HEIGHT))
        
        self.messages, self.game_over_reason, self.game_start_time = [], "", pygame.time.get_ticks()
        self.event_manager = EventManager(self)
        self.next_meteor_spawn_modifier = 1.0
        self.schedule_next_meteor()
        self.screen_shake = 0
        self.game_state = "playing"

    def schedule_next_meteor(self):
        min_t, max_t = BASE_METEOR_SPAWN_MIN_SEC, BASE_METEOR_SPAWN_MAX_SEC
        modifier = self.meteor_spawn_mod * self.next_meteor_spawn_modifier
        self.next_meteor_spawn = pygame.time.get_ticks() + random.randint(int(min_t*1000*modifier), int(max_t*1000*modifier))

    def play_music(self, track_name):
        music_path = get_asset(f'music_{track_name}')
        if pygame.mixer.music.get_busy() and self.current_music_path == music_path:
            return
        if music_path:
            pygame.mixer.music.fadeout(1000)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(loops=-1, fade_ms=1000)
            self.current_music_path = music_path
        else:
            self.current_music_path = None

    def run(self):
        while self.is_running:
            self.dt_sec = self.clock.tick(FPS) / 1000.0
            
            state_handler_method_name = f"handle_{self.game_state}_state"
            state_handler = getattr(self, state_handler_method_name, self.handle_menu_state)
            state_handler()
            
            pygame.display.flip()

    def handle_menu_state(self):
        self.handle_menu_events()
        self.menu_stars.update(self.dt_sec, True)
        self.draw_menu()

    def handle_playing_state(self):
        self.handle_game_events()
        self.update_game()
        self.draw_game()

    def handle_game_over_state(self):
        self.handle_end_screen_events()
        self.draw_game(final_frame=True)
        self.draw_end_screen("КОРАБЛЬ УНИЧТОЖЕН", self.game_over_reason, RED)
        
    def handle_victory_state(self):
        self.handle_end_screen_events()
        self.draw_game(final_frame=True)
        self.draw_end_screen("ВЫ СПАСЕНЫ!", "Команда эвакуации прибыла.", GREEN)

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.start_new_game('easy')
                if event.key == pygame.K_2: self.start_new_game('normal')
                if event.key == pygame.K_3: self.start_new_game('hard')

    def handle_game_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.game_state = "menu"; self.play_music('menu'); self.player.stop_sounds()
                if event.key == pygame.K_e: self.player.start_fixing(self.systems, self.add_message)
                if self.player.rect.colliderect(self.toolbox.rect.inflate(40,40)):
                    if event.key == pygame.K_1: self.player.equip_tool('wrench'); self.add_message("Взят гаечный ключ", WHITE)
                    if event.key == pygame.K_2: self.player.equip_tool('watering_can'); self.add_message("Взята лейка", WHITE)
                if self.player.rect.colliderect(self.terminal.rect.inflate(40,40)) and event.key == pygame.K_f:
                    if self.terminal.use(self.systems, self.add_message): 
                        sound = get_asset('sound_terminal_use')
                        if sound: sound.play()
                if self.reactor.is_overloaded and self.player.rect.colliderect(self.reactor.rect.inflate(40,40)) and event.key == pygame.K_f:
                    self.reactor.stabilize(); self.add_message("Реактор стабилизирован!", GREEN); self.screen_shake = 0
            if event.type == pygame.KEYUP and event.key == pygame.K_e:
                self.player.stop_fixing()
            if event.type == LOSE_LIFE_EVENT:
                self.lose_life(event.reason)

    def handle_end_screen_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.is_running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.game_state = "menu"; self.play_music('menu')

    def update_game(self):
        now = pygame.time.get_ticks()
        
        self.all_sprites.update(self.dt_sec, self)
        self.stars.update(self.dt_sec, not self.engine.is_broken)
        self.effects.update(self.dt_sec, self)
        
        self.camera.update_camera(self.player.rect)
        self.event_manager.update()

        if now > self.next_meteor_spawn:
            meteor = Meteor(self.world_rect.width, self.world_rect.height)
            self.all_sprites.add(meteor)
            self.drawable_sprites.add(meteor)
            self.meteors.add(meteor)
            self.schedule_next_meteor()

        for meteor in self.meteors:
            offset_x, offset_y = meteor.rect.left - self.world_rect.left, meteor.rect.top - self.world_rect.top
            if self.ship_mask.overlap(meteor.mask, (offset_x, offset_y)):
                meteor.kill()
                self.screen_shake = SCREEN_SHAKE_INTENSITY * 3
                sound = get_asset('sound_meteor_hit')
                if sound: sound.play()
                if self.shield.is_boosted:
                    self.add_message("Усиленные щиты отразили удар!", UI_BOOST_COLOR)
                    self.shield.is_boosted = False # Буст сбивается ударом
                elif not self.shield.is_broken:
                    self.shield.trigger_breakdown(self, forced=True)
                else:
                    self.add_message("Метеорит попал в корпус!", RED)
                    pygame.event.post(pygame.event.Event(LOSE_LIFE_EVENT, {"reason": "Прямое попадание метеорита!"}))

        if self.engine.is_broken and random.random() < 0.1 * self.dt_sec * 60:
            smoke = SmokeEffect(self.engine.rect.center)
            self.effects.add(smoke)

        if self.screen_shake > 0: self.screen_shake -= 1

        if (now - self.game_start_time) / 1000.0 >= self.game_duration:
            self.victory()

    def draw_game(self, final_frame=False):
        self.screen.fill(BLACK)
        self.stars.draw(self.screen)
        
        render_offset = [random.randint(-self.screen_shake, self.screen_shake) for _ in range(2)] if self.screen_shake > 0 else (0,0)
        self.screen.blit(self.bg_image, self.camera.apply_to_rect(self.world_rect.move(render_offset)))
        
        for sprite in sorted(self.drawable_sprites, key=lambda s: s.rect.bottom):
            # Рисуем тень
            shadow_rect = pygame.Rect(0, 0, sprite.rect.width * 0.7, 10)
            shadow_rect.midbottom = sprite.rect.midbottom
            shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0,0,0,90), (0,0, *shadow_rect.size))
            self.screen.blit(shadow_surf, self.camera.apply_to_rect(shadow_rect.move(render_offset)))
            # Рисуем спрайт
            self.screen.blit(sprite.image, self.camera.apply_to_rect(sprite.rect.move(render_offset)))
            
        for effect in self.effects:
             self.screen.blit(effect.image, self.camera.apply_to_rect(effect.rect.move(render_offset)))
             
        #
        self.fog_surface.fill(BLACK)
        player_screen_pos = self.camera.apply_to_rect(self.player.rect).center
        pygame.draw.circle(self.fog_surface, WHITE, player_screen_pos, FOG_OF_WAR_RADIUS)
        self.screen.blit(self.fog_surface, (0,0))
        
        if not final_frame:
            self.draw_system_helpers()
            self.draw_ui()

    def draw_menu(self):
        self.screen.fill(BLACK)
        self.menu_stars.draw(self.screen)
        self.draw_text("Космический Аврал", self.font_large, UI_WARN_COLOR, WIDTH // 2, HEIGHT // 4)
        self.draw_text("Выберите сложность:", self.font_medium, WHITE, WIDTH // 2, HEIGHT // 2 - 50)
        self.draw_text("[1] Легко", self.font_medium, GREEN, WIDTH // 2, HEIGHT // 2 + 20)
        self.draw_text("[2] Нормально", self.font_medium, WHITE, WIDTH // 2, HEIGHT // 2 + 80)
        self.draw_text("[3] Сложно", self.font_medium, RED, WIDTH // 2, HEIGHT // 2 + 140)
        self.draw_text("Нажмите ESC для выхода", self.font_small, GRAY, WIDTH // 2, HEIGHT - 50)
        
    def draw_ui(self):
        time_left = max(0, self.game_duration - (pygame.time.get_ticks() - self.game_start_time) / 1000.0)
        self.draw_text(f"Эвакуация: {int(time_left // 60):02}:{int(time_left % 60):02}", self.font_medium, TEXT_COLOR, WIDTH // 2, 30, align="center")
        
        for i in range(BASE_PLAYER_LIVES + 1):
            img = self.heart_full_img if i < self.player_lives else self.heart_empty_img
            self.screen.blit(img, (20 + i * (self.heart_full_img.get_width() + 5), 20))

        y_offset, status_list = 20, []
        for system in self.systems:
            if system.is_broken:
                if system.system_type == "plant":
                    time_since_broken = (pygame.time.get_ticks() - system.time_broken_start) / 1000.0
                    critical_time_left = self.life_support_time - time_since_broken
                    if critical_time_left > 0: status_list.append((f"{system.name}: ОТКАЗ ({int(critical_time_left)}с)", UI_WARN_COLOR, 1))
                    else: status_list.append((f"{system.name}: ОТКАЗ (КРИТИЧНО!)", RED, 2))
                else: status_list.append((f"{system.name}: ОТКАЗ", UI_WARN_COLOR, 1))
            if system.is_boosted: status_list.append((f"{system.name}: УСИЛЕНО", UI_BOOST_COLOR, 0))
        if self.reactor.is_overloaded: status_list.append((f"РЕАКТОР: ПЕРЕГРУЗКА ({int(self.reactor.time_to_meltdown)}с)", RED, 3))
        
        for text, color, _ in sorted(status_list, key=lambda x: x[2], reverse=True):
            self.draw_text(text, self.font_small, color, WIDTH - 10, y_offset, "topright"); y_offset += 25

        self.messages = [msg for msg in self.messages if pygame.time.get_ticks() < msg[1]]
        y_offset = HEIGHT - 20
        for _, _, surf, rect in reversed(self.messages):
            rect.bottomleft = (20, y_offset)
            self.screen.blit(surf, rect)
            y_offset -= rect.height + 5

        if self.player.active_repair_system:
            system = self.player.active_repair_system
            s_pos = self.camera.apply_to_rect(system.rect)
            pb_bars = get_asset('progressbars')
            pb_idx = min(len(pb_bars) - 1, int(system.repair_progress * len(pb_bars)))
            pb_img = pb_bars[pb_idx]
            pb_rect = pb_img.get_rect(midbottom=(s_pos.centerx, s_pos.top - 5))
            self.screen.blit(pb_img, pb_rect)

    def draw_system_helpers(self):
        p_rect_inflated = self.player.rect.inflate(50, 50)
        if p_rect_inflated.colliderect(self.toolbox.rect):
            self.draw_text("[1] Ключ [2] Лейка", self.font_small, WHITE, self.camera.apply_to_rect(self.toolbox.rect).centerx, self.camera.apply_to_rect(self.toolbox.rect).top - 20, "center")
        if p_rect_inflated.colliderect(self.terminal.rect):
            self.draw_text("[F] Использовать", self.font_small, WHITE, self.camera.apply_to_rect(self.terminal.rect).centerx, self.camera.apply_to_rect(self.terminal.rect).top - 20, "center")
        if self.reactor.is_overloaded and p_rect_inflated.colliderect(self.reactor.rect):
            self.draw_text("[F] Стабилизировать!", self.font_small, RED, self.camera.apply_to_rect(self.reactor.rect).centerx, self.camera.apply_to_rect(self.reactor.rect).top - 20, "center")
        
        for system in self.systems:
            if system.is_broken and p_rect_inflated.colliderect(system.rect):
                icon = self.tool_icons.get(system.required_tool)
                if icon:
                    r = icon.get_rect(midbottom=self.camera.apply_to_rect(system.rect).midtop)
                    r.y -= 5
                    self.screen.blit(icon, r)

    def add_message(self, text, color=TEXT_COLOR):
        if len(self.messages) >= MAX_MESSAGES_DISPLAYED:
            self.messages.pop(0)
        surf = self.font_small.render(text, True, color)
        rect = surf.get_rect(topleft=(20, 0))
        self.messages.append((text, pygame.time.get_ticks() + MESSAGE_DURATION_SEC * 1000, surf, rect))

    def draw_text(self, text, font, color, x, y, align="center"):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if align == "center": rect.center = (x, y)
        elif align == "topleft": rect.topleft = (x, y)
        elif align == "topright": rect.topright = (x, y)
        self.screen.blit(surf, rect)

    def draw_end_screen(self, title, reason, color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        self.draw_text(title, self.font_large, color, WIDTH // 2, HEIGHT // 3)
        self.draw_text(reason, self.font_medium, TEXT_COLOR, WIDTH // 2, HEIGHT // 2)
        self.draw_text("Нажмите 'R' для возврата в меню", self.font_medium, WHITE, WIDTH // 2, HEIGHT - 150)

    def lose_life(self, reason):
        if self.player_lives > 0 and self.game_state == "playing":
            self.player_lives -= 1
            if reason:
                self.add_message(reason, RED)
            sound = get_asset('sound_alarm')
            # выделенный канал антиспам
            if sound and not self.alarm_channel.get_busy():
                self.alarm_channel.play(sound)
            self.screen_shake = SCREEN_SHAKE_INTENSITY * 5
            if self.player_lives <= 0:
                self.game_over("Критические повреждения корпуса.")
    
    def game_over(self, reason=""):
        if self.game_state == 'game_over': return
        self.game_state = "game_over"
        self.game_over_reason = reason
        self.player.stop_sounds()
        self.play_music('gameover')

    def victory(self):
        if self.game_state == 'victory': return
        self.game_state = "victory"
        self.player.stop_sounds()
        self.play_music('victory')

if __name__ == "__main__":
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    game = Game()
    game.run()
    pygame.quit()