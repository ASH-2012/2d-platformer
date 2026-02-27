import pygame
import random
# Assuming Projectile and Spike classes are defined in your entities module
from entities.enemies import Projectile, Spike 

class DragonBoss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 700, 600)
        self.hp = 100
        
        # The baseline stats before the AI DM injects new weights
        self.tactics = {
            "projectiles": 5, 
            "spike_drop": 5, 
            "earthquake": 5
        }
        
        self.current_state = "IDLE"
        
        # Action cooldown (How fast the boss chains standard attacks)
        self.action_timer = 120 # Starts with a 2-second delay at 60FPS
        
        # Your hardcoded ultimate ability (Every 10 seconds / 600 frames)
        self.ultimate_timer = 600 

    def update_tactics(self, new_tactics):
        """Called by the background AI thread to overwrite the boss's brain."""
        # Sanity check: Ensure the LLM didn't hallucinate weird keys
        expected_keys = ["projectiles", "spike_drop", "earthquake"]
        if all(key in new_tactics for key in expected_keys):
            self.tactics = new_tactics
        else:
            print("[SYSTEM] Rejected invalid tactics dictionary from AI.")

    def choose_attack(self):
        """Rolls the loaded dice based on the AI's weights."""
        attacks = list(self.tactics.keys())
        weights = list(self.tactics.values())
        
        # random.choices uses the integer weights to bias the selection
        self.current_state = random.choices(attacks, weights=weights, k=1)[0]

    def update(self, player, projectiles_list, spikes_list):
        if self.hp <= 0 or abs(player.rect.x - self.rect.x) > 900:
            return # Don't fight if dead or player is too far away

        # --- 1. THE HARDCODED ULTIMATE ---
        self.ultimate_timer -= 1
        if self.ultimate_timer <= 0:
            print("[BOSS] EXECUTING MASSIVE FIRE BLAST!")
            # Spawn a massive, slow projectile covering half the screen
            spawn_x = self.rect.left
            spawn_y = self.rect.centery - 100
            # You will need to add logic in your Projectile class to handle a massive size/damage
            projectiles_list.append(Projectile(spawn_x, spawn_y, -4, False, (255, 100, 0))) 
            self.ultimate_timer = 600 # Reset 10-second timer
            return # Skip standard attacks this frame

        # --- 2. THE AI-DRIVEN ATTACKS ---
        self.action_timer -= 1
        if self.action_timer <= 0:
            self.choose_attack()
            self.execute_attack(player, projectiles_list, spikes_list)

    def execute_attack(self, player, projectiles_list, spikes_list):
        print(f"[BOSS] AI selected: {self.current_state} | Current Weights: {self.tactics}")
        
        if self.current_state == "projectiles":
            # Shoot a fast projectile directly at the player's height
            spawn_x = self.rect.left
            spawn_y = player.rect.centery 
            projectiles_list.append(Projectile(spawn_x, spawn_y, -12, False, (255, 50, 50)))
            self.action_timer = 60 # 1 second cooldown for fast attacks
            
        elif self.current_state == "spike_drop":
            # Spawn a spike directly over the player
            spikes_list.append(Spike(player.rect.x, player.rect.y - 400))
            self.action_timer = 90 # 1.5 second cooldown
            
        elif self.current_state == "earthquake":
            # Punish the player if they are on the ground
            if not player.is_jumping:
                player.hp -= 15
                print("PLAYER TOOK EARTHQUAKE DAMAGE!")
            else:
                print("PLAYER DODGED THE EARTHQUAKE!")
            self.action_timer = 150 # 2.5 second cooldown (heavy attack recovery)