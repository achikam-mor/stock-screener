import ast

filepath = "AllStocks.txt"
new_tickers = ["MSTY", "MSTR", "NNE", "IONQ", "IREN"]

with open(filepath, 'r') as f:
    content = f.read().strip()
    tickers = ast.literal_eval(content)

for t in new_tickers:
    if t not in tickers:
        tickers.append(t)

tickers.sort()

# Format like AllStocks.txt: multiple tickers per line with proper formatting
formatted = "["
for i, ticker in enumerate(tickers):
    if i > 0:
        formatted += ", "
    if i > 0 and i % 15 == 0:  # New line every 15 tickers
        formatted += "\n"
    formatted += f"'{ticker}'"
formatted += "]"

with open(filepath, 'w') as f:
    f.write(formatted + "\n")
