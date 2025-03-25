import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import json
from gen_ai_usecase import (
    extract_text_from_pdf,
    parse_rules_with_openai,
    pre_aggregate_data,
    map_rules_to_dataset,
    validate_batch_with_openai,
    validate_dataset_with_openai,
    display_violations
)
import os


# Test 1: Rule Parsing with OpenAI
def test_parse_rules_with_openai():
    """Test rule parsing with mocked OpenAI response"""
    test_text = "Transactions must be between $100 and $10,000"
    
    # Create a mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = """
    [
        {"type": "min_value", "field": "Transaction_Amount", "value": 100},
        {"type": "max_value", "field": "Transaction_Amount", "value": 10000}
    ]
    """
    
    with patch('gen_ai_usecase.client.chat.completions.create', return_value=mock_response):
        rules = parse_rules_with_openai(test_text)
        assert len(rules) == 2
        assert rules[0]["type"] == "min_value"
        assert rules[0]["value"] == 100
        assert rules[1]["type"] == "max_value"
        assert rules[1]["value"] == 10000

# Test 2: Data Aggregation
def test_pre_aggregate_data():
    """Test data pre-aggregation functionality"""
    test_data = pd.DataFrame({
        "Customer_ID": [1, 1, 2, 2, 2],
        "Transaction_Amt": [100, 200, 50, 150, 300]
    })
    
    aggregated = pre_aggregate_data(test_data)
    
    # Check new columns exist
    assert "Total_Amount" in aggregated.columns
    assert "Transaction_Count" in aggregated.columns
    
    # Check aggregation values
    customer1 = aggregated[aggregated["Customer_ID"] == 1].iloc[0]
    assert customer1["Total_Amount"] == 300
    assert customer1["Transaction_Count"] == 2
    
    customer2 = aggregated[aggregated["Customer_ID"] == 2].iloc[0]
    assert customer2["Total_Amount"] == 500
    assert customer2["Transaction_Count"] == 3

# Test 3: Rule to Dataset Mapping
def test_map_rules_to_dataset():
    """Test fuzzy matching of rules to dataset columns"""
    rules = [
        {"type": "digit_length", "field": "Customer ID"},
        {"type": "min_value", "field": "Transaction Amount"}
    ]
    
    dataset = pd.DataFrame({
        "Customer_ID": [1, 2, 3],
        "Transaction_Amt": [100, 200, 300],
        "Transaction_Date": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    
    mapped_rules = map_rules_to_dataset(rules, dataset)
    
    assert len(mapped_rules) == 2
    assert mapped_rules[0]["field"] == "Customer_ID"
    assert mapped_rules[1]["field"] == "Transaction_Amt"

# Test 4: Batch Validation
def test_validate_batch_with_openai():
    """Test batch validation with mocked OpenAI response"""
    test_batch = pd.DataFrame({
        "Customer_ID": [1, 2, 3],
        "Transaction_Amt": [50, 150, 250],
        "Total_Amount": [50, 150, 250]
    })
    
    rules = [
        {"type": "min_value", "field": "Transaction_Amt", "value": 100},
        {"type": "aggregated_amount", "field": "Total_Amount", "threshold": 200}
    ]
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = """
    {
        "results": [
            {
                "record_id": 0,
                "is_valid": false,
                "violations": ["Transaction amount below minimum"]
            },
            {
                "record_id": 1,
                "is_valid": true,
                "violations": []
            },
            {
                "record_id": 2,
                "is_valid": false,
                "violations": ["Aggregated amount exceeds threshold"]
            }
        ]
    }
    """
    
    with patch('gen_ai_usecase.client.chat.completions.create', return_value=mock_response):
        result = validate_batch_with_openai(test_batch, rules, start_index=0)
        assert len(result["results"]) == 3
        assert result["results"][0]["is_valid"] is False
        assert result["results"][1]["is_valid"] is True
        assert result["results"][2]["is_valid"] is False

# Test 5: Display Violations
def test_display_violations(capsys):
    """Test the display of violations"""
    violations = [
        {
            "record_id": 1,
            "record": {"Customer_ID": 1, "Transaction_Amt": 50},
            "violations": ["Amount below minimum"]
        }
    ]
    
    rules = [
        {"type": "min_value", "field": "Transaction_Amt", "value": 100}
    ]
    
    display_violations(violations, rules)
    captured = capsys.readouterr()
    
    assert "Violations Found" in captured.out
    assert "Record ID: 1" in captured.out
    assert "Amount below minimum" in captured.out

# Test 7: Empty Dataset Validation
def test_validate_empty_dataset():
    """Test validation with empty dataset"""
    empty_df = pd.DataFrame(columns=["Customer_ID", "Transaction_Amt"])
    rules = [{"type": "min_value", "field": "Transaction_Amt", "value": 100}]
    
    # Mock OpenAI response for empty dataset
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = '{"results": []}'
    
    with patch('gen_ai_usecase.client.chat.completions.create', return_value=mock_response):
        violations = validate_dataset_with_openai(empty_df, rules)
        assert len(violations) == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])