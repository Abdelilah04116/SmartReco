"""Utility functions for data processing and rule evaluation."""
import re
import ast
import operator
from typing import Any, Dict, List, Union
import pandas as pd
from loguru import logger


# Safe operators for rule evaluation
SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
}


def safe_eval_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate a rule condition string against a context dictionary.
    
    Supports: ==, !=, >, >=, <, <=, in, not in, and, or
    Example: "age >= 25 and age <= 45"
    
    Args:
        condition: String expression to evaluate
        context: Dictionary with variable values
        
    Returns:
        Boolean result of the evaluation
    """
    try:
        # Parse the condition into an AST
        tree = ast.parse(condition, mode='eval')
        
        def eval_node(node):
            """Recursively evaluate AST nodes."""
            if isinstance(node, ast.Expression):
                return eval_node(node.body)
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                # Get value from context
                value = context.get(node.id)
                if value is None:
                    logger.warning(f"Variable '{node.id}' not found in context")
                    return None
                return value
            elif isinstance(node, ast.Num):  # Python < 3.8
                return node.n
            elif isinstance(node, ast.Str):  # Python < 3.8
                return node.s
            elif isinstance(node, ast.BoolOp):
                op = SAFE_OPERATORS[type(node.op)]
                values = [eval_node(child) for child in node.values]
                return all(values) if isinstance(node.op, ast.And) else any(values)
            elif isinstance(node, ast.Compare):
                left = eval_node(node.left)
                if left is None:
                    return False
                
                result = True
                for i, (op, comparator) in enumerate(zip(node.ops, node.comparators)):
                    right = eval_node(comparator)
                    if right is None:
                        return False
                    
                    op_func = SAFE_OPERATORS.get(type(op))
                    if op_func is None:
                        logger.error(f"Unsupported operator: {type(op)}")
                        return False
                    
                    # Handle 'in' and 'not in' with list/tuple right side
                    if isinstance(op, (ast.In, ast.NotIn)):
                        if not isinstance(right, (list, tuple, str)):
                            right = [right]
                    elif isinstance(op, ast.Eq) and isinstance(right, str):
                        # String comparison (case-insensitive for categorical)
                        if isinstance(left, str):
                            left = left.lower()
                            right = right.lower()
                    
                    if not op_func(left, right):
                        result = False
                        break
                
                return result
            elif isinstance(node, ast.List):
                return [eval_node(el) for el in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(eval_node(el) for el in node.elts)
            else:
                logger.error(f"Unsupported AST node type: {type(node)}")
                return False
        
        result = eval_node(tree)
        return bool(result) if result is not None else False
        
    except Exception as e:
        logger.error(f"Error evaluating condition '{condition}': {e}")
        return False


def normalize_column_name(col: str) -> str:
    """Normalize column names for consistency."""
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def parse_csv_data(csv_content: str) -> pd.DataFrame:
    """
    Parse CSV content into a pandas DataFrame.
    
    Args:
        csv_content: CSV file content as string
        
    Returns:
        DataFrame with normalized column names
    """
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        # Normalize column names
        df.columns = [normalize_column_name(col) for col in df.columns]
        return df
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise ValueError(f"Invalid CSV format: {e}")


def generate_customer_id(row: Dict[str, Any], index: int) -> str:
    """Generate a unique customer ID from row data or index."""
    # Try to use existing ID fields
    for id_field in ['id', 'customer_id', 'client_id', 'index']:
        if id_field in row and row[id_field] is not None:
            return str(row[id_field])
    # Fallback to index
    return f"customer_{index}"


def format_reason(rule_label: str, condition: str, row: Dict[str, Any]) -> str:
    """Generate a human-readable reason for why a rule fired."""
    # Extract key variables from condition
    reason = f"{rule_label}: condition '{condition}' was met"
    
    # Try to extract meaningful values
    for key in ['age', 'balance', 'job', 'marital', 'education', 'previous', 'poutcome']:
        if key in row:
            reason += f" ({key}={row[key]})"
            break
    
    return reason


def calculate_priority_label(score: float, thresholds: Dict[str, float]) -> str:
    """Calculate priority label based on score and thresholds."""
    if score >= thresholds.get("high", 50):
        return "high"
    elif score >= thresholds.get("medium", 25):
        return "medium"
    else:
        return "low"


