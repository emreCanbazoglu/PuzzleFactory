# Session Resume Checklist

- [ ] Run `bash .specify/scripts/bash/check-prerequisites.sh`
- [ ] Run `bash .specify/scripts/bash/session-status.sh`
- [ ] Read latest entry in `runs/wave_001/execution_log.md`
- [ ] Validate run config with `python3 .specify/scripts/python/validate_run_config.py runs/wave_001/run_config.json`
- [ ] Validate decision policy with `python3 .specify/scripts/python/check_decision_policy.py runs/wave_001/run_config.json`
- [ ] Validate template completeness with `python3 .specify/scripts/python/check_template_fields.py`
- [ ] Pick first unchecked task in active `specs/<feature>/tasks.md`
- [ ] Record completed work in both `tasks.md` and run execution log
