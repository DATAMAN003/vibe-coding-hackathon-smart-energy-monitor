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
        self.db = EnergyDatabase()
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
            return {"error": "No data available for analysis"}
        
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
        all_readings = self.db.get_recent_readings(hours=days*24)
        
        if not all_readings:
            return {"error": "No data available for home analysis"}
        
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
        
        # Device-specific quick insights
        device_lower = device_name.lower()
        
        if 'fridge' in device_lower:
            insights.extend([
                f"❄️ Fridge consuming {avg_power:.0f}W average - {'efficient' if avg_power < 150 else 'high for modern units'}",
                f"🔄 Shows {'good' if efficiency > 60 else 'poor'} cycling patterns",
                "💡 Keep temperature at 37°F for optimal efficiency"
            ])
        elif 'tv' in device_lower:
            insights.extend([
                f"📺 TV power usage: {avg_power:.0f}W - {'excellent standby' if avg_power < 10 else 'consider eco mode'}",
                f"⚡ Efficiency score: {efficiency}/100",
                "💡 Enable sleep timer to avoid overnight usage"
            ])
        elif 'computer' in device_lower:
            insights.extend([
                f"🖥️ Computer consuming {avg_power:.0f}W average",
                f"💼 {'High-performance' if avg_power > 300 else 'Standard'} system detected",
                "💡 Enable power management for 20% savings"
            ])
        elif 'microwave' in device_lower:
            insights.extend([
                f"🔥 Microwave shows burst usage patterns",
                f"⚡ Peak power: {stats['max_power_watts']:.0f}W",
                "💡 Efficient appliance - only uses power when cooking"
            ])
        elif 'ac' in device_lower or 'air' in device_lower:
            insights.extend([
                f"🌡️ AC system: {avg_power:.0f}W average",
                f"❄️ {'Working hard' if avg_power > 1000 else 'Moderate usage'}",
                "💡 Raise thermostat 2°F to save 10-15% energy"
            ])
        else:
            # Generic insights
            insights.extend([
                f"⚡ Average power consumption: {avg_power:.0f}W",
                f"📊 Efficiency score: {efficiency}/100",
                f"💰 Daily cost: ~${(stats['total_cost'] / 7):.3f}"
            ])
        
        return insights[:3]  # Return top 3 for speed
    
    def _generate_recommendations(self, device_id: str, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate actionable recommendations - FAST VERSION"""
        device_name = df['device_name'].iloc[0] if not df.empty else device_id
        avg_power = stats['avg_power_watts']
        device_lower = device_name.lower()
        
        # Quick device-specific recommendations
        if 'tv' in device_lower:
            return [
                "💡 Enable eco mode to save 20-30% energy",
                "⏰ Use sleep timer to prevent overnight usage"
            ]
        elif 'computer' in device_lower:
            return [
                "💤 Enable sleep mode when not in use",
                "⚙️ Adjust power management settings"
            ]
        elif 'fridge' in device_lower:
            return [
                "🌡️ Set temperature to 37°F for optimal efficiency",
                "🔧 Clean coils and check door seals"
            ]
        elif 'ac' in device_lower:
            return [
                "🌡️ Raise thermostat 2°F to save 10-15%",
                "🔧 Change air filters regularly"
            ]
        elif 'microwave' in device_lower:
            return [
                "✅ Already efficient - only uses power when cooking",
                "🔌 Unplug when not in use to eliminate standby power"
            ]
        else:
            return [
                "⚡ Monitor usage patterns for optimization",
                "🔌 Consider smart plugs for better control"
            ]
    
    def _generate_home_insights(self, df: pd.DataFrame, device_summary: pd.DataFrame, peak_hours: List[int]) -> List[str]:
        """Generate home-level insights"""
        insights = []
        
        total_cost = df['cost'].sum()
        total_kwh = df['energy_kwh'].sum()
        
        # Peak usage insights
        peak_hours_str = ", ".join([f"{h}:00" for h in peak_hours])
        insights.append(f"🏠 Your home's peak energy usage occurs at {peak_hours_str}")
        
        # Cost insights
        daily_cost = total_cost / 7
        monthly_estimate = daily_cost * 30
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
        """Generate home-level recommendations"""
        recommendations = []
        
        total_cost = df['cost'].sum()
        daily_cost = total_cost / 7
        
        # High-level recommendations
        if daily_cost > 5.0:
            recommendations.append("Consider a home energy audit to identify major efficiency opportunities")
        
        recommendations.append("Shift high-power activities to off-peak hours if your utility offers time-of-use rates")
        recommendations.append("Install smart power strips to eliminate phantom loads from electronics")
        
        # Seasonal recommendations
        month = datetime.now().month
        if month in [6, 7, 8]:  # Summer
            recommendations.append("Use fans to circulate air and raise AC thermostat settings")
        elif month in [12, 1, 2]:  # Winter
            recommendations.append("Lower water heater temperature and use programmable thermostats")
        
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
                return {"error": "No data available for daily report"}
            
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
            return {"error": f"Error generating daily report: {str(e)}"}
    
    
    def _generate_daily_insights(self, df: pd.DataFrame, summary: Dict, top_consumers: Dict) -> List[str]:
        """Generate insights for daily report"""
        insights = []
        
        # Cost insight
        daily_cost = summary['total_cost']
        insights.append(f"💰 Yesterday's energy cost was ${daily_cost:.2f}")
        
        # Top consumer insight
        if top_consumers:
            top_device = list(top_consumers.keys())[0]
            top_cost = list(top_consumers.values())[0]
            insights.append(f"🔌 {top_device} was your biggest energy consumer (${top_cost:.2f})")
        
        # Usage pattern insight - with proper datetime handling
        try:
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                peak_hour = df.groupby(df['timestamp'].dt.hour)['power_watts'].mean().idxmax()
                insights.append(f"📊 Peak energy usage occurred around {peak_hour}:00")
            else:
                insights.append(f"📊 Energy usage data collected successfully")
        except Exception:
            insights.append(f"📊 Energy usage patterns are being analyzed")
        
        return insights
    
    def _generate_daily_recommendations(self, df: pd.DataFrame, summary: Dict) -> List[str]:
        """Generate daily recommendations"""
        recommendations = []
        
        if summary['total_cost'] > 3.0:
            recommendations.append("Consider reducing usage during peak hours to lower costs")
        
        recommendations.append("Review which devices were left on unnecessarily")
        
        return recommendations

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