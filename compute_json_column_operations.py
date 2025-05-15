import json
import itertools

def load_and_group_data(filename):
    with open(filename) as f:
        data = json.load(f)
    grouped = {}
    for table_id, tables in data.items():
        rows = {}
        for _, records in tables.items():
            for rec in records:
                row = rec.get("row_name")
                col = rec.get("col_name")
                if not row or col is None:
                    continue
                rows.setdefault(row, []).append(rec)
        grouped[table_id] = rows
    return grouped

def parse_value(val_str, denom):
    try:
        s = val_str.strip()
        neg = s.startswith("(") and s.endswith(")")
        if neg:
            s = s[1:-1]
        s = s.replace("$", "").replace(",", "").strip()
        num = float(s)
        if isinstance(denom, str) and denom.lower() == "billion":
            num *= 1_000  # convert billions to millions
        return -num if neg else num
    except (ValueError, TypeError):
        return 0

def find_operations(grouped):
    for table_id, rows in grouped.items():
        print(f"Table {table_id}:")
        seen = set()

        for row_name, recs in rows.items():
            # filter out percent, NA denom, and NA columns
            candidates = [r for r in recs
                          if r.get("type") != "percent"
                          and r.get("denomination", "").lower() != "na"
                          and r.get("col_name") != "NA"]

            # annotate numeric values
            for r in candidates:
                r["numeric_value"] = parse_value(r.get("Value", ""), r.get("denomination", ""))

            # try each candidate as target (from highest down)
            for target in sorted(candidates, key=lambda x: x["numeric_value"], reverse=True):
                tgt_val = target["numeric_value"]
                others = [r for r in candidates if r is not target]
                found = False

                # look for a combo that sums to the target
                for k in range(1, len(others) + 1):
                    for combo in itertools.combinations(others, k):
                        total = sum(c["numeric_value"] for c in combo)
                        if abs(total - tgt_val) < 1e-6:
                            terms = [c["col_name"] for c in combo]
                            # skip trivial single-term matches
                            if len(terms) < 2:
                                continue
                            expr = " + ".join(terms) + f" = {target['col_name']}"
                            if expr not in seen:
                                print(expr)
                                seen.add(expr)
                            found = True
                            break
                    if found:
                        break

        # if no valid operations found for this table
        if not seen:
            print("No columns to be operated")
        print()

def main():
    grouped = load_and_group_data("Upload you json file path here")
    find_operations(grouped)

if __name__ == "__main__":
    main()
