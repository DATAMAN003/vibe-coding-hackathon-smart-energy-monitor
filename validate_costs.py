#!/usr/bin/env python3
"""
Validate the dashboard cost calculations
"""

def validate_dashboard():
    # From your NEW dashboard screenshot
    total_power = 140.25  # Watts
    daily_cost = 0.40     # USD
    monthly_est = 12.12   # USD
    rate = 0.12           # $/kWh
    
    print("🔍 DASHBOARD COST VALIDATION")
    print("=" * 40)
    print(f"📊 Dashboard Values:")
    print(f"   Total Power: {total_power} W")
    print(f"   Daily Cost: ${daily_cost}")
    print(f"   Monthly Est: ${monthly_est}")
    print(f"   Rate: ${rate}/kWh")
    print()
    
    # Calculate expected values
    daily_kwh = (total_power * 24) / 1000  # Convert watts to daily kWh
    daily_cost_expected = daily_kwh * rate
    monthly_cost_expected = daily_cost_expected * 30
    
    print(f"🧮 Calculated Values:")
    print(f"   Daily kWh: {daily_kwh:.3f}")
    print(f"   Daily cost expected: ${daily_cost_expected:.3f}")
    print(f"   Monthly cost expected: ${monthly_cost_expected:.2f}")
    print()
    
    # Validation
    daily_diff = abs(daily_cost_expected - daily_cost)
    monthly_diff = abs(monthly_cost_expected - monthly_est)
    
    print(f"✅ Validation Results:")
    print(f"   Daily difference: ${daily_diff:.3f}")
    print(f"   Monthly difference: ${monthly_diff:.2f}")
    print()
    
    if daily_diff < 0.05:
        print("✅ Daily cost is CORRECT!")
    else:
        print(f"❌ Daily cost ERROR: Expected ${daily_cost_expected:.3f}, got ${daily_cost}")
        
    if monthly_diff < 1.0:
        print("✅ Monthly estimate is CORRECT!")
    else:
        print(f"❌ Monthly estimate ERROR: Expected ${monthly_cost_expected:.2f}, got ${monthly_est}")
    
    print()
    print("📈 Analysis:")
    print(f"   This represents {total_power}W continuous usage")
    print(f"   That's {daily_kwh:.1f} kWh per day")
    print(f"   At ${rate}/kWh = ${daily_cost_expected:.2f}/day")
    print(f"   Monthly: ${monthly_cost_expected:.2f}")
    
    # Compare to previous low usage
    print()
    print("📊 Comparison to Previous:")
    print("   Previous: 0.061 kWh/day, $0.01/day, $0.22/month")
    print(f"   Current:  {daily_kwh:.3f} kWh/day, ${daily_cost}/day, ${monthly_est}/month")
    print(f"   Increase: {daily_kwh/0.061:.0f}x higher usage!")

if __name__ == "__main__":
    validate_dashboard()