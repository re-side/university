import pygame
import os

# --- Основные настройки экрана и FPS ---
WIDTH = 500
HEIGHT = 500
FPS = 60

# --- Цвета ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
TEXT_COLOR = (230, 230, 230)
UI_WARN_COLOR = (255, 165, 0) # Оранжевый
UI_BOOST_COLOR = (0, 255, 255) # Голубой для усилений

# --- Игровые параметры (базовые) ---
BASE_GAME_DURATION_SECONDS = 180
BASE_PLAYER_LIVES = 3
BASE_REPAIR_TIME_SECONDS = 2.5
BASE_LIFE_SUPPORT_CRITICAL_TIME_SEC = 25 # Уменьшил, чтобы было опаснее
BASE_METEOR_SPAWN_MIN_SEC = 8
BASE_METEOR_SPAWN_MAX_SEC = 16
BASE_MIN_TIME_BETWEEN_BREAKS_SEC = 15 # Системы ломаются чуть чаще
BASE_MAX_TIME_BETWEEN_BREAKS_SEC = 25
METEOR_SPEED_PIX_PER_SEC = 250

# --- Настройки камеры, UI и эффектов ---
FOG_OF_WAR_RADIUS = 250
SCREEN_SHAKE_INTENSITY = 5
MAX_MESSAGES_DISPLAYED = 5
MESSAGE_DURATION_SEC = 4

# --- Пути к папкам ---
GAME_FOLDER = os.path.dirname(__file__)
ASSETS_FOLDER = os.path.join(GAME_FOLDER, 'assets')
IMG_FOLDER = os.path.join(ASSETS_FOLDER, 'images')
SND_FOLDER = os.path.join(ASSETS_FOLDER, 'sounds')

# --- Настройки спрайт-листов ---
PLAYER_SPRITESHEET_COLS, PLAYER_SPRITESHEET_ROWS = 4, 4
PLAYER_IDLE_ROW, PLAYER_WALK_ROW = 0, 2
SMOKE_SPRITESHEET_COLS, SMOKE_SPRITESHEET_ROWS = 4, 2

# --- Кастомные события ---
LOSE_LIFE_EVENT = pygame.USEREVENT + 1