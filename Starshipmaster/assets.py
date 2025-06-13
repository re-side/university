import pygame
import os
from settings import IMG_FOLDER, SND_FOLDER

# --- Универсальные функции загрузки ---
def load_image(filename):
    """Загружает одно изображение PNG с альфа-каналом."""
    fullname = os.path.join(IMG_FOLDER, filename)
    try:
        image = pygame.image.load(fullname).convert_alpha()
        return image
    except pygame.error as message:
        print(f"Не могу загрузить изображение: {filename}")
        raise SystemExit(message)

def load_sound(filename):
    """Загружает звуковой файл."""
    fullname = os.path.join(SND_FOLDER, filename)
    try:
        return pygame.mixer.Sound(fullname)
    except pygame.error as message:
        print(f"Не могу загрузить звук: {filename}")
        return None

def parse_spritesheet(sheet_surface, cols, rows):
    """Разрезает спрайт-лист на список кадров."""
    frames = []
    frame_w = sheet_surface.get_width() // cols
    frame_h = sheet_surface.get_height() // rows
    for row_num in range(rows):
        for col_num in range(cols):
            rect = pygame.Rect(col_num * frame_w, row_num * frame_h, frame_w, frame_h)
            frames.append(sheet_surface.subsurface(rect))
    return frames

# --- Кэш для хранения загруженных ассетов ---
asset_cache = {}

def get_asset(asset_name):
    """Безопасно получает ассет из кэша."""
    return asset_cache.get(asset_name)

# --- Функция предзагрузки всех ресурсов ---
def preload_game_assets():
    """Загружает все необходимые для игры ресурсы в кэш asset_cache."""
    from settings import PLAYER_SPRITESHEET_COLS, PLAYER_SPRITESHEET_ROWS, SMOKE_SPRITESHEET_COLS, SMOKE_SPRITESHEET_ROWS
    
    print("Предзагрузка игровых ассетов...")

    # Изображения
    asset_cache['ship_interior'] = load_image('ship_interior.png')
    player_sheet = load_image('player.png')
    asset_cache['player_frames'] = parse_spritesheet(player_sheet, PLAYER_SPRITESHEET_COLS, PLAYER_SPRITESHEET_ROWS)
    asset_cache['plants_ok'] = [load_image('plants_ok.png'), load_image('plants_ok2.png'), load_image('plants_ok3.png')]
    asset_cache['plant_broken'] = load_image('plants_notok.png')
    asset_cache['progressbars'] = [load_image(f'progressbar_{i}.png') for i in range(1, 5)]
    empty_bar = pygame.Surface(asset_cache['progressbars'][0].get_size(), pygame.SRCALPHA)
    asset_cache['progressbars'].insert(0, empty_bar)
    asset_cache['toolbox'] = load_image('tools.png')
    asset_cache['wrench'] = load_image('spanner.png')
    asset_cache['watering_can'] = load_image('watering_can.png')
    asset_cache['terminal'] = load_image('terminal.png')
    asset_cache['reactor_core'] = load_image('reactor_core.png')
    asset_cache['engine_ok'] = load_image('engine.png')
    asset_cache['shield_ok'] = load_image('shield.png')
    asset_cache['meteor'] = load_image('meteor.png')
    asset_cache['heart_full'] = load_image('heart.png')
    asset_cache['heart_empty'] = load_image('heart_0.png')
    smoke_sheet = load_image('smoke.png')
    asset_cache['smoke_frames'] = parse_spritesheet(smoke_sheet, SMOKE_SPRITESHEET_COLS, SMOKE_SPRITESHEET_ROWS)
    
    # Звуки
    asset_cache['sound_alarm'] = load_sound('alarm_short.ogg')
    asset_cache['sound_repair_done'] = load_sound('success.ogg')
    asset_cache['sound_repair_loop'] = load_sound('repair.mp3')
    asset_cache['sound_meteor_hit'] = load_sound('meteor_hit.mp3')
    asset_cache['sound_footsteps'] = load_sound('footsteps.mp3')
    asset_cache['sound_terminal_use'] = load_sound('click.wav')

    # Фоновая музыка
    asset_cache['music_menu'] = os.path.join(SND_FOLDER, 'Background_Music.mp3')
    asset_cache['music_normal'] = os.path.join(SND_FOLDER, 'Background_Music_2.ogg')
    asset_cache['music_hard'] = os.path.join(SND_FOLDER, 'Background_Music_2.ogg')
    asset_cache['music_victory'] = os.path.join(SND_FOLDER, 'victory_music.ogg')
    asset_cache['music_gameover'] = os.path.join(SND_FOLDER, 'game_over.mp3')

    print("Ассеты предзагружены.")