# Examples

Each script demonstrates one aspect of transitbus. They are self-contained --
they define their own events and print what happens -- so you can run any of
them on their own:

```bash
uv run python examples/01_request_response.py
```

| File | Shows |
| ---- | ----- |
| [`01_request_response.py`](01_request_response.py) | Dispatch an event and await the value a handler returns |
| [`02_subscribing.py`](02_subscribing.py) | The three ways to subscribe, and base-class handlers that see everything |
| [`03_results_and_errors.py`](03_results_and_errors.py) | Multiple handlers, the result views, and how failures surface |
| [`04_causality.py`](04_causality.py) | Automatic `parent_id` links between an event and events dispatched from its handler |
| [`05_waiting.py`](05_waiting.py) | `bus.expect(...)` to wait for a matching event without a handler |
| [`06_forwarding.py`](06_forwarding.py) | Forwarding events between buses, and why cycles terminate |
| [`07_write_ahead_log.py`](07_write_ahead_log.py) | The `JsonlWAL` and a custom `WAL` subclass |
| [`orders.py`](orders.py) | An end-to-end walkthrough tying the pieces together |
