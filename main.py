import pygame
import sys
import os
import random

# Importing from your new modular directory structure
# You must ensure your Player, Boss, EarthBoss, Spike, and Projectile classes 
# are properly moved into the entities folder.
from entities.player import Player
from entities.enemies import Boss, EarthBoss, Spike, Projectile
from entities.dragon_ai import DragonBoss
from ai_brain.orchestrator import AITacticalBrain

pygame.init()

# --- DYNAMIC DISPLAY RESOLUTION ---
# This ensures it fits the projector/monitor at your stall
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)

# Define your relative floor
FLOOR_Y = HEIGHT - 110

# --- INITIALIZATION ---
# Instantiating the AI DM (Ensure Ollama is running 'phi3' or 'qwen' in the background)
ai_brain = AITacticalBrain(model_name="phi3") 

player = Player(100, FLOOR_Y - 60)
boss = Boss(4122, FLOOR_Y - 350) 
earth_boss = EarthBoss(8100, FLOOR_Y - 550)
dragon_boss = DragonBoss(14080, FLOOR_Y - 700)

# --- ASSET LOADING & SCALING ---
ASSET_DIR = "assets"

try:
    # Background - Stretched to fill the world map
    raw_bg = pygame.image.load(os.path.join(ASSET_DIR, "bg.jpg")).convert()
    bg_img = pygame.transform.scale(raw_bg, (15000, HEIGHT))

    # Entities
    player_img = pygame.image.load(os.path.join(ASSET_DIR, "mc.png")).convert_alpha()
    player_img = pygame.transform.scale(player_img, (player.rect.width, player.rect.height))

    boss_img = pygame.image.load(os.path.join(ASSET_DIR, "boss.png")).convert_alpha()
    boss_img = pygame.transform.scale(boss_img, (boss.rect.width, boss.rect.height))

    earth_boss_img = pygame.image.load(os.path.join(ASSET_DIR, "boss2.png")).convert_alpha()
    earth_boss_img = pygame.transform.scale(earth_boss_img, (earth_boss.rect.width, earth_boss.rect.height))

    dragon_boss_img = pygame.image.load(os.path.join(ASSET_DIR, "dragonboss.png")).convert_alpha()
    dragon_boss_img = pygame.transform.scale(dragon_boss_img, (dragon_boss.rect.width, dragon_boss.rect.height))

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
    pygame.Rect(12128, 490, 410, 150),
    pygame.Rect(12628, 317, 183, 50),
    pygame.Rect(12923, 528, 657, 150),
    pygame.Rect(13584, 379, 180, 50),
    pygame.Rect(13845, 475, 180, 50),
    pygame.Rect(13664, 636, 180, 50),
    pygame.Rect(14061, 618, 940, 150)
                
]

spikes = []
projectiles = []

# --- TELEMETRY TRACKER ---
player_profile = {
    "total_jumps": 0,
    "shots_fired": 0,
    "shots_hit": 0
}

# --- STATE MANAGEMENT ---
true_scroll = 0
camera_scroll = 0
ai_triggered = False # Prevents spamming the API

