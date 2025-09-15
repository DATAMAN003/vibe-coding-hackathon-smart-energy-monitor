"""AI-powered energy analysis using gpt-oss models"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from database import EnergyDatabase
import config

# Import torch only when needed to avoid dependency issues
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnergyAIAnalyzer:
    def __init__(self, use_mock_ai: bool = True):
        # Force use of the same database as web interface
        self.db = EnergyDatabase(db_path=str(config.DATABASE_PATH))
        self.use_mock_ai = use_mock_ai
        self.model = None
        
        if not use_mock_ai:
            self._initialize_gpt_oss()
        else:
            logger.info("Using mock AI for development - will use real gpt-oss when available")
    
    def _initialize_gpt_oss(self):
        """Initialize the gpt-oss model with proper error handling and fallback"""
        try:
            # Check if transformers is available
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                if not TORCH_AVAILABLE:
                    raise ImportError("torch not available")
                
                # Check if CUDA is available for GPU acceleration
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Initializing gpt-oss model on {device}")
                
                # Try to load the actual gpt-oss model when available
                model_name = "gpt-oss-20b"  # This will be the actual model name
                
                # For now, we'll use a smaller model as placeholder
                # When gpt-oss is released, replace with actual model
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        device_map="auto" if device == "cuda" else None,
                        low_cpu_mem_usage=True
                    )
                    self.device = device
                    logger.info(f"Successfully loaded gpt-oss model: {model_name}")
                    
                except Exception as model_error:
                    logger.warning(f"gpt-oss model not available yet: {model_error}")
                    logger.info("Falling back to mock AI - will automatically use gpt-oss when released")
                    self.use_mock_ai = True
                    
            except ImportError:
                logger.warning("transformers library not installed - install with: pip install transformers torch")
                self.use_mock_ai = True
                
        except Exception as e:
            logger.error(f"Error initializing gpt-oss: {e}")
            logger.info("Using mock AI as fallback")
            self.use_mock_ai = True
    
    def analyze_device_patterns(self, device_id: str, days: int = 7) -> Dict:
        """Analyze usage patterns for a specific device"""
        readings = self.db.get_recent_readings(device_id, hours=days*24)
        
        if not readings:
            return {
                'device_id': device_id,
                'analysis_period_days': days,
                'statistics': {
                    'avg_power_watts': 0.0,
                    'max_power_watts': 0.0,
                    'min_power_watts': 0.0,
                    'total_energy_kwh': 0.0,
                    'total_cost': 0.0,
                    'usage_hours_per_day': 0.0,
                    'peak_usage_hour': 18,
                    'weekend_vs_weekday_ratio': 1.0,
                    'efficiency_score': 50.0
                },
                'insights': ['📊 No recent data for this device - check connection'],
                'recommendations': ['🔌 Ensure device is connected and collecting data']
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(readings)
        
        # Safely convert timestamp to datetime
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'] >= 5
        except Exception:
            # Fallback if timestamp conversion fails
            df['hour'] = 12  # Default to noon
            df['day_of_week'] = 1  # Default to Tuesday
            df['is_weekend'] = False
        
        # Calculate statistics
        stats = self._calculate_device_stats(df)
        
        # Generate AI insights
        insights = self._generate_device_insights(device_id, df, stats)
        
        # Convert numpy types to Python types for JSON serialization
        stats_json = {}
        for key, value in stats.items():
            if hasattr(value, 'item'):  # numpy scalar
                stats_json[key] = value.item()
            else:
                stats_json[key] = value
        
        # Clean up any NaN or infinite values
        import math
        for key, value in stats_json.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    stats_json[key] = 0.0
        
        return {
            'device_id': device_id,
            'analysis_period_days': days,
            'statistics': stats_json,
            'insights': insights,
            'recommendations': self._generate_recommendations(device_id, df, stats)
        }
    
    def analyze_home_energy(self, days: int = 7) -> Dict:
        """Analyze overall home energy consumption"""
        try:
            all_readings = self.db.get_recent_readings(hours=days*24)
            
            if not all_readings:
                # Return basic structure instead of error
                return {
                    "analysis_period_days": days,
                    "total_devices": 7,
                    "total_energy_kwh": 0.0,
                    "total_cost": 0.0,
                    "peak_hours": [18, 19, 20],
                    "device_summary": {},
                    "insights": ["🏠 No recent data available - start collecting energy data to see insights"],
                    "recommendations": ["🔌 Connect your energy monitoring devices to begin analysis"]
                }
            
            df = pd.DataFrame(all_readings)
            
            # Safely convert timestamp to datetime
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
            except Exception:
                # Fallback if timestamp conversion fails
                df['hour'] = 12  # Default to noon
        
            # Group by device and time
            device_summary = df.groupby('device_name').agg({
                'power_watts': ['mean', 'max', 'sum'],
                'cost': 'sum'
            }).round(2)
            
            # Time-based analysis
            hourly_usage = df.groupby('hour')['power_watts'].mean()
            peak_hours = hourly_usage.nlargest(3).index.tolist()
            
            # Generate home-level insights
            home_insights = self._generate_home_insights(df, device_summary, peak_hours)
            
            # Convert device_summary to a more JSON-friendly format
            device_summary_dict = {}
            for device in device_summary.index:
                device_summary_dict[device] = {
                    'avg_power_watts': device_summary.loc[device, ('power_watts', 'mean')],
                    'max_power_watts': device_summary.loc[device, ('power_watts', 'max')],
                    'total_power_sum': device_summary.loc[device, ('power_watts', 'sum')],
                    'total_cost': device_summary.loc[device, ('cost', 'sum')]
                }
            
            return {
                'analysis_period_days': days,
                'total_devices': df['device_name'].nunique(),
                'total_energy_kwh': round(df['energy_kwh'].sum(), 4),
                'total_cost': round(df['cost'].sum(), 4),
                'peak_hours': peak_hours,
                'device_summary': device_summary_dict,
                'insights': home_insights,
                'recommendations': self._generate_home_recommendations(df, device_summary)
            }
        except Exception as e:
            # Return fallback data instead of error
            return {
                "analysis_period_days": days,
                "total_devices": 7,
                "total_energy_kwh": 0.0,
                "total_cost": 0.0,
                "peak_hours": [18, 19, 20],
                "device_summary": {},
                "insights": [f"⚠️ Analysis temporarily unavailable - collecting data..."],
                "recommendations": ["🔄 Please try refreshing the page in a moment"]
            }
    
    def _calculate_device_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate statistical measures for a device"""
        return {
            'avg_power_watts': df['power_watts'].mean(),
            'max_power_watts': df['power_watts'].max(),
            'min_power_watts': df['power_watts'].min(),
            'total_energy_kwh': df['energy_kwh'].sum(),
            'total_cost': df['cost'].sum(),
            'usage_hours_per_day': len(df[df['power_watts'] > df['power_watts'].mean() * 0.1]) / 7,
            'peak_usage_hour': df.groupby('hour')['power_watts'].mean().idxmax(),
            'weekend_vs_weekday_ratio': self._calculate_weekend_ratio(df),
            'efficiency_score': self._calculate_efficiency_score(df)
        }
    
    def _calculate_efficiency_score(self, df: pd.DataFrame) -> float:
        """Calculate an efficiency score (0-100) based on usage patterns"""
        import math
        
        if df.empty or len(df) < 2:
            return 50.0  # Default score for insufficient data
        
        try:
            power_variance = df['power_watts'].var()
            mean_power = df['power_watts'].mean()
            
            # Handle NaN or invalid values
            if math.isnan(power_variance) or math.isnan(mean_power):
                return 50.0
            
            # Lower variance relative to mean = more efficient usage
            if mean_power > 0:
                consistency_score = max(0, 100 - (power_variance / mean_power))
            else:
                consistency_score = 50
            
            # Handle NaN from calculation
            if math.isnan(consistency_score):
                consistency_score = 50
            
            # Penalize very high standby power
            standby_power = df['power_watts'].quantile(0.1)
            if math.isnan(standby_power):
                standby_power = 0
                
            standby_penalty = min(20, standby_power / 10)  # Penalty for high standby
            
            efficiency = max(0, min(100, consistency_score - standby_penalty))
            
            # Final check for NaN
            if math.isnan(efficiency):
                return 50.0
                
            return round(float(efficiency), 1)
            
        except Exception:
            return 50.0  # Safe fallback
    
    def _calculate_weekend_ratio(self, df: pd.DataFrame) -> float:
        """Calculate weekend vs weekday usage ratio safely"""
        import math
        
        try:
            if df.empty or 'is_weekend' not in df.columns:
                return 1.0
            
            weekend_data = df[df['is_weekend']]['power_watts']
            weekday_data = df[~df['is_weekend']]['power_watts']
            
            if len(weekend_data) == 0 or len(weekday_data) == 0:
                return 1.0
            
            weekend_mean = weekend_data.mean()
            weekday_mean = weekday_data.mean()
            
            if math.isnan(weekend_mean) or math.isnan(weekday_mean) or weekday_mean == 0:
                return 1.0
            
            ratio = weekend_mean / weekday_mean
            
            if math.isnan(ratio) or math.isinf(ratio):
                return 1.0
            
            return round(float(ratio), 2)
            
        except Exception:
            return 1.0
    
    def _generate_device_insights(self, device_id: str, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate AI-powered insights for a device"""
        if self.use_mock_ai:
            return self._mock_device_insights(device_id, df, stats)
        else:
            return self._gpt_oss_device_insights(device_id, df, stats)
    
    def _mock_device_insights(self, device_id: str, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate mock insights that simulate gpt-oss analysis - FAST VERSION"""
        device_name = df['device_name'].iloc[0] if not df.empty else device_id
        insights = []
        
        # Quick insights based on device type and power
        avg_power = stats['avg_power_watts']
        efficiency = stats['efficiency_score']
        # Calculate realistic daily cost based on average power
        daily_kwh = (avg_power * 24) / 1000  # Convert watts to daily kWh
        daily_cost = daily_kwh * config.ELECTRICITY_RATE
        
        # Device-specific quick insights - simplified for laymen
        # NOTE: Order matters! More specific patterns first to avoid false matches
        device_lower = device_name.lower()
        
        if 'washing' in device_lower or 'washer' in device_lower or ('wash' in device_lower and 'machine' in device_lower):
            insights.extend([
                f"🧺 Your washing machine uses {avg_power:.0f} watts per cycle",
                f"💰 Daily cost: ${daily_cost:.2f}",
                "❄️ Use cold water for 90% energy savings - modern detergents work great in cold!"
            ])
        elif 'dishwasher' in device_lower:
            insights.extend([
                f"🍽️ Dishwasher uses {avg_power:.0f} watts per cycle",
                f"💰 Daily cost: ${daily_cost:.2f}",
                "💡 Skip heated dry - open door instead to save 15% energy per load"
            ])
        elif 'dryer' in device_lower or 'clothes dryer' in device_lower:
            # Smart power-based dryer messages
            if avg_power > 2500:
                power_msg = f"👕 Your {device_name} uses {avg_power:.0f} watts - High power usage detected, consider shorter cycles"
            elif avg_power > 500:
                power_msg = f"👕 Your {device_name} uses {avg_power:.0f} watts - Normal operation, efficient drying cycle"
            else:
                power_msg = f"👕 Your {device_name} uses {avg_power:.0f} watts - Low power mode or cycle complete"
            
            insights.extend([
                power_msg,
                f"💰 Daily cost: ${daily_cost:.2f} (one of your highest energy users)",
                f"🔥 {'Heavy usage detected' if stats['usage_hours_per_day'] > 2 else 'Moderate usage'} - clean lint filter for 30% better efficiency"
            ])
        elif 'water heater' in device_lower:
            temp_f = 120
            temp_c = round((temp_f - 32) * 5/9, 1)
            insights.extend([
                f"🚿 Water heater uses {avg_power:.0f} watts to keep water hot",
                f"💰 Daily cost: ${daily_cost:.2f} (runs 24/7 to maintain temperature)",
                f"🌡️ Set to {temp_f}°F ({temp_c}°C) - hot enough for safety, saves energy vs higher temps"
            ])
        elif 'air conditioning' in device_lower or 'air conditioner' in device_lower or (device_lower.startswith('ac ') or device_lower.endswith(' ac') or device_lower == 'ac'):
            current_temp = 72  # Assume typical setting
            save_temp = current_temp + 2
            save_temp_c = round((save_temp - 32) * 5/9, 1)
            insights.extend([
                f"🌡️ AC system uses {avg_power:.0f} watts - {'Working very hard' if avg_power > 2000 else 'Normal operation'}",
                f"💰 Daily cost: ${daily_cost:.2f} (likely your biggest energy expense)",
                f"💡 Set to {save_temp}°F ({save_temp_c}°C) instead of {current_temp}°F to save 10-15% on bills"
            ])
        elif 'fridge' in device_lower or 'refrigerator' in device_lower:
            temp_f = 37
            temp_c = round((temp_f - 32) * 5/9, 1)
            insights.extend([
                f"❄️ Your fridge uses {avg_power:.0f} watts on average - {'Great! Very efficient' if avg_power < 150 else 'Higher than typical - may need maintenance'}",
                f"💰 Costs about ${daily_cost:.2f} per day to run",
                f"🌡️ Best temperature: {temp_f}°F ({temp_c}°C) for food safety and efficiency"
            ])
        elif 'tv' in device_lower or 'television' in device_lower:
            insights.extend([
                f"📺 Your TV uses {avg_power:.0f} watts - {'Excellent! Very energy efficient' if avg_power < 100 else 'Consider newer energy-saving model'}",
                f"💰 Daily cost: about ${daily_cost:.2f}",
                f"⏰ {'Good job keeping standby power low!' if avg_power < 50 else 'Tip: Use a power strip to cut standby power'}"
            ])
        elif 'computer' in device_lower or 'pc' in device_lower or 'laptop' in device_lower:
            insights.extend([
                f"🖥️ Your computer uses {avg_power:.0f} watts on average",
                f"💰 Running cost: ${daily_cost:.2f} per day",
                f"💡 {'Desktop system detected' if avg_power > 200 else 'Laptop or efficient system'} - sleep mode can save 80% energy"
            ])
        elif 'microwave' in device_lower:
            insights.extend([
                f"🔥 Microwave peak power: {stats['max_power_watts']:.0f} watts when cooking",
                f"💰 Very low daily cost: ${daily_cost:.2f} (only uses power when cooking)",
                "✅ One of your most efficient appliances - no standby power waste!"
            ])
            current_temp = 72  # Assume typical setting
            save_temp = current_temp + 2
            save_temp_c = round((save_temp - 32) * 5/9, 1)
            insights.extend([
                f"🌡️ AC system uses {avg_power:.0f} watts - {'Working very hard' if avg_power > 2000 else 'Normal operation'}",
                f"💰 Daily cost: ${daily_cost:.2f} (likely your biggest energy expense)",
                f"💡 Set to {save_temp}°F ({save_temp_c}°C) instead of {current_temp}°F to save 10-15% on bills"
            ])
        elif 'heater' in device_lower or 'heating' in device_lower:
            insights.extend([
                f"🔥 Heater uses {avg_power:.0f} watts when running",
                f"💰 Daily heating cost: ${daily_cost:.2f}",
                "🌡️ Lower by just 1°F (0.5°C) to save 5% on heating bills"
            ])
        elif 'water heater' in device_lower:
            temp_f = 120
            temp_c = round((temp_f - 32) * 5/9, 1)
            insights.extend([
                f"🚿 Water heater uses {avg_power:.0f} watts to keep water hot",
                f"💰 Daily cost: ${daily_cost:.2f} (runs 24/7 to maintain temperature)",
                f"🌡️ Set to {temp_f}°F ({temp_c}°C) - hot enough for safety, saves energy vs higher temps"
            ])
        elif 'dishwasher' in device_lower:
            insights.extend([
                f"🍽️ Dishwasher uses {avg_power:.0f} watts per cycle",
                f"💰 Daily cost: ${daily_cost:.2f}",
                "💡 Skip heated dry - open door instead to save 15% energy per load"
            ])
        elif 'oven' in device_lower:
            insights.extend([
                f"🍳 Oven uses {avg_power:.0f} watts when cooking",
                f"💰 Daily cost: ${daily_cost:.2f}",
                "🔥 Very efficient for cooking multiple items at once - batch your baking!"
            ])
        else:
            # Generic insights - simplified
            insights.extend([
                f"⚡ This device uses {avg_power:.0f} watts on average",
                f"💰 Daily cost: about ${daily_cost:.2f}",
                f"📊 Efficiency rating: {efficiency:.0f}/100 {'(Good!)' if efficiency > 60 else '(Could be better)'}"
            ])
        
        return insights[:3]  # Return top 3 for speed
    
    def _generate_recommendations(self, device_id: str, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate actionable recommendations - FAST VERSION"""
        device_name = df['device_name'].iloc[0] if not df.empty else device_id
        avg_power = stats['avg_power_watts']
        device_lower = device_name.lower()
        
        # Quick device-specific recommendations - simplified for laymen
        # NOTE: Order matters! More specific patterns first to avoid false matches
        if 'washing' in device_lower or 'washer' in device_lower or ('wash' in device_lower and 'machine' in device_lower):
            return [
                "❄️ Use cold water for 90% of loads - modern detergents work great!",
                "👕 Wash full loads when possible - same energy for more clothes",
                "🌀 Use high-speed spin to remove more water before drying"
            ]
        elif 'dishwasher' in device_lower:
            return [
                "🌬️ Skip 'Heated Dry' - just open door when done, saves 15% per load",
                "🍽️ Run only full loads - same energy whether half or completely full",
                "💧 Use 'Eco' or 'Energy Saver' cycle when dishes aren't very dirty"
            ]
        elif 'dryer' in device_lower or 'clothes dryer' in device_lower:
            return [
                "🧹 Clean lint filter before EVERY load - improves efficiency by 30%",
                "👕 Don't over-dry clothes - use moisture sensor if available",
                "🌬️ Clean dryer vent outside annually - blocked vents waste huge energy",
                "🔥 Dry full loads but don't overpack - clothes need room to tumble"
            ]
        elif 'water heater' in device_lower:
            temp_f = 120
            temp_c = round((temp_f - 32) * 5/9, 1)
            return [
                f"🌡️ Set temperature to {temp_f}°F ({temp_c}°C) - safe and efficient",
                "🚿 Take shorter showers - each minute saves significant energy",
                "🔧 Insulate hot water pipes to reduce heat loss"
            ]
        elif 'air conditioning' in device_lower or 'air conditioner' in device_lower or (device_lower.startswith('ac ') or device_lower.endswith(' ac') or device_lower == 'ac'):
            return [
                "🌡️ Raise temperature by just 2°F (1°C) - you won't notice but will save 10-15%",
                "🔧 Change air filter monthly - dirty filters make AC work harder",
                "🌬️ Use ceiling fans to feel cooler at higher temperatures"
            ]
        elif 'tv' in device_lower or 'television' in device_lower:
            return [
                "💡 Turn on 'Eco Mode' in settings - saves 20-30% energy automatically",
                "⏰ Set sleep timer so TV doesn't run all night",
                "🔌 Use a power strip to completely cut power when not watching"
            ]
        elif 'computer' in device_lower or 'pc' in device_lower or 'laptop' in device_lower:
            return [
                "💤 Set computer to sleep after 15 minutes of inactivity",
                "🖥️ Turn off monitor separately - it uses lots of power",
                "⚙️ Use 'Power Saver' mode in Windows settings"
            ]
        elif 'fridge' in device_lower or 'refrigerator' in device_lower:
            temp_f = 37
            temp_c = round((temp_f - 32) * 5/9, 1)
            return [
                f"🌡️ Set fridge to {temp_f}°F ({temp_c}°C) - perfect for food safety and efficiency",
                "🧽 Clean the coils on the back/bottom every 6 months",
                "🚪 Check door seals - should hold a dollar bill tightly when closed"
            ]
        elif 'microwave' in device_lower:
            return [
                "✅ Already very efficient - only uses power when cooking",
                "🔌 Unplug when not in use to save a few watts of standby power",
                "🍽️ Use for reheating instead of oven - much more efficient"
            ]

        elif 'oven' in device_lower:
            return [
                "🍳 Cook multiple items at once - very efficient for batch cooking",
                "🔥 Don't preheat longer than needed - most foods don't need it",
                "🚪 Keep door closed while cooking - each peek loses 25°F (14°C)"
            ]
        elif 'heater' in device_lower or 'heating' in device_lower:
            return [
                "🌡️ Lower temperature by 1°F (0.5°C) - saves 5% on heating bills",
                "🔧 Change furnace filter monthly during heating season",
                "🏠 Close vents in unused rooms to focus heat where needed"
            ]
        else:
            return [
                "⚡ Look for 'Energy Saver' or 'Eco' modes in device settings",
                "🔌 Use smart plugs to automatically turn off when not needed",
                "📊 Monitor usage patterns to find opportunities to save"
            ]
    
    def _generate_home_insights(self, df: pd.DataFrame, device_summary: pd.DataFrame, peak_hours: List[int]) -> List[str]:
        """Generate home-level insights"""
        insights = []
        
        total_cost = df['cost'].sum()
        total_kwh = df['energy_kwh'].sum()
        
        # Peak usage insights
        peak_hours_str = ", ".join([f"{h}:00" for h in peak_hours])
        insights.append(f"🏠 Your home's peak energy usage occurs at {peak_hours_str}")
        
        # Cost insights - Calculate realistic monthly estimate
        # Get average power consumption and extrapolate to monthly usage
        avg_power_watts = df['power_watts'].mean()
        # Assume devices run similar patterns daily
        daily_kwh = (avg_power_watts * 24) / 1000  # Convert watts to daily kWh
        monthly_kwh = daily_kwh * 30
        monthly_estimate = monthly_kwh * config.ELECTRICITY_RATE
        insights.append(f"💰 Estimated monthly electricity cost: ${monthly_estimate:.2f} based on current usage")
        
        # Device contribution insights
        # This would work better with the actual device_summary structure
        insights.append(f"⚡ Total energy consumption: {total_kwh:.2f} kWh over the analysis period")
        
        # Usage pattern insights
        weekend_usage = df[df['timestamp'].dt.dayofweek >= 5]['power_watts'].mean()
        weekday_usage = df[df['timestamp'].dt.dayofweek < 5]['power_watts'].mean()
        
        if weekend_usage > weekday_usage * 1.2:
            insights.append("📈 Weekend energy usage is significantly higher than weekdays")
        elif weekend_usage < weekday_usage * 0.8:
            insights.append("📉 Weekday energy usage is higher - likely due to work-from-home activities")
        
        return insights
    
    def _generate_home_recommendations(self, df: pd.DataFrame, device_summary: pd.DataFrame) -> List[str]:
        """Generate home-level recommendations - simplified for laymen"""
        recommendations = []
        
        # Calculate realistic monthly estimate
        avg_power_watts = df['power_watts'].mean()
        daily_kwh = (avg_power_watts * 24) / 1000  # Convert watts to daily kWh
        monthly_kwh = daily_kwh * 30
        monthly_estimate = monthly_kwh * config.ELECTRICITY_RATE
        
        # High-level recommendations based on cost
        if monthly_estimate > 240:  # $8/day * 30 days
            recommendations.append(f"💰 Your ${monthly_estimate:.0f}/month electricity is high - biggest savings: AC/heating, water heater, dryer")
        elif monthly_estimate > 150:  # $5/day * 30 days
            recommendations.append(f"💡 Your ${monthly_estimate:.0f}/month electricity could be lower - focus on your biggest energy users first")
        
        # Practical recommendations
        recommendations.append("🔌 Unplug devices when not in use - 'phantom loads' can add $100+ per year")
        recommendations.append("💡 Switch to LED bulbs if you haven't - they use 75% less energy than old bulbs")
        
        # Seasonal recommendations - simplified
        month = datetime.now().month
        if month in [6, 7, 8]:  # Summer
            recommendations.append("🌬️ Summer tip: Use fans and raise AC to 78°F (26°C) - you'll barely notice but save big")
        elif month in [12, 1, 2]:  # Winter
            temp_f = 68
            temp_c = round((temp_f - 32) * 5/9, 1)
            recommendations.append(f"🔥 Winter tip: Set heat to {temp_f}°F ({temp_c}°C) and wear a sweater - saves 10% per degree")
        elif month in [3, 4, 5, 9, 10, 11]:  # Spring/Fall
            recommendations.append("🌤️ Great weather for opening windows instead of using AC or heat!")
        
        return recommendations[:4]
    
    def _gpt_oss_device_insights(self, device_id: str, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate insights using actual gpt-oss model"""
        if self.model is None or self.use_mock_ai:
            return self._mock_device_insights(device_id, df, stats)
        
        try:
            prompt = self._create_analysis_prompt(device_id, df, stats)
            
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if hasattr(self, 'device'):
                inputs = inputs.to(self.device)
            
            # Generate response with gpt-oss
            if not TORCH_AVAILABLE:
                raise ImportError("torch not available")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 200,  # Add 200 tokens for response
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the generated part (after the prompt)
            generated_text = response[len(prompt):].strip()
            
            # Parse the AI response into insights
            insights = self._parse_ai_response(generated_text)
            
            return insights if insights else self._mock_device_insights(device_id, df, stats)
            
        except Exception as e:
            logger.warning(f"Error generating gpt-oss insights: {e}")
            return self._mock_device_insights(device_id, df, stats)
    
    def _create_analysis_prompt(self, device_id: str, df: pd.DataFrame, stats: Dict) -> str:
        """Create a prompt for gpt-oss analysis"""
        device_name = df['device_name'].iloc[0] if not df.empty else device_id
        
        prompt = f"""
        Analyze the energy consumption data for {device_name}:
        
        Statistics:
        - Average power: {stats['avg_power_watts']:.1f}W
        - Peak power: {stats['max_power_watts']:.1f}W
        - Total energy: {stats['total_energy_kwh']:.2f} kWh
        - Peak usage hour: {stats['peak_usage_hour']}:00
        - Efficiency score: {stats['efficiency_score']}/100
        - Weekend vs weekday ratio: {stats['weekend_vs_weekday_ratio']:.2f}
        
        Provide 3-4 specific insights about this device's energy usage patterns and efficiency.
        Focus on actionable observations that help the user understand their energy consumption.
        """
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> List[str]:
        """Parse AI-generated response into structured insights"""
        try:
            # Split response into lines and clean up
            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            
            insights = []
            for line in lines:
                # Look for bullet points, numbered items, or sentences
                if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.')):
                    # Remove bullet point markers
                    clean_line = line.lstrip('•-*1234567890. ').strip()
                    if clean_line and len(clean_line) > 10:  # Minimum meaningful length
                        insights.append(clean_line)
                elif len(line) > 20 and '.' in line:  # Complete sentences
                    insights.append(line)
            
            # Limit to top 4 insights
            return insights[:4] if insights else []
            
        except Exception as e:
            logger.warning(f"Error parsing AI response: {e}")
            return []
    
    def generate_daily_report(self) -> Dict:
        """Generate a daily energy report with AI insights"""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            readings = self.db.get_recent_readings(hours=24)
            
            if not readings:
                today = datetime.now().strftime('%Y-%m-%d')
                return {
                    'summary': {
                        'date': today,
                        'total_energy_kwh': 0.0,
                        'total_cost': 0.0,
                        'peak_power_watts': 0.0
                    },
                    'top_energy_consumers': {},
                    'insights': ['📊 No data available for today - start collecting to see daily insights'],
                    'recommendations': ['🚀 Begin energy monitoring to track daily usage']
                }
            
            df = pd.DataFrame(readings)
            
            # Safely convert timestamp to datetime
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except Exception:
                pass  # Continue without datetime conversion
            
            # Clean numeric values
            import math
            def clean_value(val):
                if isinstance(val, (int, float)):
                    if math.isnan(val) or math.isinf(val):
                        return 0.0
                    return float(val)
                return val
            
            # Daily summary with cleaned values
            daily_summary = {
                'date': yesterday.strftime('%Y-%m-%d'),
                'total_energy_kwh': clean_value(df['energy_kwh'].sum()),
                'total_cost': clean_value(df['cost'].sum()),
                'peak_power_watts': clean_value(df['power_watts'].max()),
                'average_power_watts': clean_value(df['power_watts'].mean())
            }
            
            # Device rankings
            device_costs = df.groupby('device_name')['cost'].sum().sort_values(ascending=False)
            top_consumers = {k: clean_value(v) for k, v in device_costs.head(3).to_dict().items()}
            
            # Generate insights for the day
            daily_insights = self._generate_daily_insights(df, daily_summary, top_consumers)
            
            return {
                'summary': daily_summary,
                'top_energy_consumers': top_consumers,
                'insights': daily_insights,
                'recommendations': self._generate_daily_recommendations(df, daily_summary)
            }
            
        except Exception as e:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            return {
                'summary': {
                    'date': today,
                    'total_energy_kwh': 0.0,
                    'total_cost': 0.0,
                    'peak_power_watts': 0.0
                },
                'top_energy_consumers': {},
                'insights': ['📊 Daily report is being prepared - check back soon!'],
                'recommendations': ['🚀 Continue monitoring to see daily insights']
            }
    
    
    def _generate_daily_insights(self, df: pd.DataFrame, summary: Dict, top_consumers: Dict) -> List[str]:
        """Generate insights for daily report - simplified for laymen"""
        insights = []
        
        # Cost insight with monthly projection
        daily_cost = summary['total_cost']
        monthly_estimate = daily_cost * 30
        insights.append(f"💰 Yesterday cost ${daily_cost:.2f} - if every day was like this, your monthly bill would be ${monthly_estimate:.0f}")
        
        # Top consumer insight with helpful context
        if top_consumers:
            top_device = list(top_consumers.keys())[0]
            top_cost = list(top_consumers.values())[0]
            percentage = (top_cost / daily_cost * 100) if daily_cost > 0 else 0
            insights.append(f"🔌 {top_device} used the most energy yesterday (${top_cost:.2f} - {percentage:.0f}% of your total)")
        
        # Usage pattern insight - with proper datetime handling
        try:
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                peak_hour = df.groupby(df['timestamp'].dt.hour)['power_watts'].mean().idxmax()
                
                # Convert to 12-hour format for easier understanding
                if peak_hour == 0:
                    time_str = "midnight"
                elif peak_hour == 12:
                    time_str = "noon"
                elif peak_hour < 12:
                    time_str = f"{peak_hour}:00 AM"
                else:
                    time_str = f"{peak_hour-12}:00 PM"
                    
                insights.append(f"📊 Your home used the most energy around {time_str}")
            else:
                insights.append(f"📊 Energy monitoring is working great - data collected all day!")
        except Exception:
            insights.append(f"📊 Your energy usage patterns are being tracked successfully")
        
        return insights
    
    def _generate_daily_recommendations(self, df: pd.DataFrame, summary: Dict) -> List[str]:
        """Generate daily recommendations - actionable and simple"""
        recommendations = []
        
        daily_cost = summary['total_cost']
        
        if daily_cost > 5.0:
            recommendations.append("💡 Yesterday was expensive! Focus on your biggest energy users: AC, heating, water heater, dryer")
        elif daily_cost > 3.0:
            recommendations.append("⚡ Look for devices that might have been left on longer than needed")
        else:
            recommendations.append("✅ Great job keeping energy costs reasonable yesterday!")
        
        # Always include a practical tip
        recommendations.append("🔍 Check which devices ran the longest - those are your best opportunities to save")
        
        # Add seasonal tip
        month = datetime.now().month
        if month in [6, 7, 8]:  # Summer
            recommendations.append("🌡️ Hot weather tip: Every degree you raise the AC saves 6-8% on cooling costs")
        elif month in [12, 1, 2]:  # Winter
            recommendations.append("🔥 Cold weather tip: Lower the heat by 1°F when sleeping or away from home")
        else:
            recommendations.append("🌤️ Nice weather - perfect time to give your AC and heater a break!")
        
        return recommendations

    def generate_monthly_analysis(self) -> Dict:
        """Generate comprehensive monthly analysis with multi-month support"""
        try:
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            # Get data for current month
            current_month_data = self._get_month_data(current_year, current_month)
            
            # Get data for previous months (up to 12 months back)
            historical_months = []
            for i in range(1, 13):  # Look back up to 12 months
                month = current_month - i
                year = current_year
                if month <= 0:
                    month += 12
                    year -= 1
                
                month_data = self._get_month_data(year, month)
                if month_data['total_kwh'] > 0:  # Only include months with data
                    historical_months.append({
                        'year': year,
                        'month': month,
                        'month_name': datetime(year, month, 1).strftime('%B'),
                        'data': month_data
                    })
                
                # Removed 3-month limit - collect all available data for advanced 6+ month analysis
                # if len(historical_months) >= 3:  # Old limit removed
                #     break
            
            # Generate analysis based on available data
            analysis = self._generate_monthly_insights(current_month_data, historical_months)
            
            return {
                'current_month': {
                    'name': current_date.strftime('%B'),
                    'year': current_year,
                    'data': current_month_data
                },
                'historical_months': historical_months,
                'projections': analysis['projections'],
                'insights': analysis['insights'],
                'predictions': analysis['predictions'],
                'recommendations': analysis['recommendations'],
                'comparison': analysis['comparison']
            }
            
        except Exception as e:
            from datetime import datetime
            current_date = datetime.now()
            return {
                'current_month': {
                    'name': current_date.strftime('%B'),
                    'year': current_date.year,
                    'data': {'top_consumers': {}}
                },
                'historical_months': [],
                'projections': {
                    'projected_kwh': '0.0',
                    'projected_cost': '$0.00',
                    'current_kwh': '0.0',
                    'days_elapsed': 1,
                    'peak_power': '0.0',
                    'active_devices': 0
                },
                'insights': ['📊 Monthly analysis is being prepared - check back soon!'],
                'predictions': ['🔮 Predictions will appear as more data is collected'],
                'recommendations': ['🚀 Continue monitoring to unlock monthly insights'],
                'comparison': {
                    'last_month_name': None,
                    'last_month_cost': '$0.00',
                    'change_percent': 0,
                    'change_direction': 'same'
                }
            }
    
    def _get_month_data(self, year: int, month: int) -> Dict:
        """Get aggregated data for a specific month"""
        try:
            # Get all readings for the month using recent readings (simplified for demo)
            readings = self.db.get_recent_readings(hours=24 * 30)  # Last 30 days as proxy
            
            if not readings:
                return {
                    'total_kwh': 0,
                    'total_cost': 0,
                    'avg_daily_kwh': 0,
                    'peak_power': 0,
                    'active_devices': 0,
                    'top_consumers': {}
                }
            
            df = pd.DataFrame(readings)
            
            # Calculate monthly totals
            total_kwh = df['energy_kwh'].sum()
            total_cost = df['cost'].sum()
            peak_power = df['power_watts'].max()
            
            # Calculate daily average
            avg_daily_kwh = total_kwh / 30  # Simplified
            
            # Get active devices count
            active_devices = df['device_id'].nunique()
            
            # Top consumers
            device_costs = df.groupby('device_name')['cost'].sum().sort_values(ascending=False)
            top_consumers = device_costs.head(5).to_dict()
            
            return {
                'total_kwh': round(total_kwh, 2),
                'total_cost': round(total_cost, 2),
                'avg_daily_kwh': round(avg_daily_kwh, 2),
                'peak_power': round(peak_power, 1),
                'active_devices': active_devices,
                'top_consumers': top_consumers
            }
            
        except Exception as e:
            return {
                'total_kwh': 0,
                'total_cost': 0,
                'avg_daily_kwh': 0,
                'peak_power': 0,
                'active_devices': 0,
                'top_consumers': {}
            }
    
    def _generate_monthly_insights(self, current_data: Dict, historical_months: List[Dict]) -> Dict:
        """Generate AI insights based on current and historical data - SUPER SIMPLE for laymen"""
        insights = []
        predictions = []
        recommendations = []
        comparison = {}
        
        # Current month projections (simple for demo, but realistic)
        current_kwh = current_data['total_kwh']
        current_cost = current_data['total_cost']
        
        # Project full month based on current data
        current_date = datetime.now()
        days_elapsed = current_date.day
        days_in_month = 30  # Simplified
        
        if days_elapsed > 0:
            projected_kwh = (current_kwh / days_elapsed) * days_in_month
            projected_cost = (current_cost / days_elapsed) * days_in_month
        else:
            projected_kwh = current_kwh
            projected_cost = current_cost
        
        projections = {
            'projected_kwh': round(projected_kwh, 1),
            'projected_cost': round(projected_cost, 2),
            'current_kwh': round(current_kwh, 2),
            'current_cost': round(current_cost, 2),
            'days_elapsed': days_elapsed,
            'peak_power': current_data['peak_power'],
            'active_devices': current_data['active_devices']
        }
        
        # SUPER SIMPLE insights that anyone can understand
        if projected_cost > 200:
            insights.append(f"💰 Heads up! Your bill might hit ${projected_cost:.0f} this month - that's pretty high")
            recommendations.append("🔥 Your AC or heater is probably the biggest culprit - try adjusting by just 2-3 degrees")
        elif projected_cost > 150:
            insights.append(f"💰 Your monthly bill looks like it'll be around ${projected_cost:.0f} - higher than average")
            recommendations.append("💡 Focus on the big stuff: AC, water heater, dryer - small changes = big savings")
        elif projected_cost > 100:
            insights.append(f"💰 Your bill should be around ${projected_cost:.0f} this month - pretty normal for most homes")
            recommendations.append("⚡ You're doing okay! Try unplugging stuff when you're not using it")
        else:
            insights.append(f"💰 Nice! Your bill looks like only ${projected_cost:.0f} this month - you're really efficient")
            recommendations.append("🌟 You're already doing great! Maybe help your neighbors save energy too")
        
        # Simple power usage insights
        if current_data['peak_power'] > 4000:
            insights.append(f"⚡ Whoa! You hit {current_data['peak_power']:.0f} watts at peak - that's like running everything at once")
            recommendations.append("🔄 Try spreading out when you use big appliances - don't run dryer + dishwasher + AC together")
        elif current_data['peak_power'] > 2000:
            insights.append(f"⚡ Your peak usage was {current_data['peak_power']:.0f} watts - pretty typical for a home")
        else:
            insights.append(f"⚡ Your peak was only {current_data['peak_power']:.0f} watts - you're not overloading your system")
        
        # Device monitoring insight
        if current_data['active_devices'] >= 5:
            insights.append(f"🏠 You're tracking {current_data['active_devices']} devices - awesome coverage!")
        else:
            insights.append(f"🏠 Monitoring {current_data['active_devices']} devices - consider adding more for better insights")
        
        # Advanced multi-month comparison (handles 6+ months with sophisticated analysis)
        if len(historical_months) >= 6:
            # ADVANCED 6+ MONTH ANALYSIS
            last_month = historical_months[0]
            
            # Calculate 6-month average
            six_month_costs = [m['data']['total_cost'] for m in historical_months[:6]]
            avg_6_month_cost = sum(six_month_costs) / 6
            
            # Seasonal analysis - compare same season from previous year if available
            current_season = self._get_season(datetime.now().month)
            seasonal_months = [m for m in historical_months if self._get_season(m['month']) == current_season]
            
            comparison = {
                'last_month_name': last_month['month_name'],
                'last_month_cost': round(last_month['data']['total_cost'], 2),
                'change_percent': round(((projected_cost - avg_6_month_cost) / avg_6_month_cost) * 100, 1) if avg_6_month_cost > 0 else 0,
                'change_direction': 'increase' if projected_cost > avg_6_month_cost else 'decrease',
                'months_of_data': len(historical_months),
                'seasonal_data': len(seasonal_months)
            }
            
            # Advanced insights with 6+ months
            if seasonal_months and len(seasonal_months) >= 2:
                seasonal_avg = sum(m['data']['total_cost'] for m in seasonal_months) / len(seasonal_months)
                seasonal_change = ((projected_cost - seasonal_avg) / seasonal_avg) * 100 if seasonal_avg > 0 else 0
                
                if abs(seasonal_change) > 20:
                    insights.append(f"🌡️ This {current_season} you're using {abs(seasonal_change):.0f}% {'more' if seasonal_change > 0 else 'less'} than last {current_season}")
                else:
                    insights.append(f"🌡️ Your {current_season} usage is consistent with last year - great predictability!")
            
            # Trend analysis
            recent_3_months = sum(m['data']['total_cost'] for m in historical_months[:3]) / 3
            older_3_months = sum(m['data']['total_cost'] for m in historical_months[3:6]) / 3
            trend = ((recent_3_months - older_3_months) / older_3_months) * 100 if older_3_months > 0 else 0
            
            if abs(trend) > 15:
                if trend > 0:
                    insights.append(f"📈 Your usage has been trending up {abs(trend):.0f}% over the last 6 months")
                    predictions.append("🔍 Consider what's changed: new appliances, different habits, or seasonal shifts")
                else:
                    insights.append(f"📉 Excellent! Your usage has been trending down {abs(trend):.0f}% over 6 months")
                    predictions.append("🌟 Your energy-saving efforts are paying off - keep it up!")
            
            # Advanced seasonal predictions
            predictions.append(f"🔮 With {len(historical_months)} months of data, I can predict your next 3 months will cost ${projected_cost * 3:.0f}")
            
            # Peak usage insights
            peak_months = sorted(historical_months, key=lambda x: x['data']['total_cost'], reverse=True)[:2]
            if peak_months:
                peak_month_names = [m['month_name'] for m in peak_months]
                predictions.append(f"⚡ Your highest usage months were {' and '.join(peak_month_names)} - plan ahead for similar periods")
                
        elif len(historical_months) >= 3:
            # Standard 3+ month analysis
            last_month = historical_months[0]
            two_months_ago = historical_months[1] 
            three_months_ago = historical_months[2]
            
            avg_historical_cost = (last_month['data']['total_cost'] + 
                                 two_months_ago['data']['total_cost'] + 
                                 three_months_ago['data']['total_cost']) / 3
            
            if avg_historical_cost > 0:
                change_vs_avg = ((projected_cost - avg_historical_cost) / avg_historical_cost) * 100
                
                comparison = {
                    'last_month_name': last_month['month_name'],
                    'last_month_cost': round(last_month['data']['total_cost'], 2),
                    'change_percent': round(change_vs_avg, 1),
                    'change_direction': 'increase' if change_vs_avg > 0 else 'decrease',
                    'months_of_data': len(historical_months)
                }
                
                if abs(change_vs_avg) > 25:
                    if change_vs_avg > 0:
                        insights.append(f"📈 This month is {abs(change_vs_avg):.0f}% higher than your 3-month average - something's different!")
                        predictions.append("🔍 Check if you're using AC/heat more, or if any appliances are running more often")
                    else:
                        insights.append(f"📉 Awesome! You're {abs(change_vs_avg):.0f}% lower than your 3-month average")
                        predictions.append("🌟 Whatever you're doing differently is working - keep it up!")
                
                # Seasonal predictions with 3+ months
                predictions.append("🌡️ With 3+ months of data, I can see your seasonal patterns forming")
                
        elif len(historical_months) >= 1:
            # Simple comparison with just last month
            last_month = historical_months[0]
            last_month_cost = last_month['data']['total_cost']
            
            if last_month_cost > 0:
                change_percent = ((projected_cost - last_month_cost) / last_month_cost) * 100
                
                comparison = {
                    'last_month_name': last_month['month_name'],
                    'last_month_cost': round(last_month_cost, 2),
                    'change_percent': round(change_percent, 1),
                    'change_direction': 'increase' if change_percent > 0 else 'decrease',
                    'months_of_data': 1
                }
                
                if abs(change_percent) > 15:
                    if change_percent > 0:
                        insights.append(f"📈 You're using {abs(change_percent):.0f}% more than {last_month['month_name']} - what changed?")
                        predictions.append("🤔 Think about what's different - weather, new appliances, or different habits?")
                    else:
                        insights.append(f"📉 Great! You're using {abs(change_percent):.0f}% less than {last_month['month_name']}")
                        predictions.append("🎉 You're improving! Keep doing whatever you changed")
        
        # Predictions based on data available
        if len(historical_months) == 0:
            predictions.append("📊 This is your first month! Keep collecting data for better predictions")
            predictions.append("🔮 After 2-3 months, I'll be able to spot patterns and give better tips")
        elif len(historical_months) < 3:
            predictions.append("📈 Getting better data! A few more months and I can predict seasonal changes")
        
        # Always practical recommendations that anyone can do
        if not any("unplug" in rec.lower() for rec in recommendations):
            recommendations.append("🔌 Unplug chargers and electronics when not using them - saves $10-20/month")
        
        if len(recommendations) < 3:
            recommendations.append("🌡️ Adjust your thermostat by 2-3 degrees - you won't notice but your wallet will!")
        
        return {
            'projections': projections,
            'insights': insights[:4],  # Keep most important
            'predictions': predictions[:3],  # Keep focused
            'recommendations': recommendations[:3],  # Keep actionable
            'comparison': comparison
        }
    
    def _get_season(self, month: int) -> str:
        """Get season name from month number"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "fall"
    
    def analyze_home_energy(self, days: int = 7) -> Dict:
        """Analyze home-wide energy patterns"""
        try:
            readings = self.db.get_recent_readings(hours=days * 24)
            
            if not readings:
                return {
                    'error': 'No data available for home analysis',
                    'total_devices': 0,
                    'total_energy_kwh': 0,
                    'total_cost': 0,
                    'peak_hours': [],
                    'device_summary': {},
                    'insights': ['Start collecting data to see home insights'],
                    'recommendations': ['Begin monitoring your devices for personalized recommendations']
                }
            
            df = pd.DataFrame(readings)
            
            # Calculate summary statistics
            total_energy = df['energy_kwh'].sum()
            total_cost = df['cost'].sum()
            total_devices = df['device_id'].nunique()
            
            # Find peak hours
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                hourly_usage = df.groupby(df['timestamp'].dt.hour)['power_watts'].mean()
                peak_hours = hourly_usage.nlargest(3).index.tolist()
            else:
                peak_hours = [18, 19, 20]  # Default evening hours
            
            # Device summary
            device_summary = {}
            for device_id in df['device_id'].unique():
                device_data = df[df['device_id'] == device_id]
                device_summary[device_id] = {
                    'avg_power_watts': device_data['power_watts'].mean(),
                    'total_energy_kwh': device_data['energy_kwh'].sum(),
                    'total_cost': device_data['cost'].sum()
                }
            
            # Generate simple insights
            insights = []
            recommendations = []
            
            daily_cost = total_cost / days
            monthly_estimate = daily_cost * 30
            
            insights.append(f"💰 Your average daily cost is ${daily_cost:.2f} - monthly estimate: ${monthly_estimate:.0f}")
            insights.append(f"🏠 Monitoring {total_devices} devices with {total_energy:.2f} kWh total usage")
            insights.append(f"⚡ Peak usage hours: {', '.join(map(str, peak_hours))}:00")
            
            recommendations.append("💡 Focus on your highest consuming devices for maximum savings")
            recommendations.append("🔌 Unplug devices when not in use to reduce standby power")
            recommendations.append("📊 Check individual device insights for specific recommendations")
            
            return {
                'total_devices': total_devices,
                'total_energy_kwh': round(total_energy, 4),
                'total_cost': round(total_cost, 4),
                'peak_hours': peak_hours,
                'device_summary': device_summary,
                'insights': insights,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'error': f'Failed to analyze home energy: {str(e)}',
                'total_devices': 0,
                'total_energy_kwh': 0,
                'total_cost': 0,
                'peak_hours': [],
                'device_summary': {},
                'insights': ['Unable to generate insights at this time'],
                'recommendations': ['Please try again later']
            }
    


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    analyzer = EnergyAIAnalyzer(use_mock_ai=True)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "device":
            device_id = sys.argv[2] if len(sys.argv) > 2 else "living_room_tv"
            result = analyzer.analyze_device_patterns(device_id)
            print(f"\n=== Device Analysis: {device_id} ===")
            print(json.dumps(result, indent=2, default=str))
        
        elif sys.argv[1] == "home":
            result = analyzer.analyze_home_energy()
            print("\n=== Home Energy Analysis ===")
            print(json.dumps(result, indent=2, default=str))
        
        elif sys.argv[1] == "daily":
            result = analyzer.generate_daily_report()
            print("\n=== Daily Energy Report ===")
            print(json.dumps(result, indent=2, default=str))
    
    else:
        print("Usage:")
        print("  python ai_analyzer.py device [device_id]")
        print("  python ai_analyzer.py home")
        print("  python ai_analyzer.py daily")