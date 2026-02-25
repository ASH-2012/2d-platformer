import pygame

class Player:
    def __init__(self, x, y):
        self.spawn_x = x
        self.spawn_y = y
        self.rect = pygame.Rect(x, y, 50, 60)
        self.vel_y = 0
        self.is_jumping = False
        self.speed = 6
        self.hp = 100 
        self.facing_right = True

    def move(self, platforms):
        keys = pygame.key.get_pressed()
        dx = 0
        
        if keys[pygame.K_LEFT]: 
            dx = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]: 
            dx = self.speed
            self.facing_right = True
            
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.vel_y = -16
            self.is_jumping = True

        # Gravity
        self.vel_y += 0.8 
        dy = self.vel_y

        # Collision Math
        for plat in platforms:
            if plat.colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0 
            if plat.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y > 0: 
                    self.rect.bottom = plat.top
                    dy = 0
                    self.vel_y = 0
                    self.is_jumping = False
                elif self.vel_y < 0: 
                    self.rect.top = plat.bottom
                    dy = 0
                    self.vel_y = 0

        self.rect.x += dx
        self.rect.y += dy

        # Death Pit Respawn
        if self.rect.y > 2000:
            self.hp -= 5
            self.rect.x = self.spawn_x
            self.rect.y = self.spawn_y
            self.vel_y = 0