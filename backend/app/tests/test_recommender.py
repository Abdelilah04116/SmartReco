"""Unit tests for recommender functionality."""
import pytest
from app.recommender import Recommender
from app.scoring_rules import RuleEngine
from app.config import settings


@pytest.fixture
def recommender_instance():
    """Create a recommender instance for testing."""
    return Recommender()


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    return {
        "age": 35,
        "job": "management",
        "marital": "married",
        "education": "tertiary",
        "balance": 6000,
        "previous": 1,
        "poutcome": "success"
    }


def test_score_customer_high_priority(recommender_instance, sample_customer):
    """Test scoring a high-priority customer."""
    score = recommender_instance.score_customer(sample_customer)
    
    assert score.priority_score > 0
    assert score.priority_label in ["high", "medium", "low"]
    assert len(score.rules_fired) > 0
    assert score.customer_id is not None


def test_score_customer_low_priority(recommender_instance):
    """Test scoring a low-priority customer."""
    customer = {
        "age": 18,
        "job": "student",
        "balance": 100,
        "previous": 0,
        "poutcome": "unknown"
    }
    
    score = recommender_instance.score_customer(customer)
    
    assert score.priority_score >= 0
    assert score.priority_label in ["high", "medium", "low"]


def test_score_multiple_customers(recommender_instance):
    """Test scoring multiple customers."""
    customers = [
        {"age": 30, "balance": 5000, "poutcome": "success"},
        {"age": 20, "balance": 100, "poutcome": "failure"},
        {"age": 40, "balance": 10000, "poutcome": "unknown"}
    ]
    
    scores = recommender_instance.score_customers(customers)
    
    assert len(scores) == 3
    assert all(s.priority_score >= 0 for s in scores)


def test_get_recommendations(recommender_instance):
    """Test getting top N recommendations."""
    customers = [
        {"age": 30, "balance": 5000, "poutcome": "success"},
        {"age": 20, "balance": 100, "poutcome": "failure"},
        {"age": 40, "balance": 10000, "poutcome": "unknown"},
        {"age": 35, "balance": 8000, "poutcome": "success"}
    ]
    
    scored = recommender_instance.score_customers(customers)
    recommendations = recommender_instance.get_recommendations(scored, top_n=2)
    
    assert len(recommendations) == 2
    # Should be sorted by score descending
    assert recommendations[0].priority_score >= recommendations[1].priority_score


def test_get_recommendations_with_filter(recommender_instance):
    """Test getting recommendations with filter."""
    customers = [
        {"age": 30, "balance": 5000, "poutcome": "success"},
        {"age": 20, "balance": 100, "poutcome": "failure"},
        {"age": 40, "balance": 10000, "poutcome": "unknown"}
    ]
    
    scored = recommender_instance.score_customers(customers)
    recommendations = recommender_instance.get_recommendations(
        scored,
        top_n=10,
        filter_criteria={"priority_label": "high"}
    )
    
    assert all(r.priority_label == "high" for r in recommendations)


def test_generate_suggested_action(recommender_instance, sample_customer):
    """Test generating suggested action."""
    score = recommender_instance.score_customer(sample_customer)
    action = recommender_instance.generate_suggested_action(score)
    
    assert isinstance(action, str)
    assert len(action) > 0


def test_simulate_campaign(recommender_instance):
    """Test campaign simulation."""
    customers = [
        {"age": 30, "balance": 5000, "poutcome": "success"},
        {"age": 20, "balance": 100, "poutcome": "failure"},
        {"age": 40, "balance": 10000, "poutcome": "unknown"}
    ]
    
    scored = recommender_instance.score_customers(customers)
    simulation = recommender_instance.simulate_campaign(scored, top_n=2)
    
    assert "estimated_conversion_rate" in simulation
    assert "estimated_revenue" in simulation
    assert "total_customers" in simulation
    assert simulation["total_customers"] == 2


def test_rules_fired_structure(recommender_instance, sample_customer):
    """Test that rules_fired has correct structure."""
    score = recommender_instance.score_customer(sample_customer)
    
    for rule in score.rules_fired:
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'rule_label')
        assert hasattr(rule, 'points')
        assert hasattr(rule, 'reason')
        assert rule.points > 0


