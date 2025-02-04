"""AI assistant for thruster efficiency predictions."""
import openai
import os
from typing import Dict, List, Optional
from models import GridSpecifications

class ThrusterAIAssistant:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.system_prompt = """
You are an AI assistant specializing in Space Engineers thruster configurations.
Analyze grid specifications and provide optimization suggestions.
Focus on:
- Thruster type distribution
- Mass-to-thrust ratio
- Power efficiency
- Atmospheric vs Space performance
Provide specific, actionable recommendations.
"""

    def analyze_grid(self, specs: GridSpecifications) -> Dict[str, str]:
        """Analyze grid specifications and provide recommendations."""
        thrusts = specs.calculate_thrust_by_type()
        total_thrust = specs.calculate_total_thrust()
        lift_capacity = specs.calculate_lift_capacity()
        twr = total_thrust / (specs.mass * specs.gravity) if specs.mass > 0 else 0

        prompt = f"""
Current Grid Configuration:
- Mass: {specs.mass:,.2f} kg
- Total Thrust: {total_thrust:,.2f} N
- Thrust-to-Weight Ratio: {twr:.2f}
- Atmospheric Thrust: {thrusts['atmospheric']:,.2f} N
- Ion Thrust: {thrusts['ion']:,.2f} N
- Hydrogen Thrust: {thrusts['hydrogen']:,.2f} N
- Lift Capacity: {lift_capacity:,.2f} kg

Please analyze this configuration and provide:
1. Efficiency Assessment: Evaluate the current setup's efficiency
2. Optimization Suggestions: Recommend improvements
3. Use Case Analysis: Suggest ideal scenarios for this configuration
"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            analysis = response.choices[0].message.content

            # Split analysis into sections
            sections = analysis.split("\n\n")
            return {
                "efficiency": sections[0] if len(sections) > 0 else "Analysis unavailable",
                "optimization": sections[1] if len(sections) > 1 else "No optimization suggestions",
                "use_cases": sections[2] if len(sections) > 2 else "No use case analysis"
            }

        except Exception as e:
            return {
                "efficiency": f"Error analyzing efficiency: {str(e)}",
                "optimization": "Analysis unavailable",
                "use_cases": "Analysis unavailable"
            }

    def suggest_improvements(self, current_specs: GridSpecifications) -> Dict[str, any]:
        """Suggest specific improvements for the current configuration."""
        thrusts = current_specs.calculate_thrust_by_type()
        total_thrust = current_specs.calculate_total_thrust()

        # Check for zero total thrust to avoid division by zero
        if total_thrust == 0:
            return {
                "thrust_balance": "No thrusters configured",
                "efficiency_score": 0,
                "suggested_changes": ["Add thrusters to begin analysis"]
            }

        # Calculate distribution percentages
        thrust_distribution = {
            k: (v / total_thrust) * 100 if total_thrust > 0 else 0 
            for k, v in thrusts.items()
        }

        suggestions = {
            "thrust_balance": self._analyze_thrust_balance(thrust_distribution),
            "efficiency_score": self._calculate_efficiency_score(current_specs),
            "suggested_changes": self._generate_suggested_changes(current_specs)
        }

        return suggestions

    def _analyze_thrust_balance(self, distribution: Dict[str, float]) -> str:
        """Analyze the balance of different thruster types."""
        if all(v == 0 for v in distribution.values()):
            return "No thrusters configured"

        if distribution["atmospheric"] > 60:
            return "Heavy atmospheric focus - consider diversifying for space operations"
        elif distribution["ion"] > 60:
            return "Heavy ion focus - may struggle in atmosphere"
        elif distribution["hydrogen"] > 60:
            return "Heavy hydrogen focus - check fuel efficiency"
        return "Balanced thrust distribution"

    def _calculate_efficiency_score(self, specs: GridSpecifications) -> float:
        """Calculate an efficiency score (0-100) based on various factors."""
        total_thrust = specs.calculate_total_thrust()

        # Handle zero cases
        if total_thrust == 0 or specs.mass == 0:
            return 0

        twr = total_thrust / (specs.mass * specs.gravity)

        # Base score on TWR
        base_score = min(100, max(0, twr * 20))

        # Adjust for thrust distribution
        thrusts = specs.calculate_thrust_by_type()
        ideal_thrust = total_thrust / 3  # Ideal balanced distribution

        distribution_penalty = sum(
            abs(t - ideal_thrust) for t in thrusts.values()
        ) / total_thrust * 20 if total_thrust > 0 else 100

        return max(0, min(100, base_score - distribution_penalty))

    def _generate_suggested_changes(self, specs: GridSpecifications) -> List[str]:
        """Generate specific suggested changes for improvement."""
        suggestions = []
        total_thrust = specs.calculate_total_thrust()

        if total_thrust == 0:
            return ["Add thrusters to begin analysis"]

        twr = total_thrust / (specs.mass * specs.gravity) if specs.mass > 0 else 0

        if twr == 0:
            suggestions.append("Add mass and thrusters to calculate thrust-to-weight ratio")
        elif twr < 1.5:
            suggestions.append("Add more thrusters to improve lift capacity")
        elif twr > 4:
            suggestions.append("Consider reducing thrust for better efficiency")

        thrusts = specs.calculate_thrust_by_type()

        # Check atmospheric capabilities
        if specs.mass > 0 and thrusts["atmospheric"] < specs.mass * specs.gravity:
            suggestions.append("Increase atmospheric thrusters for better planet performance")

        # Check space capabilities
        if specs.mass > 0 and thrusts["ion"] + thrusts["hydrogen"] < specs.mass * specs.gravity:
            suggestions.append("Increase ion/hydrogen thrusters for space operations")

        return suggestions