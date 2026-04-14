from core.monitor import get_all_stats
from core.analyzer import analyze

stats = get_all_stats()
issues = analyze(stats)

print("STATS:", stats)
print("\nISSUES:", issues)