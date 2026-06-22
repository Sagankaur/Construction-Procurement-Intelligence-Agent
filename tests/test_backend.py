import unittest
import uuid
from pathlib import Path

from src.alerts import generate_alerts
from src.database import get_procurement_facts, init_db
from src.delay_model import get_delivery_risk_table, load_procurement_data, predict_delay_risk
from src.document_loader import extract_procurement_facts, search_query, store_document
from src.rag_engine import get_answer
from src.vendor_risk import get_vendor_risk_table

TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP_ROOT.mkdir(exist_ok=True)

    def _db_path(self) -> Path:
        return TMP_ROOT / f"test_{uuid.uuid4().hex}.db"

    def test_rag_answers_with_citation(self):
        db_path = self._db_path()
        init_db(db_path)
        doc_id, _ = store_document(
            "po.txt",
            b"Structural steel expected ROJ date is 2026-06-24. ABC Metals is at risk.",
            db_path,
        )
        results = search_query("expected ROJ date for steel", db_path=db_path)
        self.assertGreaterEqual(len(results), 1)
        response = get_answer(
            "What is the expected ROJ date for steel?",
            db_path=db_path,
            use_ollama=False,
        )
        self.assertIn("2026-06-24", response.answer)
        self.assertIn("[po.txt#c0]", response.answer)
        # Verify source cards are populated
        self.assertGreater(len(response.sources), 0)
        self.assertEqual(response.sources[0].filename, "po.txt")

    def test_rag_declines_unsupported_question(self):
        db_path = self._db_path()
        init_db(db_path)
        store_document("po.txt", b"Concrete delivery is on track.", db_path)
        response = get_answer(
            "What is the weather in Delhi?",
            db_path=db_path,
            use_ollama=False,
        )
        self.assertIn("do not have enough information", response.answer)

    def test_delay_vendor_and_alerts_are_populated(self):
        data = load_procurement_data()
        # Pick valid material/vendor from loaded data
        material = data["material_name"].iloc[0]
        vendor = data["vendor_name"].iloc[0]
        phase = data["project_phase"].iloc[0]

        prediction = predict_delay_risk(
            material_name=material,
            vendor_name=vendor,
            order_date="2026-05-18",
            promised_delivery_date="2026-06-20",
            quantity=120,
            priority="Critical",
            project_phase=phase,
        )
        self.assertIn(prediction["risk_level"], {"Low", "Medium", "High"})
        self.assertGreaterEqual(prediction["risk_score"], 0)
        self.assertIn("expected_roj_date", prediction)

        delivery_risks = get_delivery_risk_table()
        self.assertFalse(delivery_risks.empty)
        # Verify po_number column exists with expected format
        self.assertTrue(
            delivery_risks["po_number"].str.startswith("PO-").any(),
            "Expected PO-prefixed order numbers in delivery risk table",
        )

        vendor_risks = get_vendor_risk_table()
        self.assertFalse(vendor_risks.empty)
        # Verify at least one vendor is tracked
        self.assertGreater(len(vendor_risks), 0)

        alerts = generate_alerts()
        self.assertGreaterEqual(len(alerts), 1)
        self.assertTrue(any(alert["type"] == "Delivery Risk" for alert in alerts))

    def test_processed_data_loads_with_expected_columns(self):
        """Verify processed CSV loads with all expected columns for the UI."""
        data = load_procurement_data()
        required = [
            "material_name", "vendor_name", "po_number", "order_date",
            "promised_delivery_date", "actual_delivery_date", "current_status",
            "risk_level", "quantity", "contract_value", "category",
            "project_phase", "criticality", "priority",
        ]
        for col in required:
            self.assertIn(col, data.columns, f"Missing expected column: {col}")

    def test_vendor_risk_table_has_expected_columns(self):
        """Verify vendor risk table has all columns the UI expects."""
        table = get_vendor_risk_table()
        required = [
            "vendor_name", "orders", "on_time_rate", "avg_delay_days",
            "risk_score", "risk_level", "recommendation",
        ]
        for col in required:
            self.assertIn(col, table.columns, f"Missing expected column: {col}")

    def test_extract_procurement_facts(self):
        """Verify fact extraction finds PO numbers, dates, and materials."""
        text = (
            "Purchase Order PO-1234 for Structural Steel, 120 tonnes.\n"
            "Vendor: ABC Metals. Delivery date: 2026-07-15.\n"
            "Total value: INR 84,00,000."
        )
        facts = extract_procurement_facts(text)
        fields = {f["field"] for f in facts}
        self.assertIn("PO Number", fields)
        self.assertIn("Date", fields)
        self.assertIn("Material", fields)
        self.assertIn("Quantity", fields)

    def test_store_document_returns_facts(self):
        """Verify store_document returns extracted facts along with doc_id."""
        db_path = self._db_path()
        init_db(db_path)
        doc_id, facts = store_document(
            "test_po.txt",
            b"PO-5678 for 50 tonnes of TMT Rebar. Delivery: 2026-08-01. Value: Rs 39,00,000.",
            db_path,
        )
        self.assertIsInstance(doc_id, int)
        self.assertGreater(len(facts), 0)

        # Verify facts are persisted in DB
        db_facts = get_procurement_facts(doc_id, db_path)
        self.assertGreater(len(db_facts), 0)


if __name__ == "__main__":
    unittest.main()
