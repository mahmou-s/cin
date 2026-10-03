import os


def pytest_sessionfinish(session, exitstatus):
    if os.getenv("CIN_FAIL_ON_SKIP") != "1":
        return
    terminal = session.config.pluginmanager.getplugin("terminalreporter")
    skipped = len(terminal.stats.get("skipped", [])) if terminal else 0
    if skipped:
        session.exitstatus = 1
        if terminal:
            terminal.write_sep("=", f"CIN_FAIL_ON_SKIP: {skipped} skipped test(s)")

