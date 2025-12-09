"""AI Agent using Google Gemini for intelligent data analysis and recommendations."""
from __future__ import annotations

import json
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. AI agent features will be disabled.")

from .config import settings
from .schema_detection import schema_detector


class DataAnalysisAgent:
    """AI agent that analyzes CSV data and provides intelligent recommendations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI agent.
        
        Args:
            api_key: Google Gemini API key (or from env GEMINI_API_KEY)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("AI Agent initialized with Gemini")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            logger.warning("AI Agent not available - Gemini API key not configured")
    
    def analyze_dataset(self, 
                       df: pd.DataFrame,
                       sample_size: int = 1000) -> Dict[str, Any]:
        """
        Analyze dataset and provide AI-powered recommendations.
        
        Args:
            df: Input DataFrame
            sample_size: Sample size for analysis (to reduce token usage)
            
        Returns:
            Dictionary with analysis and recommendations
        """
        if not self.model:
            return self._fallback_analysis(df)
        
        try:
            # Sample data for analysis
            sample_df = df.sample(n=min(sample_size, len(df)), random_state=42) if len(df) > sample_size else df
            
            # Get schema information
            schema = schema_detector.detect_schema(sample_df, sample_size=min(500, len(sample_df)))
            
            # Prepare data summary for AI
            data_summary = self._prepare_data_summary(sample_df, schema)
            
            # Get AI recommendations
            recommendations = self._get_ai_recommendations(data_summary, schema)
            
            # Apply AI-suggested transformations
            transformation_plan = self._create_transformation_plan(recommendations, schema)
            
            return {
                "analysis": {
                    "dataset_summary": data_summary,
                    "schema": schema,
                },
                "recommendations": recommendations,
                "transformation_plan": transformation_plan,
                "suggested_charts": self._suggest_charts(schema, sample_df),
                "feature_engineering_suggestions": self._suggest_features(schema, sample_df),
            }
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._fallback_analysis(df)
    
    def _prepare_data_summary(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a summary of the dataset for AI analysis."""
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": schema.get("numeric_columns", []),
            "categorical_columns": schema.get("categorical_columns", []),
            "missing_values": {},
            "data_types": {},
            "sample_statistics": {}
        }
        
        # Analyze missing values
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            summary["missing_values"][col] = {
                "count": int(missing_count),
                "percentage": float(missing_pct)
            }
        
        # Data types
        for col in df.columns:
            summary["data_types"][col] = str(df[col].dtype)
        
        # Sample statistics for numeric columns
        for col in schema.get("numeric_columns", []):
            if col in df.columns:
                summary["sample_statistics"][col] = {
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                    "std": float(df[col].std()) if not df[col].isna().all() else None,
                }
        
        # Sample values for categorical columns
        for col in schema.get("categorical_columns", [])[:5]:  # Limit to 5
            if col in df.columns:
                summary["sample_statistics"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(5).to_dict()
                }
        
        return summary
    
    def _get_ai_recommendations(self, data_summary: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered recommendations from Gemini."""
        if not self.model:
            return {}
        
        prompt = f"""You are a senior data scientist analyzing a CSV dataset. Provide recommendations in JSON format.

Dataset Summary:
- Rows: {data_summary['row_count']}
- Columns: {data_summary['column_count']}
- Numeric columns: {data_summary['numeric_columns']}
- Categorical columns: {data_summary['categorical_columns']}
- Missing values: {json.dumps(data_summary['missing_values'], indent=2)}

Please provide recommendations in this JSON format:
{{
    "data_cleaning": {{
        "handle_missing_values": "strategy (drop/impute/keep)",
        "imputation_method": "method for numeric/categorical",
        "outlier_handling": "strategy",
        "normalization_needed": true/false,
        "normalization_method": "standard/min-max/log"
    }},
    "feature_engineering": {{
        "suggested_interactions": ["col1*col2", "col3/col4"],
        "suggested_transformations": ["log(col)", "sqrt(col)"],
        "categorical_encoding": "one-hot/target/label"
    }},
    "insights": [
        "insight 1",
        "insight 2"
    ]
}}

Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            recommendations = json.loads(response_text)
            logger.info("AI recommendations received")
            return recommendations
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return {}
    
    def _create_transformation_plan(self, 
                                    recommendations: Dict[str, Any],
                                    schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a transformation plan based on AI recommendations."""
        plan = {
            "steps": [],
            "feature_engineering": [],
            "normalization": None
        }
        
        if "data_cleaning" in recommendations:
            cleaning = recommendations["data_cleaning"]
            
            # Missing value handling
            if cleaning.get("handle_missing_values") == "impute":
                plan["steps"].append({
                    "action": "impute_missing_values",
                    "method": cleaning.get("imputation_method", "median"),
                    "columns": schema.get("numeric_columns", [])
                })
            
            # Normalization
            if cleaning.get("normalization_needed"):
                plan["normalization"] = {
                    "method": cleaning.get("normalization_method", "standard"),
                    "columns": schema.get("numeric_columns", [])
                }
        
        if "feature_engineering" in recommendations:
            fe = recommendations["feature_engineering"]
            
            if "suggested_interactions" in fe:
                plan["feature_engineering"].extend([
                    {"type": "interaction", "formula": formula}
                    for formula in fe["suggested_interactions"]
                ])
            
            if "suggested_transformations" in fe:
                plan["feature_engineering"].extend([
                    {"type": "transformation", "formula": formula}
                    for formula in fe["suggested_transformations"]
                ])
        
        return plan
    
    def _suggest_charts(self, schema: Dict[str, Any], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Suggest appropriate chart types based on data structure."""
        suggestions = []
        
        numeric_cols = schema.get("numeric_columns", [])
        categorical_cols = schema.get("categorical_columns", [])
        
        # Bar charts for categorical data
        if categorical_cols:
            suggestions.append({
                "type": "bar",
                "reason": "Good for categorical distributions",
                "columns": categorical_cols[:3],
                "priority": "high"
            })
        
        # Pie charts for categorical with low cardinality
        low_cardinality_cats = [
            col for col in categorical_cols 
            if col in df.columns and df[col].nunique() <= 10
        ]
        if low_cardinality_cats:
            suggestions.append({
                "type": "pie",
                "reason": "Good for proportions of categorical data",
                "columns": low_cardinality_cats[:2],
                "priority": "medium"
            })
        
        # Histograms for numeric data
        if numeric_cols:
            suggestions.append({
                "type": "histogram",
                "reason": "Shows distribution of numeric data",
                "columns": numeric_cols[:3],
                "priority": "high"
            })
        
        # Scatter plots for relationships
        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "scatter",
                "reason": "Shows relationships between numeric variables",
                "columns": numeric_cols[:2],
                "priority": "medium"
            })
        
        # Line charts for time series
        datetime_cols = schema.get("datetime_columns", [])
        if datetime_cols and numeric_cols:
            suggestions.append({
                "type": "line",
                "reason": "Good for time series data",
                "columns": datetime_cols[:1] + numeric_cols[:1],
                "priority": "high"
            })
        
        return suggestions
    
    def _suggest_features(self, schema: Dict[str, Any], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Suggest feature engineering operations."""
        suggestions = []
        
        numeric_cols = schema.get("numeric_columns", [])
        categorical_cols = schema.get("categorical_columns", [])
        
        # Interaction features
        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "interaction",
                "formula": f"{numeric_cols[0]} * {numeric_cols[1]}",
                "reason": "Captures multiplicative relationships"
            })
        
        # Ratio features
        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "ratio",
                "formula": f"{numeric_cols[0]} / {numeric_cols[1]}",
                "reason": "Normalizes by another variable"
            })
        
        # Polynomial features
        if numeric_cols:
            suggestions.append({
                "type": "polynomial",
                "formula": f"{numeric_cols[0]}^2",
                "reason": "Captures non-linear relationships"
            })
        
        return suggestions
    
    def _fallback_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Fallback analysis when AI is not available."""
        schema = schema_detector.detect_schema(df, sample_size=min(1000, len(df)))
        
        return {
            "analysis": {
                "dataset_summary": {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                },
                "schema": schema,
            },
            "recommendations": {
                "data_cleaning": {
                    "handle_missing_values": "impute",
                    "imputation_method": "median",
                }
            },
            "transformation_plan": {
                "steps": [{"action": "impute_missing_values", "method": "median"}]
            },
            "suggested_charts": self._suggest_charts(schema, df),
            "feature_engineering_suggestions": self._suggest_features(schema, df),
        }
    
    def apply_transformations(self, 
                             df: pd.DataFrame,
                             transformation_plan: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply transformations suggested by AI agent.
        
        Args:
            df: Input DataFrame
            transformation_plan: Transformation plan from analyze_dataset
            
        Returns:
            Transformed DataFrame
        """
        result_df = df.copy()
        
        # Apply missing value imputation
        for step in transformation_plan.get("steps", []):
            if step.get("action") == "impute_missing_values":
                method = step.get("method", "median")
                columns = step.get("columns", [])
                
                for col in columns:
                    if col in result_df.columns:
                        if method == "median":
                            result_df[col].fillna(result_df[col].median(), inplace=True)
                        elif method == "mean":
                            result_df[col].fillna(result_df[col].mean(), inplace=True)
                        elif method == "mode":
                            result_df[col].fillna(result_df[col].mode()[0] if not result_df[col].mode().empty else 0, inplace=True)
        
        # Apply feature engineering
        for fe in transformation_plan.get("feature_engineering", []):
            if fe.get("type") == "interaction":
                formula = fe.get("formula", "")
                # Simple parsing - expects "col1*col2"
                parts = formula.split("*")
                if len(parts) == 2:
                    col1, col2 = parts[0].strip(), parts[1].strip()
                    if col1 in result_df.columns and col2 in result_df.columns:
                        result_df[f"{col1}_x_{col2}"] = result_df[col1] * result_df[col2]
        
        # Apply normalization
        norm_plan = transformation_plan.get("normalization")
        if norm_plan:
            method = norm_plan.get("method", "standard")
            columns = norm_plan.get("columns", [])
            
            if method == "standard":
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                for col in columns:
                    if col in result_df.columns:
                        values = result_df[[col]].values
                        result_df[col] = scaler.fit_transform(values).flatten()
            elif method == "min-max":
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler()
                for col in columns:
                    if col in result_df.columns:
                        values = result_df[[col]].values
                        result_df[col] = scaler.fit_transform(values).flatten()
        
        return result_df


# Global AI agent instance
ai_agent = DataAnalysisAgent()

