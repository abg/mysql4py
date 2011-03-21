"""SSL support"""

for name in ('pyssl', 'm2crypto'):
    try:
        start_ssl = __import__(name, globals(), locals(), []).start_ssl
    except ImportError, exc:
        continue
    else:
        break
else:
    start_ssl = None
