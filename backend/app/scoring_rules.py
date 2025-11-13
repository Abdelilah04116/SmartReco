"""Rule engine for scoring customers based on business rules."""
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from .config import settings
from .schemas import RuleConfig
from .utils import safe_eval_condition, normalize_column_name


class RuleEngine:
    """Engine for evaluating business rules against customer data."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the rule engine with configuration.
        
        Args:
            config_path: Path to rules configuration YAML file
        """
        if config_path:
            self.config_path = config_path
        else:
            # Try multiple possible paths
            possible_paths = [
                settings.RULES_CONFIG_PATH,
                Path("rules_config.yaml"),
                Path("/app/rules_config.yaml"),
                Path("../rules_config.yaml"),
            ]
            self.config_path = None
            for path in possible_paths:
                if path.exists():
                    self.config_path = path
                    break
            if not self.config_path:
                self.config_path = settings.RULES_CONFIG_PATH
        
        self.rules: List[RuleConfig] = []
        self.load_rules()
    
    def load_rules(self) -> None:
        """Load rules from YAML configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Rules config not found at {self.config_path}, using defaults")
                self.rules = self._get_default_rules()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            rules_list = config.get('rules', [])
            self.rules = [RuleConfig(**rule) for rule in rules_list]
            
            logger.info(f"Loaded {len(self.rules)} rules from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            self.rules = self._get_default_rules()
    
    def _get_default_rules(self) -> List[RuleConfig]:
        """Get default rules if config file is not available."""
        return [
            RuleConfig(
                id="rule_1",
                label="Prime Age Range",
                condition="age >= 25 and age <= 45",
                points=20.0,
                description="Customers in prime age range (25-45) are more likely to convert",
                enabled=True
            ),
            RuleConfig(
                id="rule_2",
                label="High Balance",
                condition="balance > 5000",
                points=25.0,
                description="Customers with high balance have better conversion potential",
                enabled=True
            ),
            RuleConfig(
                id="rule_3",
                label="Previous Success",
                condition="poutcome == 'success'",
                points=30.0,
                description="Customers with previous successful campaign outcome",
                enabled=True
            ),
        ]
    
    def get_rules(self) -> List[RuleConfig]:
        """Get all rules."""
        return self.rules
    
    def get_rule(self, rule_id: str) -> Optional[RuleConfig]:
        """Get a specific rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def update_rule(self, rule_id: str, enabled: Optional[bool] = None,
                   threshold: Optional[float] = None, points: Optional[float] = None) -> bool:
        """
        Update a rule's configuration.
        
        Args:
            rule_id: ID of the rule to update
            enabled: New enabled status
            threshold: New threshold value
            points: New points value
            
        Returns:
            True if rule was found and updated, False otherwise
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        
        if enabled is not None:
            rule.enabled = enabled
        if threshold is not None:
            rule.threshold = threshold
        if points is not None:
            rule.points = points
        
        logger.info(f"Updated rule {rule_id}: enabled={rule.enabled}, points={rule.points}")
        return True
    
    def evaluate_rules(self, customer_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled rules against customer data.
        
        Args:
            customer_data: Dictionary with customer attributes
            
        Returns:
            List of fired rules with their details
        """
        fired_rules = []
        
        # Normalize customer data keys
        normalized_data = {normalize_column_name(k): v for k, v in customer_data.items()}
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                # Evaluate condition
                condition_met = safe_eval_condition(rule.condition, normalized_data)
                
                if condition_met:
                    # Check threshold if specified
                    if rule.threshold is not None:
                        relevant_value = normalized_data.get('balance', 0)
                        if isinstance(relevant_value, (int, float)):
                            if relevant_value < rule.threshold:
                                continue
                    
                    fired_rules.append({
                        'rule_id': rule.id,
                        'rule_label': rule.label,
                        'points': rule.points,
                        'reason': f"{rule.label}: {rule.description}"
                    })
                    
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
                continue
        
        return fired_rules
    
    def save_rules(self) -> bool:
        """Save current rules configuration to YAML file."""
        try:
            config = {
                'rules': [rule.model_dump() for rule in self.rules]
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved {len(self.rules)} rules to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            return False


# Global rule engine instance
rule_engine = RuleEngine()

