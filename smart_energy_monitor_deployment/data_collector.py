"""Data collection from various smart plugs and DIY current sensors"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
import config
from database import EnergyDatabase
from hardware_interface import get_sensor_interface

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnergyDataCollector:
    def __init__(self, use_simulation: bool = False):
        self.db = EnergyDatabase()
        self.devices = config.ENERGY_SENSORS
        self.running = False
        self.sensor_interface = get_sensor_interface(use_simulation)
        self.energy_accumulator = {}  # Track energy over time
    
    async def collect_kasa_data(self, device_config: Dict) -> Optional[Dict]:
        """Collect data from TP-Link Kasa smart plugs"""
        try:
            from kasa import SmartPlug
            
            plug = SmartPlug(device_config['ip'])
            await plug.update()
            
            if not plug.is_on:
                return None
            
            # Get power consumption data
            emeter = plug.emeter_realtime
            
            return {
                'device_id': device_config.get('id', device_config['ip']),
                'device_name': device_config['name'],
                'power_watts': emeter.get('power', 0),
                'voltage': emeter.get('voltage', 0),
                'current': emeter.get('current', 0),
                'energy_kwh': emeter.get('total', 0) / 1000,  # Convert Wh to kWh
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error collecting from Kasa device {device_config['name']}: {e}")
            return None
    
    async def collect_shelly_data(self, device_config: Dict) -> Optional[Dict]:
        """Collect data from Shelly smart plugs via HTTP API"""
        try:
            import aiohttp
            
            url = f"http://{device_config['ip']}/meter/0"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            'device_id': device_config.get('id', device_config['ip']),
                            'device_name': device_config['name'],
                            'power_watts': data.get('power', 0),
                            'energy_kwh': data.get('total', 0) / 60000,  # Convert to kWh
                            'timestamp': datetime.now()
                        }
                        
        except Exception as e:
            logger.error(f"Error collecting from Shelly device {device_config['name']}: {e}")
            return None
    
    def collect_ct_sensor_data(self, device_id: str, device_config: Dict) -> Optional[Dict]:
        """Collect data from CT current sensors"""
        try:
            reading = self.sensor_interface.read_ct_sensor(device_config)
            
            # Calculate energy consumption since last reading
            current_time = datetime.now()
            power_watts = reading['power_watts']
            
            if device_id in self.energy_accumulator:
                last_time, last_power = self.energy_accumulator[device_id]
                time_diff_hours = (current_time - last_time).total_seconds() / 3600
                
                # Simple energy calculation (average power * time)
                avg_power = (power_watts + last_power) / 2
                energy_kwh = (avg_power * time_diff_hours) / 1000
            else:
                energy_kwh = 0
            
            # Update accumulator
            self.energy_accumulator[device_id] = (current_time, power_watts)
            
            # Update reading with calculated energy
            reading['energy_kwh'] = energy_kwh
            reading['device_id'] = device_id
            reading['timestamp'] = current_time
            
            return reading
            
        except Exception as e:
            logger.error(f"Error collecting from CT sensor {device_config['name']}: {e}")
            return None

    async def collect_from_device(self, device_id: str, device_config: Dict) -> Optional[Dict]:
        """Collect data from a single device based on its type"""
        device_type = device_config.get('type', 'unknown')
        
        if device_type == 'kasa':
            return await self.collect_kasa_data(device_config)
        elif device_type == 'shelly':
            return await self.collect_shelly_data(device_config)
        elif device_type == 'ct_sensor':
            return self.collect_ct_sensor_data(device_id, device_config)
        else:
            logger.warning(f"Unknown device type: {device_type}")
            return None
    
    async def collect_all_devices(self) -> List[Dict]:
        """Collect data from all configured devices"""
        tasks = []
        
        for device_id, device_config in self.devices.items():
            task = self.collect_from_device(device_id, device_config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_readings = []
        for result in results:
            if isinstance(result, dict):
                valid_readings.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Collection error: {result}")
        
        return valid_readings
    
    def save_readings(self, readings: List[Dict]):
        """Save readings to database"""
        for reading in readings:
            try:
                self.db.add_reading(
                    device_id=reading['device_id'],
                    device_name=reading['device_name'],
                    power_watts=reading['power_watts'],
                    voltage=reading.get('voltage'),
                    current=reading.get('current'),
                    energy_kwh=reading.get('energy_kwh')
                )
                logger.info(f"Saved reading for {reading['device_name']}: {reading['power_watts']}W")
            except Exception as e:
                logger.error(f"Error saving reading: {e}")
    
    async def start_collection(self):
        """Start the continuous data collection process"""
        self.running = True
        logger.info("Starting energy data collection...")
        
        # Register devices in database
        for device_id, device_config in self.devices.items():
            self.db.add_device(
                device_id=device_id,
                device_name=device_config['name'],
                device_type=device_config['type'],
                ip_address=device_config.get('ip')
            )
        
        while self.running:
            try:
                # Collect data from all devices
                readings = await self.collect_all_devices()
                
                if readings:
                    self.save_readings(readings)
                    logger.info(f"Collected {len(readings)} readings")
                else:
                    logger.warning("No readings collected this cycle")
                
                # Wait for next collection cycle
                await asyncio.sleep(config.POLLING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in collection cycle: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    def stop_collection(self):
        """Stop the data collection process"""
        self.running = False
        logger.info("Stopping energy data collection...")

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    # Check for simulation mode
    use_sim = "sim" in sys.argv
    collector = EnergyDataCollector(use_simulation=use_sim)
    
    if "test" in sys.argv:
        # Test single collection
        async def test_collection():
            readings = await collector.collect_all_devices()
            print(f"Collected {len(readings)} readings:")
            for reading in readings:
                print(f"  {reading['device_name']}: {reading['power_watts']:.2f}W")
                if 'current_amps' in reading:
                    print(f"    Current: {reading['current_amps']:.3f}A")
        
        asyncio.run(test_collection())
    else:
        # Start continuous collection
        print(f"Starting energy collection {'(simulation mode)' if use_sim else '(hardware mode)'}...")
        try:
            asyncio.run(collector.start_collection())
        except KeyboardInterrupt:
            print("\nStopping collection...")
            collector.stop_collection()