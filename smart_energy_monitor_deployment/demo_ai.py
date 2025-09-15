#!/usr/bin/env python3
"""
Smart Energy Monitor - AI Features Demo
Demonstrates the AI analysis capabilities with sample data
"""

import sys
import json
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_collector import EnergyDataCollector
from ai_analyzer import EnergyAIAnalyzer
from database import EnergyDatabase

def print_banner():
    """Print demo banner"""
    print("""
🤖 Smart Energy Monitor - AI Demo
==================================
Demonstrating AI-powered energy analysis
""")

async def generate_sample_data():
    """Generate realistic sample data for demo"""
    print("📊 Generating sample energy data...")
    
    collector = EnergyDataCollector(use_simulation=True)
    
    # Collect data multiple times to build history
    all_readings = []
    for i in range(10):  # Simulate 10 collection cycles
        readings = await collector.collect_all_devices()
        if readings:
            collector.save_readings(readings)
            all_readings.extend(readings)
        
        # Small delay to create time variation
        await asyncio.sleep(0.1)
    
    print(f"✅ Generated {len(all_readings)} sample readings")
    return all_readings

def demo_device_analysis():
    """Demonstrate device-specific AI analysis"""
    print("\n🔍 Device Analysis Demo")
    print("-" * 30)
    
    analyzer = EnergyAIAnalyzer(use_mock_ai=True)
    
    # Analyze different devices
    devices = [
        "living_room_tv",
        "kitchen_fridge", 
        "office_computer",
        "bedroom_ac"
    ]
    
    for device_id in devices:
        print(f"\n📱 Analyzing {device_id}...")
        
        analysis = analyzer.analyze_device_patterns(device_id, days=1)
        
        if 'error' in analysis:
            print(f"   ⚠️  {analysis['error']}")
            continue
        
        # Display key insights
        stats = analysis.get('statistics', {})
        insights = analysis.get('insights', [])
        recommendations = analysis.get('recommendations', [])
        
        print(f"   ⚡ Average Power: {stats.get('avg_power_watts', 0):.1f}W")
        print(f"   📊 Efficiency Score: {stats.get('efficiency_score', 0)}/100")
        print(f"   💰 Daily Cost: ${(stats.get('total_cost', 0)):.3f}")
        
        print("   🧠 AI Insights:")
        for insight in insights[:2]:  # Show top 2 insights
            print(f"      • {insight}")
        
        print("   💡 Recommendations:")
        for rec in recommendations[:2]:  # Show top 2 recommendations
            print(f"      • {rec}")

def demo_home_analysis():
    """Demonstrate home-level AI analysis"""
    print("\n\n🏠 Home Energy Analysis Demo")
    print("-" * 35)
    
    analyzer = EnergyAIAnalyzer(use_mock_ai=True)
    
    analysis = analyzer.analyze_home_energy(days=1)
    
    if 'error' in analysis:
        print(f"⚠️  {analysis['error']}")
        return
    
    print(f"🏡 Total Devices Monitored: {analysis.get('total_devices', 0)}")
    print(f"⚡ Total Energy: {analysis.get('total_energy_kwh', 0):.2f} kWh")
    print(f"💰 Total Cost: ${analysis.get('total_cost', 0):.2f}")
    
    peak_hours = analysis.get('peak_hours', [])
    if peak_hours:
        peak_str = ", ".join([f"{h}:00" for h in peak_hours])
        print(f"📈 Peak Usage Hours: {peak_str}")
    
    print("\n🧠 Home AI Insights:")
    insights = analysis.get('insights', [])
    for insight in insights:
        print(f"   • {insight}")
    
    print("\n💡 Home Recommendations:")
    recommendations = analysis.get('recommendations', [])
    for rec in recommendations:
        print(f"   • {rec}")
    
    # Show top energy consumers
    device_summary = analysis.get('device_summary', {})
    if device_summary:
        print("\n🔌 Top Energy Consumers:")
        # Sort devices by total cost
        sorted_devices = sorted(
            device_summary.items(), 
            key=lambda x: x[1].get('total_cost', 0), 
            reverse=True
        )
        
        for device, stats in sorted_devices[:3]:  # Top 3
            cost = stats.get('total_cost', 0)
            avg_power = stats.get('avg_power_watts', 0)
            print(f"   {device}: ${cost:.3f} ({avg_power:.1f}W avg)")

def demo_daily_report():
    """Demonstrate daily AI report generation"""
    print("\n\n📅 Daily AI Report Demo")
    print("-" * 25)
    
    analyzer = EnergyAIAnalyzer(use_mock_ai=True)
    
    report = analyzer.generate_daily_report()
    
    if 'error' in report:
        print(f"⚠️  {report['error']}")
        return
    
    summary = report.get('summary', {})
    print(f"📊 Daily Summary:")
    print(f"   Date: {summary.get('date', 'Today')}")
    print(f"   Energy: {summary.get('total_energy_kwh', 0):.2f} kWh")
    print(f"   Cost: ${summary.get('total_cost', 0):.2f}")
    print(f"   Peak Power: {summary.get('peak_power_watts', 0):.0f}W")
    
    top_consumers = report.get('top_energy_consumers', {})
    if top_consumers:
        print(f"\n🔌 Top Consumers:")
        for device, cost in list(top_consumers.items())[:3]:
            print(f"   {device}: ${cost:.3f}")
    
    insights = report.get('insights', [])
    if insights:
        print(f"\n🧠 Daily Insights:")
        for insight in insights:
            print(f"   • {insight}")

def demo_ai_capabilities():
    """Show what the AI system can do"""
    print("\n\n🤖 AI Capabilities Overview")
    print("-" * 30)
    
    capabilities = [
        "🔍 Pattern Recognition - Identifies usage patterns and anomalies",
        "📊 Efficiency Analysis - Scores device efficiency (0-100)",
        "💡 Smart Recommendations - Actionable energy-saving tips",
        "🏠 Home-Level Insights - Whole-house energy analysis", 
        "📅 Daily Reports - Automated daily energy summaries",
        "⚡ Real-Time Analysis - Instant insights on current usage",
        "🎯 Device-Specific Tips - Tailored advice per appliance type",
        "💰 Cost Optimization - Identifies highest-cost devices"
    ]
    
    print("Current AI Features (Mock AI):")
    for capability in capabilities:
        print(f"   ✅ {capability}")
    
    print(f"\n🚀 Future with gpt-oss:")
    future_features = [
        "🧠 Advanced Natural Language Insights",
        "🔮 Predictive Energy Forecasting", 
        "🎨 Personalized Energy Coaching",
        "📈 Trend Analysis with Explanations"
    ]
    
    for feature in future_features:
        print(f"   🔜 {feature}")

async def main():
    """Run the complete AI demo"""
    print_banner()
    
    # Generate sample data
    await generate_sample_data()
    
    # Run AI demos
    demo_device_analysis()
    demo_home_analysis() 
    demo_daily_report()
    demo_ai_capabilities()
    
    print(f"\n🎉 AI Demo Complete!")
    print(f"\nTo see the AI in action with real-time data:")
    print(f"   python app.py")
    print(f"   # Then visit http://localhost:5000")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        sys.exit(1)