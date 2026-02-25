import pygame
import sys
import os

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
boss = Boss(4222, FLOOR_Y - 90) 
earth_boss = EarthBoss(8200, FLOOR_Y - 200)
dragon_boss = DragonBoss(14180, FLOOR_Y - 250)

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
    pygame.Rect(0, FLOOR_Y, 610, 150), 
    pygame.Rect(752, FLOOR_Y, 318, 150),     
    pygame.Rect(1244, FLOOR_Y, 948, 150),    
    pygame.Rect(2366, FLOOR_Y, 648, 150),    
    pygame.Rect(3116, FLOOR_Y, 15000, 150), # Continuous floor for the rest of the map  
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
while running:
    # 1. INPUT & EVENT PUMP
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Emergency Exit for Fullscreen
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:  
                direction = 15 if player.facing_right else -15
                projectiles.append(Projectile(player.rect.centerx, player.rect.centery, direction, True, (255, 100, 0)))
                player_profile["shots_fired"] += 1 # TELEMETRY LOG
                
            if event.key == pygame.K_SPACE and not player.is_jumping:
                player_profile["total_jumps"] += 1 # TELEMETRY LOG

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

    if boss.hp > 0:
        pass # Add your Stage 1 boss update logic here
        
    if earth_boss.hp > 0:
        earth_boss.update(player)
        
    # The Dragon Boss relies entirely on its internal Weighted Probability State Machine now
    dragon_boss.update(player, projectiles, spikes)

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
    screen.blit(bg_img, (-camera_scroll, 0)) # Background is now active

    # Draw Platforms (Leave as rects unless you have floor tiles ready)
    for plat in platforms:
        pygame.draw.rect(screen, (50, 200, 50), (plat.x - camera_scroll, plat.y, plat.width, plat.height))

   # Draw Player
    if not player.facing_right:
        flipped_player = pygame.transform.flip(player_img, True, False)
        screen.blit(flipped_player, (player.rect.x - camera_scroll, player.rect.y))
    else:
        screen.blit(player_img, (player.rect.x - camera_scroll, player.rect.y))

    # Draw Bosses
    if boss.hp > 0:
        screen.blit(boss_img, (boss.rect.x - camera_scroll, boss.rect.y))
    if earth_boss.hp > 0:
        screen.blit(earth_boss_img, (earth_boss.rect.x - camera_scroll, earth_boss.rect.y))
    if dragon_boss.hp > 0:
        screen.blit(dragon_boss_img, (dragon_boss.rect.x - camera_scroll, dragon_boss.rect.y))

    # Draw Projectiles & Spikes
    for proj in projectiles:
        pygame.draw.rect(screen, proj.color, (proj.rect.x - camera_scroll, proj.rect.y, proj.rect.width, proj.rect.height))
    for spike in spikes:
        screen.blit(spike_img, (spike.rect.x - camera_scroll, spike.rect.y))
    
    # Draw UI
    hp_text = font.render(f"HP: {max(0, player.hp)} | AI Triggered: {ai_triggered}", True, (0,0,0))
    screen.blit(hp_text, (20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()