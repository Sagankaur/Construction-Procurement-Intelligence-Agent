import unittest
import uuid
from pathlib import Path

from src.alerts import generate_alerts
from src.database import init_db
from src.delay_model import get_delivery_risk_table, predict_delay_risk
from src.document_loader import search_query, store_document
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
        store_document(
            "po.txt",
            b"Structural steel expected ROJ date is 2026-06-24. ABC Metals is at risk.",
            db_path,
        )
        results = search_query("expected ROJ date for steel", db_path=db_path)
        self.assertGreaterEqual(len(results), 1)
        answer = get_answer(
            "What is the expected ROJ date for steel?",
            db_path=db_path,
            use_ollama=False,
        )
        self.assertIn("2026-06-24", answer)
        self.assertIn("[po.txt#c0]", answer)

    def test_rag_declines_unsupported_question(self):
        db_path = self._db_path()
        init_db(db_path)
        store_document("po.txt", b"Concrete delivery is on track.", db_path)
        answer = get_answer(
            "What is the weather in Delhi?",
            db_path=db_path,
            use_ollama=False,
        )
        self.assertIn("do not have enough information", answer)

    def test_delay_vendor_and_alerts_are_populated(self):
        prediction = predict_delay_risk(
            material_name="Structural Steel",
            vendor_name="ABC Metals",
            order_date="2026-05-18",
            promised_delivery_date="2026-06-20",
            quantity=120,
            priority="Critical",
            project_phase="Superstructure",
        )
        self.assertIn(prediction["risk_level"], {"Low", "Medium", "High"})
        self.assertGreaterEqual(prediction["risk_score"], 0)
        self.assertIn("expected_roj_date", prediction)

        delivery_risks = get_delivery_risk_table()
        self.assertFalse(delivery_risks.empty)
        self.assertIn("PO-1001", set(delivery_risks["po_number"]))

        vendor_risks = get_vendor_risk_table()
        self.assertFalse(vendor_risks.empty)
        self.assertIn("ABC Metals", set(vendor_risks["vendor_name"]))

        alerts = generate_alerts()
        self.assertGreaterEqual(len(alerts), 1)
        self.assertTrue(any(alert["type"] == "Delivery Risk" for alert in alerts))


if __name__ == "__main__":
    unittest.main()
