# Logging System - Quick Reference

## TL;DR - What You Need to Know

- **Console**: Clean, readable output - one line per ticket
- **`ai_services.log`**: All details including debug timing
- **`ai_services_performance.log`**: Dedicated performance metrics
- **`ai_services_errors.log`**: Errors only for quick issue spotting

All files rotate automatically when they get big.

---

## Common Tasks

### View Console Output (what you see while running)
```bash
# Run normally - just execute your script
python process_tickets.py

# Output looks like:
# ai_services.processor - INFO - Found 100 ticket file(s) to process
# ai_services.processor - INFO - Processing: tickets.json (100 ticket(s))
# ai_services.processor - INFO - Processed ticket 'X' in 52.74ms - Category: Y
# ... (one line per ticket)
# ai_services.processor - INFO - Batch complete: 100 total tickets in 5.32s
# ai_services.processor - INFO - PERFORMANCE SUMMARY
# ai_services.processor - INFO - model.encode: count=100, avg=5.23ms, ...
```

### Check Performance Metrics (detailed timing analysis)
```bash
# Real-time performance log
tail -f project-root/logs/ai_services/ai_services_performance.log

# Search for specific operation
grep "model.encode" project-root/logs/ai_services/ai_services_performance.log

# Count timing entries
wc -l project-root/logs/ai_services/ai_services_performance.log

# Last 20 timing entries
tail -20 project-root/logs/ai_services/ai_services_performance.log
```

### Check All Activity (debug everything)
```bash
# Real-time full log
tail -f project-root/logs/ai_services/ai_services.log

# Search for specific ticket ID or error
grep "ticket_123" project-root/logs/ai_services/ai_services.log

# Find all errors in the full log
grep ERROR project-root/logs/ai_services/ai_services.log
```

### Check Errors Only (quick issue diagnosis)
```bash
# Real-time errors
tail -f project-root/logs/ai_services/ai_services_errors.log

# All errors from today
grep ERROR project-root/logs/ai_services/ai_services_errors.log | wc -l

# Specific error type
grep "Failed to process" project-root/logs/ai_services/ai_services_errors.log
```

### Find Performance Issues
```bash
# What's slow?
grep "took" project-root/logs/ai_services/ai_services_performance.log | sort -t' ' -k9 -rn | head -10

# Average timing across all operations
awk '{print $NF}' project-root/logs/ai_services/ai_services_performance.log | \
  sed 's/ms.*//' | \
  awk '{sum+=$1; count++} END {print "Average: " sum/count "ms"}'
```

### Analyze Performance Summary
```bash
# Extract performance summary from main log
grep -A 30 "PERFORMANCE SUMMARY" project-root/logs/ai_services/ai_services.log

# Or from performance log
tail -50 project-root/logs/ai_services/ai_services_performance.log
```

---

## File Locations

```
📁 project-root/
  └── 📁 logs/
      └── 📁 ai_services/
          ├── 📄 ai_services.log              (main, all details)
          ├── 📄 ai_services.log.1-5          (backups)
          ├── 📄 ai_services_performance.log  (timing only)
          ├── 📄 ai_services_performance.log.1-3  (backups)
          ├── 📄 ai_services_errors.log       (errors only)
          └── 📄 ai_services_errors.log.1-10  (backups)
```

---

## Log Levels Explained

| Level | Console | File | Perf | Error | Usage |
|-------|---------|------|------|-------|-------|
| DEBUG | ✗ | ✓ | ✓ | ✗ | Detailed timing info |
| INFO | ✓ | ✓ | ✗ | ✗ | Key events, status |
| WARNING | ✗ | ✓ | ✗ | ✓ | Issues that aren't critical |
| ERROR | ✗ | ✓ | ✗ | ✓ | Failed operations |
| CRITICAL | ✗ | ✓ | ✗ | ✓ | System failures |

---

## Reading Log Files

### Main Log Format
```
2026-01-31 10:05:32,123 - ai_services.processor - INFO - [process_ticket:42] - Processed ticket 'Network' in 52.74ms
                          └─ module name                 └─ function name:line
```

### Performance Log Format
```
2026-01-31 10:05:32,123 - ai_services.performance - [TIMING] model.encode() took 5.23ms (text length: 250)
                                                           └─ timing measurement
```

---

## Troubleshooting

### "I'm seeing too many lines in console"
→ That's actually fixed! Console now only shows INFO level. If you're still seeing DEBUG lines, check if console handler level got changed.

### "I can't find my timing data"
→ Check `ai_services_performance.log` or the general `ai_services.log` (performance logs append to both).

### "Log files are huge"
→ They auto-rotate when they exceed 10MB. Check the numbered backups (.log.1, .log.2, etc.)

### "I need to search for specific tickets"
→ Use grep: `grep "your_ticket_id" project-root/logs/ai_services/ai_services.log`

### "When do logs get rotated?"
→ Automatically when files reach their size limit:
- Main: 10MB → keep 5 old files
- Performance: 5MB → keep 3 old files  
- Errors: 5MB → keep 10 old files

---

## Performance Analysis Examples

### Find average processing time per ticket
```bash
grep "Processed ticket" project-root/logs/ai_services/ai_services.log | \
  grep -oP 'in \K[0-9.]+' | \
  awk '{sum+=$1; count++} END {print "Avg: " sum/count "ms, Total: " sum "ms, Tickets: " count}'
```

### Find slowest tickets
```bash
grep "Processed ticket" project-root/logs/ai_services/ai_services.log | \
  grep -oP 'Processed ticket '\''\K[^'\'']+' | head -5
```

### Monitor in real-time (update every 1 sec)
```bash
watch -n 1 'tail project-root/logs/ai_services/ai_services.log'
```

### Compare performance over runs
```bash
# Before optimization
tail project-root/logs/ai_services/ai_services.log | grep "PERFORMANCE SUMMARY" -A 20

# After optimization
tail project-root/logs/ai_services/ai_services.log | grep "PERFORMANCE SUMMARY" -A 20
```

---

## Integration Checklist

- [ ] Logging system set up ✓
- [ ] Console clean (no spam) ✓
- [ ] Metrics collected automatically ✓
- [ ] Summary printed at end ✓
- [ ] Files rotate automatically ✓
- [ ] Ready for production ✓

---

## Next Steps When Scaling

As you grow, consider:

1. **Add metrics to Prometheus**: Parse the PERFORMANCE SUMMARY
2. **Send logs to ELK**: Use Filebeat to ship logs
3. **Create Grafana dashboards**: Visualize avg/min/max timings
4. **Set up alerts**: Alert when operations exceed threshold
5. **Add distributed tracing**: Use OpenTelemetry for multi-service tracking

---

**Questions?** Check [LOGGING_SETUP.md](LOGGING_SETUP.md) for detailed info.

**Diagrams?** See [LOGGING_ARCHITECTURE.md](../LOGGING_ARCHITECTURE.md) for system flow.

**Summary?** Read [LOGGING_REFACTOR_SUMMARY.md](LOGGING_REFACTOR_SUMMARY.md) for what changed.
