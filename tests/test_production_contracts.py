"""Static contract checks that do not require optional production dependencies."""
from pathlib import Path
import unittest

ROOT=Path(__file__).parents[1]
class ProductionContractTests(unittest.TestCase):
    def test_production_files_and_migrations_exist(self):
        for path in ['backend/main.py','backend/worker.py','docker-compose.prod.yml','migrations/versions/0007_reviews_recommendations.py']:
            self.assertTrue((ROOT/path).exists(), path)
    def test_contract_routes_present(self):
        source=(ROOT/'backend/api.py').read_text(encoding='utf-8')
        for route in ['generation-jobs','diagnoses','creative-plans','performance-records','promotion-links','ad-experiments','ad-recommendations','review-reports']:
            self.assertIn(route, source)
