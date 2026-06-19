import pytest
from futedata.collectors.base import BaseCollector, CollectionResult
from futedata.constants import DataSource
import pandas as pd

class MockCollector(BaseCollector):
    source = DataSource.FOOTBALL_DATA

    def collect(self):
        return [
            CollectionResult(
                data={"test": "ok"},
                rows=1,
                endpoint="mock_endpoint",
                schema_hash="123",
                metadata={}
            )
        ]

    def save_raw(self, result, filename=None):
        pass

def test_base_collector_run():
    collector = MockCollector()
    results = collector.run()
    
    assert len(results) == 1
    assert results[0].endpoint == "mock_endpoint"
    assert results[0].status == "success"
    assert results[0].rows_fetched == 1
