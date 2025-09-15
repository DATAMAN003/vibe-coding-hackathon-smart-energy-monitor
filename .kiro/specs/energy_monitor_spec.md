# Smart Energy Monitor - Kiro Specification

## Project Overview
Build a comprehensive AI-powered home energy monitoring system that provides real-time insights, cost tracking, and personalized recommendations while maintaining complete local privacy.

## Core Requirements

### 1. Real-Time Energy Monitoring
- **Hardware Integration**: Support for MCP3008 ADC + Current Transformers
- **Simulation Mode**: Realistic appliance behavior patterns for development
- **Data Collection**: Async, non-blocking data gathering every 60 seconds
- **Database Storage**: Efficient SQLite storage with proper indexing

### 2. AI-Powered Analysis
- **Pattern Recognition**: Identify usage patterns, peak hours, and inefficiencies
- **Smart Insights**: Generate human-readable explanations of energy consumption
- **Personalized Recommendations**: Actionable advice to reduce energy usage
- **Efficiency Scoring**: Rate device efficiency and suggest improvements
- **Future-Ready**: Built for gpt-oss integration with intelligent mock AI fallback

### 3. Web Dashboard
- **Real-Time Interface**: Live monitoring with auto-refresh
- **Device Management**: Individual device tracking and analysis
- **Historical Charts**: Power usage trends over time
- **Cost Tracking**: Real-time cost calculations and monthly estimates
- **Responsive Design**: Works on desktop and mobile

### 4. Privacy-First Design
- **100% Local**: No data sent to cloud services
- **Offline AI**: Uses local models for analysis
- **Secure**: All data stays on device
- **No Internet Required**: Works completely offline

## Technical Architecture

### Data Flow
```
CT Sensors → Raspberry Pi + MCP3008 → SQLite DB → AI Analyzer → Web Dashboard
```

### Key Components
1. **hardware_interface.py**: Hardware abstraction layer
2. **data_collector.py**: Async data collection and storage
3. **ai_analyzer.py**: AI-powered analysis and insights
4. **web_interface.py**: Flask web application
5. **energy_calculator.py**: Energy and cost calculations
6. **database.py**: Database schema and operations

## Device Configuration
Support monitoring of common home appliances:
- Living Room TV
- Kitchen appliances (microwave, fridge)
- HVAC systems (AC units)
- Home office equipment
- Laundry appliances (washer, dryer)

## AI Analysis Features
- Device-specific insights based on power patterns
- Usage pattern analysis and trend detection
- Cost optimization suggestions
- Efficiency scoring and recommendations
- Peak usage identification

## Performance Requirements
- Handle 7+ devices simultaneously
- Process data every 60 seconds
- Support 30+ days of historical data
- Sub-second web interface response times
- 99%+ uptime for data collection

## Security & Privacy
- No external API calls
- Local data storage only
- No user data collection
- Secure hardware interfaces
- Offline operation capability
