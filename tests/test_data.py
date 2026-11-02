import unittest
from collections import Counter
from generate_data import make_data

DATA=make_data()

class DatasetTests(unittest.TestCase):
    def test_four_fictional_employees(self):
        self.assertEqual(set(DATA["personas"]),{"diego","allison","maria","roger"})
    def test_four_fiscal_years_per_employee(self):
        for user in DATA["personas"]:
            self.assertEqual({r["fy"] for r in DATA["records"] if r["owner"]==user},{"FY24","FY25","FY26","FY27"})
    def test_unique_record_ids(self):
        ids=[r["id"] for r in DATA["records"]]
        self.assertEqual(len(ids),len(set(ids)))
    def test_all_records_have_valid_owners_and_categories(self):
        self.assertTrue(all(r["owner"] in DATA["personas"] and r["category"] in DATA["categories"] for r in DATA["records"]))
    def test_counts_reconcile_with_records(self):
        for person in DATA["personas"]:
            for year in ["FY24","FY25","FY26","FY27"]:
                records=[r for r in DATA["records"] if r["owner"]==person and r["fy"]==year]
                counts=Counter(r["category"] for r in records)
                self.assertEqual(sum(counts.values()),len(records))
    def test_different_role_emphasis(self):
        records=[r for r in DATA["records"] if r["fy"]=="FY26"]
        totals={p:Counter(r["category"] for r in records if r["owner"]==p) for p in DATA["personas"]}
        self.assertGreater(totals["diego"]["spikes"],totals["diego"]["mrs"])
        self.assertGreater(totals["allison"]["manual"],totals["maria"]["manual"])
        self.assertGreater(totals["maria"]["mrs"],totals["diego"]["mrs"])
        self.assertGreater(totals["roger"]["spikes"],totals["maria"]["spikes"])

if __name__=="__main__":
    unittest.main()
