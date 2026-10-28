
import json
from pathlib import Path

from claims_intake.budget import Budget
from claims_intake.loop import run
from claims_intake.tracer import Tracer


class FakeUsage:
    input_tokens = 100
    output_tokens = 20


class FakeBlock:
    def __init__(self, block_type, **kwargs):
        self.type = block_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = FakeUsage()


class FakeMessages:
    def __init__(self):
        self.responses = [
            FakeResponse(
                [
                    FakeBlock(
                        "tool_use",
                        id="tool_1",
                        name="lookup_policy",
                        input={"policy_id": "P1"},
                    )
                ],
                "tool_use",
            ),
            FakeResponse(
                [FakeBlock("text", text="Claim processed.")],
                "end_turn",
            ),
        ]

    def create(self, **kwargs):
        if not self.responses:
            raise RuntimeError("Unexpected extra model call")
        return self.responses.pop(0)


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def execute_tool(name, inputs):
    return json.dumps({"tool": name, "result": "mock policy found"})


def main():
    trace_path = Path("evidence") / "trace.jsonl"

    with Tracer(trace_path) as tracer:
        result = run(
            client=FakeClient(),
            model="offline-test-model",
            system="Test system",
            tools=[{"name": "lookup_policy"}],
            messages=[{"role": "user", "content": "Check policy P1"}],
            tool_executor=execute_tool,
            budget=Budget(
                max_input_tokens=1000,
                max_wall_clock_s=60.0,
            ),
            tracer=tracer,
        )

    print(f"Turns: {result.turn_count}")
    print(f"Input tokens: {result.total_input_tokens}")
    print(f"Output tokens: {result.total_output_tokens}")
    print(f"Trace saved to: {trace_path}")
    print(trace_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