# --- MAIN LOOP ---
running = True
dev_click_text = "DEV: Click anywhere"
while running:
    # 1. INPUT & EVENT PUMP
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Emergency Exit for Fullscreen
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        if event.type == pygame.KEYDOWN and player.hp > 0:
            if event.key == pygame.K_f:  
                direction = 15 if player.facing_right else -15
                projectiles.append(Projectile(player.rect.centerx, player.rect.centery, direction, True, (255, 100, 0)))
                player_profile["shots_fired"] += 1 # TELEMETRY LOG
                
            if event.key == pygame.K_SPACE and not player.is_jumping:
                player_profile["total_jumps"] += 1 # TELEMETRY LOG
            
 # DEVELOPER TOOL: Get World Coordinates

        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_x, mouse_y = pygame.mouse.get_pos()
          world_x = mouse_x + camera_scroll

          # Update the screen text variable
          dev_click_text = f"X: {world_x} | Y: {mouse_y}"
          print(f"[DEV] Map Coordinate -> X: {world_x} | Y: {mouse_y}")

    # 2. CAMERA LOGIC
    true_scroll += (player.rect.x - (WIDTH // 2) - true_scroll) / 10
    camera_scroll = max(0, int(true_scroll))

    # 3. THE AI TRIGGER (The 30-Second Buffer)
    if earth_boss.hp <= 0 and not ai_triggered:
        print("[SYSTEM] Stage 2 Clear. Transmitting Telemetry to AI Brain...")
        
        # Calculate accuracy to give the AI better context
        accuracy = 0
        if player_profile["shots_fired"] > 0:
            accuracy = round((player_profile["shots_hit"] / player_profile["shots_fired"]) * 100, 2)
        
        final_profile = {
            "jumps": player_profile["total_jumps"],
            "accuracy_percent": accuracy
        }
        
        # This fires off onto a separate CPU thread. The game loop continues instantly.
        ai_brain.request_tactics_async(final_profile, dragon_boss)
        ai_triggered = True 

    # 4. GAME LOGIC UPDATES
    if player.hp > 0:
        player.move(platforms) # Note: move() needs to handle SPACEbar internally, but don't double-count jumps
    else:
        # The player is dead. Apply terminal gravity so they fall off the map.
        player.vel_y += 0.8
        player.rect.y += player.vel_y    

    if boss.hp > 0:
        pass # Add your Stage 1 boss update logic here
        
    if earth_boss.hp > 0:
        earth_boss.update(player)
        
    # The Dragon Boss relies entirely on its internal Weighted Probability State Machine now
    dragon_boss.update(player, projectiles, spikes)

    # Contact Damage & Knockback
    # (Checking if the player's physical rect touches any boss rect)
    if player.hp > 0:
        for b in [boss, earth_boss, dragon_boss]:
            if b.hp > 0 and player.rect.colliderect(b.rect):
                player.hp -= 2 # Drain health rapidly while touching
                
                # Brutal Knockback: Throw the player away from the boss
                if player.rect.centerx < b.rect.centerx:
                    player.rect.x -= 30 # Knocked left
                else:
                    player.rect.x += 30 # Knocked right
                
                player.vel_y = -8 # Knocked slightly into the air

    # Collision & Projectile Math
    for proj in projectiles[:]:
        proj.rect.x += proj.speed
        if proj.rect.x > player.rect.x + 800 or proj.rect.x < player.rect.x - 800:
            projectiles.remove(proj)
            continue
            
        if proj.is_player:
            if boss.hp > 0 and proj.rect.colliderect(boss.rect):
                boss.hp -= 1  
                player_profile["shots_hit"] += 1 # TELEMETRY LOG
                projectiles.remove(proj)
            elif earth_boss.hp > 0 and proj.rect.colliderect(earth_boss.rect):
                earth_boss.hp -= 1
                player_profile["shots_hit"] += 1 # TELEMETRY LOG
                projectiles.remove(proj)
            elif dragon_boss.hp > 0 and proj.rect.colliderect(dragon_boss.rect):
                dragon_boss.hp -= 1
                player_profile["shots_hit"] += 1 # TELEMETRY LOG
                projectiles.remove(proj)
        else:
            if proj.rect.colliderect(player.rect):
                player.hp -= 10
                projectiles.remove(proj)

    # Spike Math
    for spike in spikes[:]:
        spike.update(player)
        if spike.rect.y > HEIGHT: # Clean up memory
            spikes.remove(spike)

    # 5. RENDERING (Clear screen, draw background, draw entities)
    screen.fill((135, 206, 235))

    # --- SCREEN SHAKE MATH ---
    shake_x = 0
    shake_y = 0
    # If the boss is charging, generate violent random offsets
    if earth_boss.hp > 0 and hasattr(earth_boss, 'is_charging') and earth_boss.is_charging:
        shake_x = random.randint(-12, 12) 
        shake_y = random.randint(-12, 12) 

    # Apply shake to camera scroll for X, use shake_y directly for Y
    render_scroll_x = camera_scroll + shake_x

    # Draw Background
    screen.blit(bg_img, (-render_scroll_x, shake_y)) 

    # Draw Platforms
    for plat in platforms:
        pygame.draw.rect(screen, (50, 200, 50), (plat.x - render_scroll_x, plat.y + shake_y, plat.width, plat.height))

    # Draw Player (Preserving your flip logic)
    if not player.facing_right:
        flipped_player = pygame.transform.flip(player_img, True, False)
        screen.blit(flipped_player, (player.rect.x - render_scroll_x, player.rect.y + shake_y))
    else:
        screen.blit(player_img, (player.rect.x - render_scroll_x, player.rect.y + shake_y))

    # Draw Bosses
    if boss.hp > 0:
        screen.blit(boss_img, (boss.rect.x - render_scroll_x, boss.rect.y + shake_y))
        
    if earth_boss.hp > 0:
        # THE VISUAL CUE (Now perfectly syncing with the screen shake)
        if hasattr(earth_boss, 'is_charging') and earth_boss.is_charging:
            center_x = earth_boss.rect.centerx - render_scroll_x
            center_y = earth_boss.rect.centery + shake_y
            radius = (earth_boss.rect.width // 2) + 30 
            pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y), radius)
            
        screen.blit(earth_boss_img, (earth_boss.rect.x - render_scroll_x, earth_boss.rect.y + shake_y))

    if dragon_boss.hp > 0:
        screen.blit(dragon_boss_img, (dragon_boss.rect.x - render_scroll_x, dragon_boss.rect.y + shake_y))

    # Draw Projectiles & Spikes
    for proj in projectiles:
        pygame.draw.rect(screen, proj.color, (proj.rect.x - render_scroll_x, proj.rect.y + shake_y, proj.rect.width, proj.rect.height))
    for spike in spikes:
        screen.blit(spike_img, (spike.rect.x - render_scroll_x, spike.rect.y + shake_y))

    # ==========================================
    # --- DYNAMIC UI (Anchored to the screen) ---
    # ==========================================
    
    # 1. Player Health Bar (Top Left)
    # Background (Red - missing health)
    pygame.draw.rect(screen, (150, 0, 0), (20, 20, 200, 20)) 
    # Foreground (Green - current health). Assuming Max HP is 100. (100 * 2 = 200 pixels wide)
    pygame.draw.rect(screen, (0, 255, 0), (20, 20, max(0, player.hp * 2), 20)) 
    # White Outline
    pygame.draw.rect(screen, (255, 255, 255), (20, 20, 200, 20), 2)

    # 2. AI Trigger Text (Changed to stark white for visibility)
    ai_text = font.render(f"AI Triggered: {ai_triggered}", True, (255, 255, 255))
    screen.blit(ai_text, (20, 50))

    # 3. Dynamic Boss Health Bars (Only draws if the boss is on screen)
    active_bosses = [
        ("Stage 1 Boss", boss), 
        ("Earthquake Golem", earth_boss), 
        ("Dragon AI", dragon_boss)
    ]
    
    bars_drawn = 0 
    for name, b in active_bosses:
        if b.hp > 0:
            # Check if boss is currently visible to the camera lens
            relative_x = b.rect.x - camera_scroll
            if -b.rect.width < relative_x < WIDTH: 
                
                bar_width = 400
                bar_x = (WIDTH // 2) - (bar_width // 2)
                # Draw at the bottom of the screen. Stack them if multiple bosses overlap.
                bar_y = HEIGHT - 50 - (bars_drawn * 60) 
                
                # IMPORTANT: Assuming boss max HP is 50. Change 50.0 to your actual max HP.
                hp_percentage = max(0, b.hp) / 50.0 
                
                # Dark Red Background
                pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, 20))
                # Orange/Yellow Foreground 
                pygame.draw.rect(screen, (255, 165, 0), (bar_x, bar_y, int(bar_width * hp_percentage), 20))
                # White Outline
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, 20), 2)
                
                # Render Boss Name above the bar
                boss_text = font.render(name, True, (255, 255, 255))
                screen.blit(boss_text, (bar_x, bar_y - 25))
                
                bars_drawn += 1


# 4. Developer Coordinate Tool (Top Right)
    # Ensure 'dev_click_text' is defined before your while loop: dev_click_text = "Click for Coords"
        # 4. Developer Coordinate Tool (Top Left, Safe Zone)
    try:
        dev_text = font.render(dev_click_text, True, (255, 255, 0)) # Yellow text
        # Hard-anchored under the AI text to bypass Windows scaling cutoff
        screen.blit(dev_text, (20, 80)) 
    except NameError:
        pass # Prevents a crash if you forgot to add the variable in your event loop
    except NameError:
        pass # Prevents a crash if you forgot to add the variable in your event loop
    
    
# --- GAME OVER OVERLAY ---
    if player.hp <= 0:
        # Massive red text in the center of the screen
        game_over_font = pygame.font.SysFont("Arial", 80, bold=True)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()