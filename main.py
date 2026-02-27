import pygame
import sys
import os
import random

from entities.player import Player
from entities.enemies import Boss, EarthBoss, Spike, Projectile
from entities.dragon_ai import DragonBoss
from ai_brain.orchestrator import AITacticalBrain

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)

FLOOR_Y = HEIGHT - 110

ai_brain = AITacticalBrain(model_name="phi3") 

player = Player(100, FLOOR_Y - 60)
boss = Boss(4122, FLOOR_Y - 350) 
earth_boss = EarthBoss(8100, FLOOR_Y - 550)
dragon_boss = DragonBoss(14080, FLOOR_Y - 700)

ASSET_DIR = "assets"

try:
    raw_bg = pygame.image.load(os.path.join(ASSET_DIR, "bg.jpg")).convert()
    bg_img = pygame.transform.scale(raw_bg, (15000, HEIGHT))
    player_img = pygame.transform.scale(pygame.image.load(os.path.join(ASSET_DIR, "mc.png")).convert_alpha(), (player.rect.width, player.rect.height))
    boss_img = pygame.transform.scale(pygame.image.load(os.path.join(ASSET_DIR, "boss.png")).convert_alpha(), (boss.rect.width, boss.rect.height))
    earth_boss_img = pygame.transform.scale(pygame.image.load(os.path.join(ASSET_DIR, "boss2.png")).convert_alpha(), (earth_boss.rect.width, earth_boss.rect.height))
    dragon_boss_img = pygame.transform.scale(pygame.image.load(os.path.join(ASSET_DIR, "dragonboss.png")).convert_alpha(), (dragon_boss.rect.width, dragon_boss.rect.height))
    spike_img = pygame.image.load(os.path.join(ASSET_DIR, "spike.png")).convert_alpha()
except FileNotFoundError as e:
    print(f"\n[CRITICAL ERROR] Missing asset file: {e}")
    print("Ensure you are running the script from the SCIENCE_DAY root directory.")
    pygame.quit()
    sys.exit()

platforms = [
    pygame.Rect(0, FLOOR_Y, 649, 150), 
    pygame.Rect(805, FLOOR_Y, 327, 150),     
    pygame.Rect(1300, FLOOR_Y, 958, 150),    
    pygame.Rect(2426, FLOOR_Y, 650, 150),    
    pygame.Rect(3173, FLOOR_Y, 1564, 150),
    pygame.Rect(4857, 652, 4216, 150),
    pygame.Rect(7802, 455, 120, 50),
    pygame.Rect(7989, 383, 120, 50),
    pygame.Rect(7886, 229, 120, 50),
    pygame.Rect(9157, 500, 321, 150),
    pygame.Rect(9518, 690, 120, 50),
    pygame.Rect(9687, 565, 120, 50),
    pygame.Rect(9853, 501, 398, 150),
    pygame.Rect(10357, 596, 218, 150),
    pygame.Rect(10687, 639, 400, 150),
    pygame.Rect(11219, 526, 796, 150),
    pygame.Rect(12128, 530, 410, 150),
    pygame.Rect(12628, 317, 183, 50),
    pygame.Rect(12923, 528, 657, 150),
    pygame.Rect(13584, 379, 180, 50),
    pygame.Rect(13845, 475, 180, 50),
    pygame.Rect(13664, 636, 180, 50),
    pygame.Rect(14061, 618, 940, 150)
]

spikes = [
    Spike(4887, 85),
    Spike(5129, 65),
    Spike(5364, 50),
    Spike(5433, 70),
    Spike(5633, 94),
    Spike(5942, 70),
    Spike(6365, 78),
    Spike(6135, 62),
    Spike(6642, 49),
    Spike(6840, 56),
    Spike(7094, 83),
    Spike(7415, 68),
    Spike(7585, 60),
    Spike(7843, 82),
    Spike(7642, 79),
    Spike(8120, 51)
]
projectiles = []

player_profile = {
    "total_jumps": 0,
    "shots_fired": 0,
    "shots_hit": 0
}

