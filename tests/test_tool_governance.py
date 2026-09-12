from dataclasses import replace

import pytest

from tool_governance_demo import (
    ACCOUNTS,
    SIDE_EFFECTS,
    ToolCall,
    base_context,
    build_runtime,
    reset_side_effects,
)


@pytest.fixture(autouse=True)
def clean_state():
    original = dict(ACCOUNTS)
    reset_side_effects()
    yield
    ACCOUNTS.clear()
    ACCOUNTS.update(original)
    reset_side_effects()


@pytest.mark.asyncio
async def test_transfer_schema_rejects_extra():
    runtime, _, _ = build_runtime()
    context = base_context()
    result = await runtime.invoke(
        ToolCall(
            "call_t1",
            "transfer",
            {
                "from_account": "ACC-A-12345",
                "to_account": "ACC-A-654321",
                "amount": 100.0,
                "approved": True,
            },
        ),
        context,
    )
    assert result.code == "INVALID_ARGUMENT"
    assert SIDE_EFFECTS["transfer_executions"] == 0


@pytest.mark.asyncio
async def test_transfer_precheck_insufficient():
    runtime, _, _ = build_runtime()
    context = base_context()
    result = await runtime.invoke(
        ToolCall(
            "call_t2",
            "transfer",
            {"from_account": "ACC-A-654321", "to_account": "ACC-A-888888", "amount": 6000.0},
        ),
        context,
    )
    assert result.code == "INSUFFICIENT_BALANCE"
    assert SIDE_EFFECTS["transfer_executions"] == 0


@pytest.mark.asyncio
async def test_transfer_precheck_exceed_limit():
    runtime, approvals, _ = build_runtime()
    context = base_context()
    arguments = {"from_account": "ACC-A-123456", "to_account": "ACC-A-654321", "amount": 60000.0}
    approvals.approve("approval_t3", context, "transfer", arguments)
    result = await runtime.invoke(
        ToolCall("call_t3", "transfer", arguments),
        replace(context, approval_id="approval_t3"),
    )
    assert result.code == "EXCEED_LIMIT"
    assert SIDE_EFFECTS["transfer_executions"] == 0


@pytest.mark.asyncio
async def test_transfer_approval_binding():
    runtime, approvals, _ = build_runtime()
    context = base_context()
    arguments = {"from_account": "ACC-A-123456", "to_account": "ACC-A-654321", "amount": 100.0}
    approvals.approve("approval_t4", context, "transfer", arguments)
    result = await runtime.invoke(
        ToolCall(
            "call_t4",
            "transfer",
            {**arguments, "amount": 200.0},
        ),
        replace(context, approval_id="approval_t4"),
    )
    assert result.code == "APPROVAL_REQUIRED"
    assert SIDE_EFFECTS["transfer_executions"] == 0


@pytest.mark.asyncio
async def test_transfer_timeout_no_retry():
    runtime, approvals, _ = build_runtime()
    context = base_context()
    arguments = {"from_account": "ACC-A-123456", "to_account": "ACC-A-654321", "amount": 90000.0}
    approvals.approve("approval_t5", context, "transfer", arguments)
    result = await runtime.invoke(
        ToolCall("call_t5", "transfer", arguments),
        replace(context, approval_id="approval_t5"),
    )
    assert result.code == "TIMEOUT_UNKNOWN"
    assert SIDE_EFFECTS["transfer_executions"] <= 1
