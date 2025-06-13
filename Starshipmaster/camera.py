import pygame
from settings import WIDTH, HEIGHT

class GameCamera:
    def __init__(self, world_width, world_height):
        self.camera_rect = pygame.Rect(0, 0, world_width, world_height)
        self.world_width = world_width
        self.world_height = world_height

    def apply_to_rect(self, entity_rect):
        """Смещает прямоугольник сущности для отрисовки относительно камеры."""
        return entity_rect.move(self.camera_rect.topleft)

    def update_camera(self, target_rect):
        """Обновляет позицию камеры, чтобы она следовала за целью (игроком)."""
        x = -target_rect.centerx + WIDTH // 2
        y = -target_rect.centery + HEIGHT // 2

        # Огранничение скролинга
        x = min(0, x) 
        y = min(0, y) 
        
        if self.world_width > WIDTH:
            x = max(-(self.world_width - WIDTH), x)
        else:
            x = 0
        
        if self.world_height > HEIGHT:
            y = max(-(self.world_height - HEIGHT), y)
        else:
            y = 0
            
        self.camera_rect.topleft = (x, y)