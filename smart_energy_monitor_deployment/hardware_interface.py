"""Hardware interface for DIY current sensors using Raspberry Pi"""

import time
import math
import logging
from typing import Dict, List, Optional, Tuple
import config

logger = logging.getLogger(__name__)

class CurrentSensorInterface:
    def __init__(self):
        self.adc = None
        self.setup_adc()
    
    def setup_adc(self):
        """Initialize the MCP3008 ADC via SPI"""
        try:
            import spidev
            self.adc = spidev.SpiDev()
            self.adc.open(config.ADC_SPI_PORT, config.ADC_SPI_DEVICE)
            self.adc.max_speed_hz = 1000000  # 1MHz
            logger.info("ADC initialized successfully")
        except ImportError:
            logger.error("spidev not available - install with: pip install spidev")
            self.adc = None
        except Exception as e:
            logger.error(f"Failed to initialize ADC: {e}")
            self.adc = None
    
    def read_adc_channel(self, channel: int) -> float:
        """Read voltage from ADC channel (0-7)"""
        if not self.adc:
            return 0.0
        
        try:
            # MCP3008 command: start bit + single/diff + channel + don't care bits
            command = [1, (8 + channel) << 4, 0]
            response = self.adc.xfer2(command)
            
            # Convert response to 10-bit value
            adc_value = ((response[1] & 3) << 8) + response[2]
            
            # Convert to voltage (0-3.3V)
            voltage = (adc_value / 1023.0) * config.ADC_VREF
            return voltage
            
        except Exception as e:
            logger.error(f"Error reading ADC channel {channel}: {e}")
            return 0.0
    
    def read_ct_sensor(self, sensor_config: Dict, samples: int = 1000) -> Dict:
        """Read current from CT sensor with RMS calculation"""
        channel = sensor_config['adc_channel']
        ct_ratio = sensor_config['ct_ratio']
        voltage = sensor_config['voltage']
        calibration = sensor_config.get('calibration_factor', 1.0)
        
        # Collect samples for RMS calculation
        readings = []
        sample_interval = 0.0001  # 100μs between samples (10kHz sampling)
        
        for _ in range(samples):
            reading = self.read_adc_channel(channel)
            readings.append(reading)
            time.sleep(sample_interval)
        
        # Calculate RMS current
        if not readings:
            return self._create_reading_dict(sensor_config, 0, 0, 0)
        
        # Remove DC bias (assume midpoint is 1.65V for 3.3V supply)
        dc_bias = config.ADC_VREF / 2
        ac_readings = [r - dc_bias for r in readings]
        
        # Calculate RMS
        sum_squares = sum(r * r for r in ac_readings)
        rms_voltage = math.sqrt(sum_squares / len(ac_readings))
        
        # Convert to current (assuming burden resistor creates 1V per amp)
        # This needs calibration based on your specific CT and burden resistor
        rms_current = (rms_voltage * ct_ratio / 1000) * calibration  # Convert mA to A
        
        # Calculate power (assuming resistive load, so P = V * I)
        power_watts = voltage * rms_current
        
        # Calculate energy (this is instantaneous, real energy needs integration over time)
        energy_kwh = power_watts / 1000  # This will be calculated properly in the collector
        
        return self._create_reading_dict(sensor_config, rms_current, power_watts, energy_kwh)
    
    def _create_reading_dict(self, sensor_config: Dict, current: float, power: float, energy: float) -> Dict:
        """Create standardized reading dictionary"""
        return {
            'device_id': sensor_config.get('device_id', f"ct_{sensor_config['adc_channel']}"),
            'device_name': sensor_config['name'],
            'current_amps': current,
            'power_watts': power,
            'voltage': sensor_config['voltage'],
            'energy_kwh': energy,
            'sensor_type': 'ct_sensor',
            'adc_channel': sensor_config['adc_channel']
        }
    
    def calibrate_sensor(self, sensor_config: Dict, known_load_watts: float) -> float:
        """Calibrate a CT sensor against a known load"""
        print(f"Calibrating {sensor_config['name']}...")
        print(f"Please turn on a device with known power consumption: {known_load_watts}W")
        input("Press Enter when the load is stable...")
        
        # Take several readings
        readings = []
        for i in range(10):
            reading = self.read_ct_sensor(sensor_config, samples=500)
            readings.append(reading['power_watts'])
            print(f"Reading {i+1}: {reading['power_watts']:.2f}W")
            time.sleep(1)
        
        # Calculate average measured power
        avg_measured = sum(readings) / len(readings)
        
        if avg_measured > 0:
            calibration_factor = known_load_watts / avg_measured
            print(f"Calculated calibration factor: {calibration_factor:.3f}")
            return calibration_factor
        else:
            print("No power detected - check connections")
            return 1.0
    
    def test_all_sensors(self):
        """Test all configured sensors"""
        print("Testing all current sensors...")
        print("-" * 50)
        
        for device_id, sensor_config in config.ENERGY_SENSORS.items():
            if sensor_config['type'] == 'ct_sensor':
                reading = self.read_ct_sensor(sensor_config)
                print(f"{reading['device_name']}:")
                print(f"  Current: {reading['current_amps']:.3f} A")
                print(f"  Power: {reading['power_watts']:.2f} W")
                print(f"  Channel: {reading['adc_channel']}")
                print()