true_scroll = 0
camera_scroll = 0
ai_triggered = False 

running = True
dev_click_text = "DEV: Click anywhere"
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        if event.type == pygame.KEYDOWN and player.hp > 0:
            if event.key == pygame.K_f:  
                direction = 15 if player.facing_right else -15
                projectiles.append(Projectile(player.rect.centerx, player.rect.centery, direction, True, (255, 100, 0)))
                player_profile["shots_fired"] += 1 
                
            if event.key == pygame.K_SPACE and not player.is_jumping:
                player_profile["total_jumps"] += 1 
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = mouse_x + camera_scroll
            dev_click_text = f"X: {world_x} | Y: {mouse_y}"
            print(f"[DEV] Map Coordinate -> X: {world_x} | Y: {mouse_y}")

    true_scroll += (player.rect.x - (WIDTH // 2) - true_scroll) / 10
    camera_scroll = max(0, int(true_scroll))

    if earth_boss.hp <= 0 and not ai_triggered:
        print("[SYSTEM] Stage 2 Clear. Transmitting Telemetry to AI Brain...")
        accuracy = 0
        if player_profile["shots_fired"] > 0:
            accuracy = round((player_profile["shots_hit"] / player_profile["shots_fired"]) * 100, 2)
        
        final_profile = {
            "jumps": player_profile["total_jumps"],
            "accuracy_percent": accuracy
        }
        
        ai_brain.request_tactics_async(final_profile, dragon_boss)
        ai_triggered = True 

    if player.hp > 0:
        player.move(platforms) 
    else:
        player.vel_y += 0.8
        player.rect.y += player.vel_y    

    if boss.hp > 0:
        boss.update(player, projectiles) # CORRECTED: Stage 1 Boss Brain Activated
        
    if earth_boss.hp > 0:
        earth_boss.update(player)
        
    dragon_boss.update(player, projectiles, spikes)

    if player.hp > 0:
        for b in [boss, earth_boss, dragon_boss]:
            if b.hp > 0 and player.rect.colliderect(b.rect):
                player.hp -= 2 
                
                if player.rect.centerx < b.rect.centerx:
                    player.rect.x -= 30 
                else:
                    player.rect.x += 30 
                
                player.vel_y = -8 

    for proj in projectiles[:]:
        proj.rect.x += proj.speed
        if proj.rect.x > player.rect.x + 800 or proj.rect.x < player.rect.x - 800:
            projectiles.remove(proj)
            continue
            
        if proj.is_player:
            if boss.hp > 0 and proj.rect.colliderect(boss.rect):
                boss.hp -= 1  
                player_profile["shots_hit"] += 1 
                projectiles.remove(proj)
            elif earth_boss.hp > 0 and proj.rect.colliderect(earth_boss.rect):
                earth_boss.hp -= 1
                player_profile["shots_hit"] += 1 
                projectiles.remove(proj)
            elif dragon_boss.hp > 0 and proj.rect.colliderect(dragon_boss.rect):
                dragon_boss.hp -= 1
                player_profile["shots_hit"] += 1 
                projectiles.remove(proj)
        else:
            if proj.rect.colliderect(player.rect):
                player.hp -= 10
                projectiles.remove(proj)

    for spike in spikes[:]:
        spike.update(player)
        if spike.rect.y > HEIGHT: 
            spikes.remove(spike)

    screen.fill((135, 206, 235))

    shake_x = 0
    shake_y = 0
    if earth_boss.hp > 0 and hasattr(earth_boss, 'is_charging') and earth_boss.is_charging:
        shake_x = random.randint(-12, 12) 
        shake_y = random.randint(-12, 12) 

    # CORRECTED: Dragon Boss Earthquake Camera Link
    if dragon_boss.hp > 0 and hasattr(dragon_boss, 'is_shaking') and dragon_boss.is_shaking:
        shake_x = random.randint(-20, 20) 
        shake_y = random.randint(-20, 20)

    render_scroll_x = camera_scroll + shake_x
    screen.blit(bg_img, (-render_scroll_x, shake_y)) 

    if not player.facing_right:
        flipped_player = pygame.transform.flip(player_img, True, False)
        screen.blit(flipped_player, (player.rect.x - render_scroll_x, player.rect.y + shake_y))
    else:
        screen.blit(player_img, (player.rect.x - render_scroll_x, player.rect.y + shake_y))

    if boss.hp > 0:
        screen.blit(boss_img, (boss.rect.x - render_scroll_x, boss.rect.y + shake_y))
        
    if earth_boss.hp > 0:
        if hasattr(earth_boss, 'is_charging') and earth_boss.is_charging:
            center_x = earth_boss.rect.centerx - render_scroll_x
            center_y = earth_boss.rect.centery + shake_y
            radius = (earth_boss.rect.width // 2) + 30 
            pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y), radius)
            
        screen.blit(earth_boss_img, (earth_boss.rect.x - render_scroll_x, earth_boss.rect.y + shake_y))

    if dragon_boss.hp > 0:
        screen.blit(dragon_boss_img, (dragon_boss.rect.x - render_scroll_x, dragon_boss.rect.y + shake_y))

    for proj in projectiles:
        pygame.draw.rect(screen, proj.color, (proj.rect.x - render_scroll_x, proj.rect.y + shake_y, proj.rect.width, proj.rect.height))
    for spike in spikes:
        screen.blit(spike_img, (spike.rect.x - render_scroll_x, spike.rect.y + shake_y))

    pygame.draw.rect(screen, (150, 0, 0), (20, 20, 200, 20)) 
    pygame.draw.rect(screen, (0, 255, 0), (20, 20, max(0, player.hp * 2), 20)) 
    pygame.draw.rect(screen, (255, 255, 255), (20, 20, 200, 20), 2)

    ai_text = font.render(f"AI Triggered: {ai_triggered}", True, (255, 255, 255))
    screen.blit(ai_text, (20, 50))

    active_bosses = [
        ("Stage 1 Boss", boss), 
        ("Earthquake Golem", earth_boss), 
        ("Dragon AI", dragon_boss)
    ]
    
    active_bosses = [
        ("Stage 1 Boss", boss, 30.0), 
        ("Earthquake Golem", earth_boss, 50.0), 
        ("Dragon AI", dragon_boss, 100.0)
    ]
    
    bars_drawn = 0 
    for name, b, max_hp in active_bosses: # Add max_hp here
        if b.hp > 0:
            relative_x = b.rect.x - camera_scroll
            if -b.rect.width < relative_x < WIDTH: 
                
                bar_width = 400
                bar_x = (WIDTH // 2) - (bar_width // 2)
                bar_y = HEIGHT - 50 - (bars_drawn * 60) 
                
                # Dynamic percentage calculation
                hp_percentage = max(0, b.hp) / max_hp 
                
                pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, 20))
                pygame.draw.rect(screen, (255, 165, 0), (bar_x, bar_y, int(bar_width * hp_percentage), 20))
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, 20), 2)
                
                boss_text = font.render(name, True, (255, 255, 255))
                screen.blit(boss_text, (bar_x, bar_y - 25))
                
                bars_drawn += 1

    try:
        dev_text = font.render(dev_click_text, True, (255, 255, 0)) 
        screen.blit(dev_text, (20, 80)) 
    except NameError:
        pass 
    
    if player.hp <= 0:
        game_over_font = pygame.font.SysFont("Arial", 80, bold=True)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(game_over_text, text_rect)
        
        # Add a restart prompt
        restart_font = pygame.font.SysFont("Arial", 30, bold=True)
        restart_text = restart_font.render("Press 'R' to Restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)
        
        # Listen for the restart key inside the main loop
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            # Reset player
            player.hp = 100
            player.rect.x = player.spawn_x
            player.rect.y = player.spawn_y
            player.vel_y = 0
            # Reset bosses
            boss.hp = 30
            earth_boss.hp = 50
            dragon_boss.hp = 100
            # Clear stage
            projectiles.clear()
            # Reset AI trigger
            ai_triggered = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()