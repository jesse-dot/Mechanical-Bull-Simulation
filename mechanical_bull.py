"""
Mechanical Bull Simulator
A physics-based simulation of a mechanical bull with a rider using Pygame and Pymunk.
"""

import pygame
import pymunk
import pymunk.pygame_util
import math
import random


# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Physics constants
GRAVITY = 981  # cm/s^2 (1 unit = 1 cm)
G_FORCE_THRESHOLD = 3.0  # Maximum G-force before rider falls off
MAX_CONSTRAINT_FORCE = 50000  # Maximum force the constraint can handle

# Bull properties
BULL_PLATFORM_WIDTH = 100
BULL_PLATFORM_HEIGHT = 20
BULL_MASS = 50
PIVOT_HEIGHT = 200

# Rider properties
RIDER_RADIUS = 20
RIDER_MASS = 10

# Motor properties
BASE_TORQUE = 50000
TORQUE_MULTIPLIER = 1.0
STOCHASTIC_AMPLITUDE = 30000


class MechanicalBullSimulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mechanical Bull Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Physics space
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        
        # Drawing options
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        # Game state
        self.running = True
        self.rider_fell = False
        self.torque_multiplier = TORQUE_MULTIPLIER
        self.manual_pitch_torque = 0
        self.manual_roll_torque = 0
        
        # Time tracking for stochastic functions
        self.time = 0
        
        # G-force tracking
        self.current_g_force = 1.0
        
        self._setup_physics()
    
    def _setup_physics(self):
        """Set up the physics bodies and constraints."""
        # Create static pivot point
        self.pivot_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.pivot_body.position = (SCREEN_WIDTH // 2, PIVOT_HEIGHT)
        
        # Create bull platform (dynamic body)
        moment = pymunk.moment_for_box(BULL_MASS, (BULL_PLATFORM_WIDTH, BULL_PLATFORM_HEIGHT))
        self.bull_body = pymunk.Body(BULL_MASS, moment)
        self.bull_body.position = self.pivot_body.position
        
        self.bull_shape = pymunk.Poly.create_box(self.bull_body, 
                                                  (BULL_PLATFORM_WIDTH, BULL_PLATFORM_HEIGHT))
        self.bull_shape.friction = 0.8
        self.bull_shape.color = (139, 69, 19, 255)  # Brown
        
        self.space.add(self.bull_body, self.bull_shape)
        
        # Create pivot joint (allows rotation on both axes)
        self.pivot_joint = pymunk.PivotJoint(self.pivot_body, self.bull_body, 
                                             self.pivot_body.position)
        self.pivot_joint.collide_bodies = False
        self.space.add(self.pivot_joint)
        
        # Create rider
        rider_moment = pymunk.moment_for_circle(RIDER_MASS, 0, RIDER_RADIUS)
        self.rider_body = pymunk.Body(RIDER_MASS, rider_moment)
        self.rider_body.position = (SCREEN_WIDTH // 2, PIVOT_HEIGHT - BULL_PLATFORM_HEIGHT // 2 - RIDER_RADIUS - 5)
        
        self.rider_shape = pymunk.Circle(self.rider_body, RIDER_RADIUS)
        self.rider_shape.friction = 0.9
        self.rider_shape.color = (255, 0, 0, 255)  # Red
        
        self.space.add(self.rider_body, self.rider_shape)
        
        # Create constraint to attach rider to bull (breakable)
        self.rider_constraint = pymunk.PinJoint(self.bull_body, self.rider_body,
                                                (0, -BULL_PLATFORM_HEIGHT // 2 - RIDER_RADIUS - 5),
                                                (0, 0))
        self.rider_constraint.max_force = MAX_CONSTRAINT_FORCE
        self.rider_constraint.error_bias = 0.1
        self.space.add(self.rider_constraint)
        
        # Ground for visual reference
        ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        ground_shape = pymunk.Segment(ground_body, (0, SCREEN_HEIGHT - 50), 
                                      (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 5)
        ground_shape.friction = 1.0
        ground_shape.color = (100, 100, 100, 255)
        self.space.add(ground_body, ground_shape)
    
    def _stochastic_torque(self, axis='pitch'):
        """
        Generate stochastic torque for realistic bull movement.
        Uses sine waves with noise for organic motion.
        """
        # Different frequencies for pitch and roll
        if axis == 'pitch':
            freq1, freq2 = 0.5, 1.2
        else:  # roll
            freq1, freq2 = 0.7, 1.5
        
        # Combine multiple sine waves with random noise
        torque = (math.sin(self.time * freq1) * STOCHASTIC_AMPLITUDE * 0.6 +
                  math.sin(self.time * freq2) * STOCHASTIC_AMPLITUDE * 0.4 +
                  random.uniform(-STOCHASTIC_AMPLITUDE * 0.3, STOCHASTIC_AMPLITUDE * 0.3))
        
        return torque * self.torque_multiplier
    
    def _calculate_g_force(self):
        """
        Calculate the G-force experienced by the rider.
        G-force = sqrt((centripetal_acceleration^2 + gravitational_acceleration^2)) / g
        """
        if self.rider_fell:
            self.current_g_force = 1.0
            return
        
        # Get rider velocity
        velocity = self.rider_body.velocity
        
        # Calculate centripetal acceleration
        # For circular motion: a_c = v^2 / r
        # We approximate using the distance from pivot
        dx = self.rider_body.position.x - self.pivot_body.position.x
        dy = self.rider_body.position.y - self.pivot_body.position.y
        radius = math.sqrt(dx**2 + dy**2)
        
        if radius > 0:
            speed = math.sqrt(velocity.x**2 + velocity.y**2)
            centripetal_accel = (speed**2) / radius
        else:
            centripetal_accel = 0
        
        # Calculate total acceleration (centripetal + gravitational)
        total_accel = math.sqrt(centripetal_accel**2 + GRAVITY**2)
        
        # Convert to G-force
        self.current_g_force = total_accel / GRAVITY
        
        # Check if constraint should break
        if self.current_g_force > G_FORCE_THRESHOLD and not self.rider_fell:
            # Remove the constraint
            if self.rider_constraint in self.space.constraints:
                self.space.remove(self.rider_constraint)
                self.rider_fell = True
                print(f"Rider fell off! G-force: {self.current_g_force:.2f}g")
    
    def _apply_motor_torques(self):
        """Apply stochastic and manual torques to the bull platform."""
        if not self.rider_fell:
            # Stochastic torques for automatic movement
            pitch_torque = self._stochastic_torque('pitch')
            roll_torque = self._stochastic_torque('roll')
            
            # Add manual control torques
            total_torque = (pitch_torque + roll_torque + 
                           self.manual_pitch_torque + self.manual_roll_torque)
            
            # Apply torque to bull
            self.bull_body.torque = total_torque
    
    def _handle_input(self):
        """Handle keyboard input for manual control."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset simulation
                    self._reset_simulation()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
        
        # Continuous key press handling
        keys = pygame.key.get_pressed()
        
        # Manual tilt controls (Arrow keys)
        self.manual_pitch_torque = 0
        self.manual_roll_torque = 0
        
        if keys[pygame.K_LEFT]:
            self.manual_roll_torque = -BASE_TORQUE
        if keys[pygame.K_RIGHT]:
            self.manual_roll_torque = BASE_TORQUE
        if keys[pygame.K_UP]:
            self.manual_pitch_torque = BASE_TORQUE
        if keys[pygame.K_DOWN]:
            self.manual_pitch_torque = -BASE_TORQUE
        
        # Motor intensity controls (+ and -)
        if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:  # + key
            self.torque_multiplier = min(3.0, self.torque_multiplier + 0.02)
        if keys[pygame.K_MINUS]:
            self.torque_multiplier = max(0.0, self.torque_multiplier - 0.02)
    
    def _reset_simulation(self):
        """Reset the simulation to initial state."""
        # Clear the space
        for constraint in list(self.space.constraints):
            self.space.remove(constraint)
        for body in list(self.space.bodies):
            self.space.remove(body)
        for shape in list(self.space.shapes):
            self.space.remove(shape)
        
        # Reset state
        self.rider_fell = False
        self.torque_multiplier = TORQUE_MULTIPLIER
        self.time = 0
        self.current_g_force = 1.0
        
        # Recreate physics
        self._setup_physics()
        print("Simulation reset")
    
    def _render(self):
        """Render the simulation."""
        self.screen.fill((200, 220, 255))  # Light blue background
        
        # Draw physics objects
        self.space.debug_draw(self.draw_options)
        
        # Draw pivot point
        pygame.draw.circle(self.screen, (0, 0, 0), 
                          (int(self.pivot_body.position.x), int(self.pivot_body.position.y)), 
                          8)
        
        # Draw UI text
        info_texts = [
            f"G-Force: {self.current_g_force:.2f}g",
            f"Motor Intensity: {self.torque_multiplier:.2f}x",
            f"Status: {'FELL OFF!' if self.rider_fell else 'Riding'}",
            f"Angle: {math.degrees(self.bull_body.angle):.1f}°",
            "",
            "Controls:",
            "Arrow Keys: Manual tilt",
            "+/-: Adjust motor intensity",
            "R: Reset",
            "ESC: Quit"
        ]
        
        y_offset = 10
        for text in info_texts:
            if text:  # Skip empty lines
                surface = self.font.render(text, True, (0, 0, 0))
                self.screen.blit(surface, (10, y_offset))
            y_offset += 25
        
        # Warning if G-force is high
        if self.current_g_force > G_FORCE_THRESHOLD * 0.8 and not self.rider_fell:
            warning = self.font.render("WARNING: High G-Force!", True, (255, 0, 0))
            self.screen.blit(warning, (SCREEN_WIDTH // 2 - 100, 10))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        dt = 1.0 / FPS
        
        print("Mechanical Bull Simulator")
        print("Controls:")
        print("  Arrow Keys: Manual tilt control")
        print("  +/-: Adjust motor intensity")
        print("  R: Reset simulation")
        print("  ESC: Quit")
        print(f"\nG-Force threshold: {G_FORCE_THRESHOLD}g")
        
        while self.running:
            self._handle_input()
            
            # Apply motor torques
            self._apply_motor_torques()
            
            # Update physics
            self.space.step(dt)
            
            # Calculate forces
            self._calculate_g_force()
            
            # Update time for stochastic functions
            self.time += dt
            
            # Render
            self._render()
            
            # Control frame rate
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    simulator = MechanicalBullSimulator()
    simulator.run()


if __name__ == "__main__":
    main()
