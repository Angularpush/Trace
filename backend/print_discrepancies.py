import sqlite3
import json

conn = sqlite3.connect('trace.db')
c = conn.cursor()
rows = c.execute("""
    SELECT id, transaction_id, rule_code, severity, title, description, 
           expected_value, actual_value, difference_value, difference_amount, llm_explanation 
    FROM discrepancies 
    WHERE transaction_id IN (SELECT id FROM transactions WHERE transaction_ref = 'PO-2024-002')
""").fetchall()

print(f"Found {len(rows)} discrepancies for PO-2024-002:\n")
for r in rows:
    print(f"Rule Code: {r[2]}")
    print(f"Severity: {r[3]}")
    print(f"Title: {r[4]}")
    print(f"Description: {r[5]}")
    print(f"Expected: {r[6]}")
    print(f"Actual: {r[7]}")
    print(f"Difference Value: {r[8]}")
    print(f"Diff Amount: {r[9]}")
    print(f"LLM Explanation: {r[10]}")
    evs = c.execute("SELECT document_name, page_number, field_name, exact_value, snippet FROM evidences WHERE discrepancy_id = ?", (r[0],)).fetchall()
    print("Evidences:")
    for ev in evs:
        print(f"   • [{ev[0]}] Page {ev[1]} - {ev[2]}: {ev[3]} | Snippet: {ev[4]}")
    print("-" * 60)