# Advanced simulation mode for realistic testing
class SimulatedCurrentSensor:
    """Advanced simulated current sensor with realistic patterns"""
    
    def __init__(self):
        import random
        from datetime import datetime, timedelta
        self.random = random
        self.datetime = datetime
        self.start_time = datetime.now()
        
        # Realistic appliance profiles with usage patterns
        self.appliance_profiles = {
            'tv': {
                'base_power': 150,
                'standby_power': 5,
                'usage_hours': [(18, 23), (7, 9)],  # Evening and morning
                'weekend_factor': 1.3,
                'seasonal_factor': 1.0
            },
            'microwave': {
                'base_power': 1200,
                'standby_power': 3,
                'usage_pattern': 'burst',  # Short high-power bursts
                'daily_uses': 4,
                'use_duration': 3  # minutes
            },
            'ac': {
                'base_power': 2000,
                'standby_power': 0,
                'temperature_dependent': True,
                'usage_hours': [(14, 22)],  # Afternoon/evening
                'seasonal_factor': 2.5  # Much higher in summer
            },
            'fridge': {
                'base_power': 200,
                'standby_power': 80,
                'cycle_pattern': True,
                'cycle_minutes': 45,  # On for 15min, off for 30min
                'always_on': True
            },
            'computer': {
                'base_power': 300,
                'standby_power': 10,
                'usage_hours': [(9, 17), (19, 23)],  # Work and evening
                'weekend_factor': 0.7,
                'load_variation': 0.4  # Gaming vs idle
            },
            'washer': {
                'base_power': 800,
                'standby_power': 2,
                'usage_pattern': 'cycle',
                'cycle_duration': 60,  # minutes
                'daily_probability': 0.3
            },
            'dryer': {
                'base_power': 3000,
                'standby_power': 0,
                'usage_pattern': 'cycle',
                'cycle_duration': 45,
                'follows_washer': True
            }
        }
        
        # Track device states
        self.device_states = {}
        
        # Add more randomness - seed with current time + random component for different patterns each run
        import time
        # Use microseconds and process ID for maximum uniqueness each run
        import os
        seed = int(time.time() * 1000000) + os.getpid() + self.random.randint(0, 10000)
        self.random.seed(seed)
        
        # Add interval-based randomness for continuous variation
        self.last_randomization = time.time()
        self.randomization_interval = 120  # Re-randomize every 2 minutes for more variation
        
        # Global device activity control - randomly vary how many devices are active
        self.global_activity_state = {
            'target_active_count': self.random.randint(2, 6),  # Random 2-6 devices active
            'last_activity_change': time.time(),
            'activity_change_interval': 120,  # Change activity pattern every 2 minutes for realistic variation
            'forced_off_devices': set(),  # Devices forced off for variety
            'forced_on_devices': set()    # Devices forced on for variety
        }
        
        # Add random variation to appliance profiles for each run
        self._randomize_profiles()
        
        logger.info("Using advanced simulated current sensors with realistic patterns")
    
    def _randomize_profiles(self):
        """Add random variations to appliance profiles for each app run"""
        for appliance, profile in self.appliance_profiles.items():
            # Randomize base power within realistic ranges
            base_variation = self.random.uniform(0.8, 1.2)
            profile['base_power'] = int(profile['base_power'] * base_variation)
            
            # Randomize standby power
            if 'standby_power' in profile:
                standby_variation = self.random.uniform(0.5, 1.5)
                profile['standby_power'] = max(0, profile['standby_power'] * standby_variation)
            
            # Add random usage probability variations
            profile['random_factor'] = self.random.uniform(0.7, 1.3)
            
            # Randomize cycle patterns
            if profile.get('cycle_pattern'):
                cycle_variation = self.random.uniform(0.8, 1.2)
                profile['cycle_minutes'] = int(profile.get('cycle_minutes', 45) * cycle_variation)
    
    def _update_global_activity(self):
        """Update global device activity patterns to vary active device count"""
        import time
        current_time = time.time()
        
        # Check if it's time to change activity pattern
        if current_time - self.global_activity_state['last_activity_change'] > self.global_activity_state['activity_change_interval']:
            # Randomly choose new target active count (2-6 devices)
            self.global_activity_state['target_active_count'] = self.random.randint(2, 6)
            self.global_activity_state['last_activity_change'] = current_time
            
            # Clear previous forced states
            self.global_activity_state['forced_off_devices'].clear()
            self.global_activity_state['forced_on_devices'].clear()
            
            # Get all device names from config
            import config
            all_devices = list(config.ENERGY_SENSORS.keys())
            
            # Randomly select devices to force off or on to achieve target count
            target_count = self.global_activity_state['target_active_count']
            
            if target_count < len(all_devices):
                # Force some devices off
                devices_to_force_off = self.random.sample(all_devices, len(all_devices) - target_count)
                self.global_activity_state['forced_off_devices'].update(devices_to_force_off)
            
            # Randomly force 1-2 devices on for variety
            remaining_devices = [d for d in all_devices if d not in self.global_activity_state['forced_off_devices']]
            if remaining_devices:
                force_on_count = min(self.random.randint(1, 2), len(remaining_devices))
                devices_to_force_on = self.random.sample(remaining_devices, force_on_count)
                self.global_activity_state['forced_on_devices'].update(devices_to_force_on)
    
    def _should_device_be_active(self, device_name: str, device_id: str) -> bool:
        """Determine if a device should be active based on global activity control"""
        # Use the actual device_id from config (like 'living_room_tv', 'kitchen_fridge', etc.)
        actual_device_id = device_id.replace('sim_', '')  # Remove sim_ prefix if present
        
        # Map ADC channels to device IDs for proper identification
        channel_to_device = {
            0: 'living_room_tv',
            1: 'kitchen_microwave', 
            2: 'kitchen_fridge',
            3: 'bedroom_ac',
            4: 'office_computer',
            5: 'laundry_washer',
            6: 'laundry_dryer'
        }
        
        # If device_id is just a number (ADC channel), map it to proper device ID
        if actual_device_id.isdigit():
            channel = int(actual_device_id)
            actual_device_id = channel_to_device.get(channel, actual_device_id)
        
        # Check forced states first
        if actual_device_id in self.global_activity_state['forced_off_devices']:
            return False
        if actual_device_id in self.global_activity_state['forced_on_devices']:
            return True
        
        # For fridge, keep it mostly active (it's essential)
        if 'fridge' in device_name.lower():
            return self.random.random() < 0.85  # 85% chance to be active
        
        # For other devices, use random probability based on time and device type
        hour = self.datetime.now().hour
        
        # Different probabilities based on time of day
        if 6 <= hour <= 9:  # Morning
            morning_devices = ['microwave', 'tv', 'computer']
            if any(d in device_name.lower() for d in morning_devices):
                return self.random.random() < 0.6
        elif 17 <= hour <= 23:  # Evening
            evening_devices = ['tv', 'computer', 'ac']
            if any(d in device_name.lower() for d in evening_devices):
                return self.random.random() < 0.7
        elif 10 <= hour <= 16:  # Daytime
            daytime_devices = ['computer', 'ac']
            if any(d in device_name.lower() for d in daytime_devices):
                return self.random.random() < 0.5
        
        # Default random probability
        return self.random.random() < 0.4
    
    def _get_time_factors(self):
        """Get current time-based factors"""
        now = self.datetime.now()
        hour = now.hour
        day_of_week = now.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5
        
        # Seasonal factor (rough approximation)
        month = now.month
        if month in [6, 7, 8]:  # Summer
            seasonal_factor = 1.5
        elif month in [12, 1, 2]:  # Winter
            seasonal_factor = 1.2
        else:
            seasonal_factor = 1.0
            
        return hour, is_weekend, seasonal_factor
    
    def _simulate_appliance_power(self, device_name: str, profile: Dict) -> float:
        """Simulate realistic power consumption for an appliance"""
        hour, is_weekend, seasonal_factor = self._get_time_factors()
        device_key = device_name.lower()
        
        # Initialize device state if needed
        if device_key not in self.device_states:
            self.device_states[device_key] = {
                'last_update': self.datetime.now(),
                'is_on': False,
                'cycle_start': None,
                'burst_end': None
            }
        
        state = self.device_states[device_key]
        base_power = profile['base_power']
        standby_power = profile.get('standby_power', 0)
        
        # Always-on devices (like fridge)
        if profile.get('always_on'):
            if profile.get('cycle_pattern'):
                # Cycling pattern (fridge compressor)
                cycle_minutes = profile.get('cycle_minutes', 45)
                minutes_since_start = (self.datetime.now() - self.start_time).total_seconds() / 60
                cycle_position = minutes_since_start % cycle_minutes
                
                if cycle_position < cycle_minutes * 0.33:  # On for 1/3 of cycle
                    return base_power * self.random.uniform(0.9, 1.1)
                else:
                    return standby_power * self.random.uniform(0.8, 1.2)
        
        # Usage hours pattern
        usage_hours = profile.get('usage_hours', [])
        in_usage_hours = any(start <= hour <= end for start, end in usage_hours)
        
        # Weekend factor
        weekend_factor = profile.get('weekend_factor', 1.0) if is_weekend else 1.0
        
        # Seasonal adjustment
        seasonal_adj = profile.get('seasonal_factor', 1.0) * seasonal_factor
        
        # Burst pattern (microwave)
        if profile.get('usage_pattern') == 'burst':
            daily_uses = profile.get('daily_uses', 4)
            use_duration = profile.get('use_duration', 3)
            
            # Random chance of being in use
            if self.random.random() < (daily_uses * use_duration) / (24 * 60):
                return base_power * self.random.uniform(0.95, 1.05)
            else:
                return standby_power
        
        # Cycle pattern (washer/dryer)
        if profile.get('usage_pattern') == 'cycle':
            daily_prob = profile.get('daily_probability', 0.2)
            cycle_duration = profile.get('cycle_duration', 60)
            
            # Check if currently in cycle
            if state.get('cycle_start'):
                elapsed = (self.datetime.now() - state['cycle_start']).total_seconds() / 60
                if elapsed < cycle_duration:
                    # In cycle - vary power based on cycle stage
                    cycle_progress = elapsed / cycle_duration
                    if cycle_progress < 0.1:  # Fill/start
                        power_factor = 0.3
                    elif cycle_progress < 0.8:  # Main cycle
                        power_factor = 1.0
                    else:  # Spin/drain
                        power_factor = 0.6
                    
                    return base_power * power_factor * self.random.uniform(0.9, 1.1)
                else:
                    # Cycle complete
                    state['cycle_start'] = None
                    return standby_power
            
            # Random chance to start cycle during usage hours
            if in_usage_hours and self.random.random() < daily_prob / 24:
                state['cycle_start'] = self.datetime.now()
                return base_power * 0.3  # Starting up
        
        # Regular usage pattern
        if in_usage_hours:
            # Device is likely on during usage hours
            base_probability = 0.7 * weekend_factor * profile.get('random_factor', 1.0)
            # Add time-based randomness - more variation throughout the day
            time_randomness = self.random.uniform(0.5, 1.5)
            on_probability = min(0.95, base_probability * time_randomness)
            
            if self.random.random() < on_probability:
                load_variation = profile.get('load_variation', 0.2)
                variation = self.random.uniform(1 - load_variation, 1 + load_variation)
                return base_power * variation * seasonal_adj
        
        # Default to standby power with some variation
        return standby_power * self.random.uniform(0.8, 1.2)
    
    def read_ct_sensor(self, sensor_config: Dict, samples: int = 1000) -> Dict:
        """Simulate realistic current sensor readings with dynamic device activity"""
        import time
        
        # Update global activity patterns
        self._update_global_activity()
        
        # Re-randomize profiles periodically for continuous variation
        current_time = time.time()
        if current_time - self.last_randomization > self.randomization_interval:
            self._randomize_profiles()
            self.last_randomization = current_time
            # Add some random state changes
            for device_key in self.device_states:
                if self.random.random() < 0.4:  # 40% chance to reset device state
                    self.device_states[device_key]['cycle_start'] = None
                    self.device_states[device_key]['is_on'] = self.random.choice([True, False])
        
        device_name = sensor_config['name']
        adc_channel = sensor_config['adc_channel']
        device_id = f"sim_{adc_channel}"
        
        # Check if device should be active based on global activity control
        should_be_active = self._should_device_be_active(device_name, str(adc_channel))
        
        if not should_be_active:
            # Device is off - return minimal standby power or zero
            standby_power = self.random.uniform(0, 2)  # 0-2W standby
            current = standby_power / sensor_config['voltage']
            energy_kwh = standby_power / 1000
            
            return {
                'device_id': device_id,
                'device_name': device_name,
                'current_amps': current,
                'power_watts': standby_power,
                'voltage': sensor_config['voltage'],
                'energy_kwh': energy_kwh,
                'sensor_type': 'simulated',
                'adc_channel': sensor_config['adc_channel']
            }
        
        # Device is active - simulate normal power consumption
        device_name_lower = device_name.lower()
        
        # Find matching appliance profile
        profile = None
        for appliance, app_profile in self.appliance_profiles.items():
            if appliance in device_name_lower:
                profile = app_profile
                break
        
        if profile:
            power = self._simulate_appliance_power(device_name_lower, profile)
        else:
            # Generic appliance with more variation
            base_power = self.random.uniform(50, 400)
            time_factor = abs(math.sin(current_time / 3600))  # Hourly variation
            power = base_power * (0.5 + time_factor)
        
        # Add realistic measurement noise and fluctuations
        noise_factor = self.random.uniform(0.95, 1.05)
        fluctuation = math.sin(current_time * 2) * 0.02  # Small periodic fluctuation
        power *= (noise_factor + fluctuation)
        
        # Ensure minimum realistic values for active devices
        if power < 1.5:  # Active devices should consume at least 1.5W
            power = self.random.uniform(1.5, 10)
        
        current = power / sensor_config['voltage']
        energy_kwh = power / 1000
        
        return {
            'device_id': device_id,
            'device_name': device_name,
            'current_amps': current,
            'power_watts': power,
            'voltage': sensor_config['voltage'],
            'energy_kwh': energy_kwh,
            'sensor_type': 'simulated',
            'adc_channel': sensor_config['adc_channel']
        }
    
    def test_all_sensors(self):
        """Test simulated sensors"""
        print("Testing simulated current sensors...")
        print("-" * 50)
        
        for device_id, sensor_config in config.ENERGY_SENSORS.items():
            reading = self.read_ct_sensor(sensor_config)
            print(f"{reading['device_name']}:")
            print(f"  Current: {reading['current_amps']:.3f} A")
            print(f"  Power: {reading['power_watts']:.2f} W")
            print(f"  (Simulated)")
            print()

# Factory function to get appropriate sensor interface
def get_sensor_interface(use_simulation: bool = False):
    """Get the appropriate sensor interface"""
    if use_simulation:
        return SimulatedCurrentSensor()
    else:
        return CurrentSensorInterface()

if __name__ == "__main__":
    import sys
    
    # Test the sensors
    use_sim = len(sys.argv) > 1 and sys.argv[1] == "sim"
    
    sensor_interface = get_sensor_interface(use_simulation=use_sim)
    sensor_interface.test_all_sensors()
    
    if not use_sim and hasattr(sensor_interface, 'calibrate_sensor'):
        # Offer calibration
        print("\nWould you like to calibrate any sensors? (y/n)")
        if input().lower().startswith('y'):
            for device_id, sensor_config in config.ENERGY_SENSORS.items():
                print(f"\nCalibrate {sensor_config['name']}? (y/n)")
                if input().lower().startswith('y'):
                    watts = float(input("Enter known load power in watts: "))
                    factor = sensor_interface.calibrate_sensor(sensor_config, watts)
                    print(f"Update calibration_factor to {factor:.3f} in config.py")