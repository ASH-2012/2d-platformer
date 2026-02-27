import pygame

class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 450, 350)
        self.hp = 30
        self.shoot_cooldown = 0

class EarthBoss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 450, 450)
        self.hp = 50
        self.attack_timer = 0
        self.is_charging = False # New state variable

    def update(self, player):
        if self.hp > 0 and abs(player.rect.x - self.rect.x) < 800:
            self.attack_timer += 1
            
            # The Tell: 1 second (60 frames) before the attack hits
            if self.attack_timer == 180:
                self.is_charging = True
                print("[VISUAL CUE] EARTH BOSS IS GLOWING YELLOW - PREPARE TO JUMP!")
            
            # The Strike: Hits at 270 frames
            if self.attack_timer >= 270:
                self.is_charging = False
                
                # Check if the player is physically airborne, not just if they pressed jump
                if player.vel_y == 0: 
                    player.hp -= 15
                    
                self.attack_timer = 0

class Spike:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 80)
        self.falling = False
        self.speed = 12

    def update(self, player):
        # Tripwire logic
        if abs(player.rect.centerx - self.rect.centerx) < 150 and player.rect.y > self.rect.y:
            self.falling = True

        if self.falling:
            self.rect.y += self.speed
            
        if self.rect.colliderect(player.rect):
            player.hp -= 10
            self.rect.y = 3000 # Teleport away out of bounds after hit

class Projectile:
    def __init__(self, x, y, speed, is_player, color):
        self.rect = pygame.Rect(x, y, 15, 15)
        self.speed = speed
        self.is_player = is_player
        self.color = color