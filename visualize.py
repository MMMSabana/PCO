import pygame
import random
import math

# --- PARAMETERS ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
BG_COLOR = (10, 10, 15)

# Biological & Simulation Constants
NUM_AGENTS = 200
VIEW_RADIUS = 150  # Local interaction range (pixels)
COUPLING_STRENGTH = 0.015  # ε (Epsilon): Phase advance per stimulus
REFRACTORY_PERIOD = 0.2  # Absolute refractory period (0.0 to 1.0)
NATURAL_FREQ_BASE = 0.01  # Base intrinsic frequency per frame
FREQ_VARIANCE = 0.002  # Individual heterogeneity


class Firefly:
    def __init__(self, id):
        self.id = id
        self.x = random.uniform(0, WINDOW_WIDTH)
        self.y = random.uniform(0, WINDOW_HEIGHT)

        # Oscillator state variable θ ∈ [0, 1]
        self.phase = random.random()

        # Intrinsic frequency ω_i
        self.frequency = NATURAL_FREQ_BASE + random.uniform(-FREQ_VARIANCE, FREQ_VARIANCE)

        self.flash_timer = 0
        self.is_flashing = False

    def update(self):
        """
        Natural evolution of the oscillator phase.
        Returns True if threshold is reached spontaneously.
        """
        if self.is_flashing:
            self.flash_timer -= 1
            if self.flash_timer <= 0:
                self.is_flashing = False
            return False

        self.phase += self.frequency

        # Threshold check (Integrate-and-Fire)
        if self.phase >= 1.0:
            self.fire()
            return True
        return False

    def fire(self):
        """Resets phase and activates visual signal."""
        self.phase = 0.0
        self.is_flashing = True
        self.flash_timer = 5  # Visual duration of the flash (frames)

    def nudge(self):
        """
        Apply excitatory coupling (pulse) to the oscillator.
        Mechanism: Pulse-Coupled Oscillation with Refractory Period.
        """
        # Check refractory period to prevent immediate re-excitation
        if self.phase < REFRACTORY_PERIOD or self.is_flashing:
            return False

        # Phase advance: θ_new = θ_old + ε
        self.phase += COUPLING_STRENGTH

        # Check if the nudge pushed the oscillator over the threshold
        if self.phase >= 1.0:
            self.fire()
            return True  # Signal propagation (Avalanche effect)

        return False

    def draw(self, surface):
        if self.is_flashing:
            # Bioluminescence effect
            pygame.draw.circle(surface, (255, 255, 200), (int(self.x), int(self.y)), 5)
            # Halo (Light diffusion)
            glow = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 50, 50), (20, 20), 18)
            surface.blit(glow, (self.x - 20, self.y - 20))
        else:
            # Sub-threshold state (brightness proportional to phase)
            intensity = int(30 + 100 * self.phase)
            color = (intensity, intensity, 20)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 2)


def get_toroidal_distance_sq(a, b, w, h):
    """
    Calculates squared Euclidean distance on a Toroidal Manifold.
    Metric: ds^2 = min(|x1-x2|, w - |x1-x2|)^2 + min(|y1-y2|, h - |y1-y2|)^2
    """
    dx = abs(a.x - b.x)
    dy = abs(a.y - b.y)

    if dx > w * 0.5: dx = w - dx
    if dy > h * 0.5: dy = h - dy

    return dx * dx + dy * dy


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Pulse-Coupled Oscillators: Mirollo-Strogatz Model")
    clock = pygame.time.Clock()

    agents = [Firefly(i) for i in range(NUM_AGENTS)]

    running = True
    while running:
        dt = clock.tick(FPS)
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Desynchronize (Reset to chaos)
                for a in agents: a.phase = random.random()

        # --- SIMULATION STEP ---

        # 1. Spontaneous firings (Natural frequency drive)
        firing_queue = []
        for agent in agents:
            if agent.update():
                firing_queue.append(agent)

        # 2. Pulse propagation (Instantaneous interaction)
        # Process the queue until no new agents are triggered in this time step
        processed_flashes = set()

        while firing_queue:
            source_agent = firing_queue.pop(0)

            # Prevent processing the same flash multiple times in one frame
            if source_agent.id in processed_flashes:
                continue
            processed_flashes.add(source_agent.id)

            # Broadcast signal to neighbors
            for target in agents:
                if target.id == source_agent.id:
                    continue

                # Spatial query with Toroidal topology
                dist_sq = get_toroidal_distance_sq(source_agent, target, WINDOW_WIDTH, WINDOW_HEIGHT)

                if dist_sq < VIEW_RADIUS ** 2:
                    # Apply coupling mechanism
                    triggered = target.nudge()
                    if triggered:
                        firing_queue.append(target)

        # --- RENDER ---
        for agent in agents:
            agent.draw(screen)

        # Overlay info
        # font = pygame.font.SysFont("monospace", 14)
        # info = font.render(f"Coupling: {COUPLING_STRENGTH} | Radius: {VIEW_RADIUS}", True, (100, 100, 100))
        # screen.blit(info, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()