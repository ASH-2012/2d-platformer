import pygame

class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 120, 90)
        self.hp = 30
        self.shoot_cooldown = 0

class EarthBoss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 200, 200)
        self.hp = 50
        self.attack_timer = 0

    def update(self, player):
        if self.hp > 0 and abs(player.rect.x - self.rect.x) < 800:
            self.attack_timer += 1
            if self.attack_timer >= 180:
                print("STAGE 2 BOSS: EARTHQUAKE SLAM!")
                if not player.is_jumping:
                    player.hp -= 15
                    print("PLAYER TOOK EARTHQUAKE DAMAGE!")
                else:
                    print("PLAYER DODGED THE EARTHQUAKE!")
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