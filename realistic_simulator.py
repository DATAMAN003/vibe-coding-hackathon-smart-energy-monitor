#!/usr/bin/env python3
"""
Realistic Energy Device Simulator
Simulates real-world device behavior patterns with time-of-day, seasonal, and usage intelligence
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import realistic_config as config

class RealisticDeviceSimulator:
    """Simulates realistic device behavior patterns"""
    
    def __init__(self):
        self.device_profiles = self._initialize_device_profiles()
        self.seasonal_factors = self._get_seasonal_factors()
        
    def _initialize_device_profiles(self) -> Dict:
        """Initialize realistic device behavior profiles using config data"""
        profiles = {}
        
        for device_name, specs in config.REALISTIC_DEVICE_SPECS.items():
            # Get power ranges from config
            standby_range = specs['standby']
            active_range = specs['active'] 
            high_range = specs['high']
            
            profiles[device_name] = {
                'base_power': {
                    'standby': random.uniform(*standby_range),
                    'active': random.uniform(*active_range),
                    'high': random.uniform(*high_range)
                },
                'hourly_patterns': config.HOURLY_USAGE_PATTERNS[device_name],
                'weekend_factor': config.WEEKEND_MULTIPLIERS[device_name],
                'annual_kwh': specs['annual_kwh'],
                'energy_star_rating': specs['energy_star_rating'],
                'device_type': self._classify_device_type(device_name)
            }
        
        return profiles
    
    def _classify_device_type(self, device_name: str) -> str:
        """Classify device type for behavior patterns"""
        name_lower = device_name.lower()
        if 'tv' in name_lower:
            return 'entertainment'
        elif 'microwave' in name_lower:
            return 'appliance_burst'
        elif 'fridge' in name_lower:
            return 'always_on'
        elif 'ac' in name_lower or 'air' in name_lower:
            return 'climate'
        elif 'computer' in name_lower:
            return 'work_equipment'
        elif 'washing' in name_lower or 'dryer' in name_lower:
            return 'appliance_cycle'
        else:
            return 'general'
    
    def _get_seasonal_factors(self) -> Dict:
        """Get current seasonal adjustment factors"""
        month = datetime.now().month
        
        if month in [12, 1, 2]:
            return {'season': 'winter', 'temp_factor': 0.3, 'daylight_factor': 0.7}
        elif month in [3, 4, 5]:
            return {'season': 'spring', 'temp_factor': 0.7, 'daylight_factor': 1.0}
        elif month in [6, 7, 8]:
            return {'season': 'summer', 'temp_factor': 1.3, 'daylight_factor': 1.2}
        else:  # fall
            return {'season': 'fall', 'temp_factor': 0.8, 'daylight_factor': 0.9}
    
    def _get_weekend_factor(self, device_name: str) -> float:
        """Get weekend usage multiplier"""
        if datetime.now().weekday() >= 5:  # Weekend
            return self.device_profiles[device_name]['weekend_factor']
        return 1.0
    
    def _calculate_base_probability(self, device_name: str, hour: int) -> float:
        """Calculate base probability of device being active using hourly patterns"""
        profile = self.device_profiles[device_name]
        
        # Get base probability from hourly pattern
        base_prob = profile['hourly_patterns'][hour]
        
        # Apply weekend factor
        weekend_factor = self._get_weekend_factor(device_name)
        base_prob *= weekend_factor
        
        # Apply seasonal factor for climate devices
        if profile['device_type'] == 'climate':
            season_factor = self.seasonal_factors['temp_factor']
            base_prob *= season_factor
        
        # Add some randomness for realism
        randomness = random.uniform(0.8, 1.2)
        base_prob *= randomness
        
        return min(base_prob, 1.0)  # Cap at 100%
    
    def _determine_power_state(self, device_name: str, hour: int) -> Tuple[str, float]:
        """Determine current power state and consumption"""
        profile = self.device_profiles[device_name]
        base_prob = self._calculate_base_probability(device_name, hour)
        
        # Always-on devices (like fridge) - compressor cycling
        if profile['device_type'] == 'always_on':
            # Fridge compressor cycles based on temperature and usage
            if random.random() < base_prob:
                if random.random() < 0.3:  # 30% chance of high power (defrost cycle)
                    state = 'high'
                    power = profile['base_power']['high']
                else:
                    state = 'active'
                    power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Burst usage devices (like microwave) - short high-power bursts
        elif profile['device_type'] == 'appliance_burst':
            if random.random() < base_prob * 0.05:  # 5% of base probability for bursts
                state = 'high'
                power = profile['base_power']['high']
            elif random.random() < base_prob * 0.02:  # 2% for active (warming mode)
                state = 'active'
                power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Climate devices (AC) - temperature and comfort driven
        elif profile['device_type'] == 'climate':
            # More likely to be on during extreme temperatures
            temp_factor = self.seasonal_factors['temp_factor']
            adjusted_prob = base_prob * temp_factor
            
            if random.random() < adjusted_prob:
                if temp_factor > 1.2:  # Very hot/cold - high power
                    state = 'high'
                    power = profile['base_power']['high']
                else:
                    state = 'active'
                    power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Work equipment - follows work schedule closely
        elif profile['device_type'] == 'work_equipment':
            # Higher probability during work hours, much lower on weekends
            if random.random() < base_prob:
                if 9 <= hour <= 17 and datetime.now().weekday() < 5:  # Work hours
                    if random.random() < 0.4:  # 40% chance of high power (intensive tasks)
                        state = 'high'
                        power = profile['base_power']['high']
                    else:
                        state = 'active'
                        power = profile['base_power']['active']
                else:
                    state = 'active'  # Light usage outside work hours
                    power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Cycle-based appliances (washer, dryer) - realistic cycle patterns
        elif profile['device_type'] == 'appliance_cycle':
            # Simulate realistic laundry cycles
            if 'Washing' in device_name:
                cycle_prob = base_prob * 0.08  # 8% of base probability
            else:  # Dryer
                cycle_prob = base_prob * 0.06  # 6% of base probability (follows washer)
            
            if random.random() < cycle_prob:
                if random.random() < 0.8:  # 80% chance of high power during cycle
                    state = 'high'
                    power = profile['base_power']['high']
                else:
                    state = 'active'
                    power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Entertainment and general devices
        else:
            if random.random() < base_prob:
                if random.random() < 0.25:  # 25% chance of high power when active
                    state = 'high'
                    power = profile['base_power']['high']
                else:
                    state = 'active'
                    power = profile['base_power']['active']
            else:
                state = 'standby'
                power = profile['base_power']['standby']
        
        # Add realistic power variation (±10%)
        variation = random.uniform(0.9, 1.1)
        power *= variation
        
        return state, round(power, 2)
    
    def simulate_all_devices(self) -> List[Dict]:
        """Simulate all devices and return current readings"""
        current_hour = datetime.now().hour
        readings = []
        
        for device_name in self.device_profiles.keys():
            state, power = self._determine_power_state(device_name, current_hour)
            
            # Calculate realistic voltage and current
            voltage = random.uniform(118, 122)  # Realistic US voltage variation
            current_amps = power / voltage if power > 0 else 0
            
            # Calculate energy (this would be cumulative in real system)
            energy_kwh = power / 1000.0  # Simplified for demo
            
            # Calculate realistic cost with time-of-use rates
            current_rate = self._get_current_electricity_rate()
            cost_per_hour = round(power * current_rate / 1000, 4)
            
            reading = {
                'device_name': device_name,
                'device_id': device_name.lower().replace(' ', '_'),
                'power_watts': power,
                'voltage': round(voltage, 1),
                'current_amps': round(current_amps, 2),
                'energy_kwh': round(energy_kwh, 4),
                'status': state,
                'timestamp': datetime.now().isoformat(),
                'cost_per_hour': cost_per_hour,
                'electricity_rate': current_rate
            }
            
            readings.append(reading)
        
        return readings
    
    def _get_current_electricity_rate(self) -> float:
        """Get current electricity rate based on time-of-use"""
        now = datetime.now()
        hour = now.hour
        is_weekday = now.weekday() < 5
        
        # Check if it's peak hours
        if is_weekday:
            peak_hours = config.PEAK_HOURS['weekday']
        else:
            peak_hours = config.PEAK_HOURS['weekend']
        
        is_peak = any(start <= hour < end for start, end in peak_hours)
        
        # Determine rate
        if is_peak:
            base_rate = config.TOU_RATES['peak']
        elif 22 <= hour or hour < 6:  # Off-peak hours (10 PM - 6 AM)
            base_rate = config.TOU_RATES['off_peak']
        else:
            base_rate = config.TOU_RATES['mid_peak']
        
        # Apply seasonal multiplier
        season = self.seasonal_factors['season']
        seasonal_multiplier = config.SEASONAL_RATE_MULTIPLIERS.get(season, 1.0)
        
        return round(base_rate * seasonal_multiplier, 4)
    
    def get_device_info(self) -> Dict:
        """Get information about all simulated devices"""
        info = {}
        for device_name, profile in self.device_profiles.items():
            info[device_name] = {
                'type': profile['device_type'],
                'power_range': f"{profile['base_power']['standby']:.0f}-{profile['base_power']['high']:.0f}W",
                'annual_kwh': profile['annual_kwh'],
                'energy_star_rating': profile['energy_star_rating'],
                'weekend_factor': profile['weekend_factor']
            }
        return info