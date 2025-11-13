"""Recommendation engine for prioritizing customers."""
from typing import List, Dict, Any, Optional
from loguru import logger
from .schemas import CustomerScore, RuleFired
from .scoring_rules import rule_engine
from .config import settings
from .utils import calculate_priority_label, generate_customer_id


class Recommender:
    """Engine for scoring and recommending customers."""
    
    def __init__(self):
        """Initialize the recommender."""
        self.rule_engine = rule_engine
    
    def score_customer(self, customer_data: Dict[str, Any], customer_id: Optional[str] = None) -> CustomerScore:
        """
        Score a single customer based on business rules.
        
        Args:
            customer_data: Dictionary with customer attributes
            customer_id: Optional customer ID, will be generated if not provided
            
        Returns:
            CustomerScore object with scoring details
        """
        # Generate customer ID if not provided
        if customer_id is None:
            customer_id = generate_customer_id(customer_data, 0)
        
        # Evaluate rules
        fired_rules_data = self.rule_engine.evaluate_rules(customer_data)
        
        # Calculate total score
        total_score = sum(rule['points'] for rule in fired_rules_data)
        
        # Determine priority label
        priority_label = calculate_priority_label(total_score, settings.PRIORITY_THRESHOLDS)
        
        # Build rules_fired list
        rules_fired = [
            RuleFired(
                rule_id=rule['rule_id'],
                rule_label=rule['rule_label'],
                points=rule['points'],
                reason=rule['reason']
            )
            for rule in fired_rules_data
        ]
        
        # Build explain dictionary
        explain = {
            'total_score': total_score,
            'rules_count': len(rules_fired),
            'score_breakdown': {rule.rule_id: rule.points for rule in rules_fired}
        }
        
        return CustomerScore(
            customer_id=customer_id,
            priority_score=total_score,
            priority_label=priority_label,
            rules_fired=rules_fired,
            explain=explain,
            raw_data=customer_data
        )
    
    def score_customers(self, customers_data: List[Dict[str, Any]]) -> List[CustomerScore]:
        """
        Score multiple customers.
        
        Args:
            customers_data: List of customer dictionaries
            
        Returns:
            List of CustomerScore objects
        """
        results = []
        for idx, customer_data in enumerate(customers_data):
            customer_id = generate_customer_id(customer_data, idx)
            score = self.score_customer(customer_data, customer_id)
            results.append(score)
        
        return results
    
    def get_recommendations(self, scored_customers: List[CustomerScore],
                          top_n: int = 50,
                          filter_criteria: Optional[Dict[str, Any]] = None) -> List[CustomerScore]:
        """
        Get top N recommendations from scored customers.
        
        Args:
            scored_customers: List of scored customers
            top_n: Number of top customers to return
            filter_criteria: Optional filter criteria (e.g., {"priority_label": "high"})
            
        Returns:
            Sorted list of top N customers
        """
        # Apply filters if provided
        filtered = scored_customers
        if filter_criteria:
            for key, value in filter_criteria.items():
                if key == 'priority_label':
                    filtered = [c for c in filtered if c.priority_label == value]
                elif key == 'min_score':
                    filtered = [c for c in filtered if c.priority_score >= value]
                elif key == 'max_score':
                    filtered = [c for c in filtered if c.priority_score <= value]
        
        # Sort by priority score (descending)
        sorted_customers = sorted(filtered, key=lambda x: x.priority_score, reverse=True)
        
        # Return top N
        return sorted_customers[:top_n]
    
    def generate_suggested_action(self, customer_score: CustomerScore) -> str:
        """
        Generate a suggested action text based on fired rules.
        
        Args:
            customer_score: CustomerScore object
            
        Returns:
            Human-readable action suggestion
        """
        if not customer_score.rules_fired:
            return "No specific action recommended. Customer does not match priority criteria."
        
        # Build action based on priority and rules
        actions = []
        
        if customer_score.priority_label == "high":
            actions.append("HIGH PRIORITY: Immediate contact recommended")
        elif customer_score.priority_label == "medium":
            actions.append("MEDIUM PRIORITY: Follow-up within 1 week")
        else:
            actions.append("LOW PRIORITY: Standard campaign inclusion")
        
        # Add rule-specific suggestions
        rule_labels = [rule.rule_label for rule in customer_score.rules_fired]
        if "Previous Success" in rule_labels:
            actions.append("Previous campaign success indicates high conversion potential")
        if "High Balance" in rule_labels:
            actions.append("High balance customer - offer premium products")
        if "Prime Age Range" in rule_labels:
            actions.append("Prime demographic - focus on lifestyle benefits")
        
        return ". ".join(actions) + "."
    
    def simulate_campaign(self, scored_customers: List[CustomerScore],
                         top_n: int = 50) -> Dict[str, Any]:
        """
        Simulate a campaign and estimate KPIs.
        
        Args:
            scored_customers: List of scored customers
            top_n: Number of customers to include in campaign
            
        Returns:
            Dictionary with estimated KPIs
        """
        # Get top N recommendations
        recommendations = self.get_recommendations(scored_customers, top_n=top_n)
        
        if not recommendations:
            return {
                'estimated_conversion_rate': 0.0,
                'estimated_revenue': 0.0,
                'total_customers': 0,
                'high_priority_count': 0,
                'medium_priority_count': 0,
                'low_priority_count': 0,
                'kpis': {}
            }
        
        # Count by priority
        high_count = sum(1 for c in recommendations if c.priority_label == "high")
        medium_count = sum(1 for c in recommendations if c.priority_label == "medium")
        low_count = sum(1 for c in recommendations if c.priority_label == "low")
        
        # Estimate conversion rates based on priority (rule-based heuristic)
        # High priority: 15-25%, Medium: 8-15%, Low: 3-8%
        high_conversion = 0.20  # 20%
        medium_conversion = 0.12  # 12%
        low_conversion = 0.05  # 5%
        
        # Calculate weighted average conversion rate
        total_conversions = (
            high_count * high_conversion +
            medium_count * medium_conversion +
            low_count * low_conversion
        )
        estimated_conversion_rate = total_conversions / len(recommendations) if recommendations else 0.0
        
        # Estimate revenue (assume average revenue per conversion)
        avg_revenue_per_conversion = 1000.0  # Example value
        estimated_revenue = total_conversions * avg_revenue_per_conversion
        
        # Calculate average score
        avg_score = sum(c.priority_score for c in recommendations) / len(recommendations) if recommendations else 0.0
        
        return {
            'estimated_conversion_rate': round(estimated_conversion_rate, 4),
            'estimated_revenue': round(estimated_revenue, 2),
            'total_customers': len(recommendations),
            'high_priority_count': high_count,
            'medium_priority_count': medium_count,
            'low_priority_count': low_count,
            'kpis': {
                'average_score': round(avg_score, 2),
                'high_priority_rate': round(high_count / len(recommendations), 4) if recommendations else 0.0,
                'estimated_conversions': int(total_conversions),
                'cost_per_customer': 5.0,  # Example
                'roi': round((estimated_revenue - (len(recommendations) * 5.0)) / (len(recommendations) * 5.0), 2) if recommendations else 0.0
            }
        }


# Global recommender instance
recommender = Recommender()


