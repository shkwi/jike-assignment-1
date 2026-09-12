
# 跑全部测试
python -m pytest tests/test_tool_governance.py -v

# 只跑某一个（比如你当前打开文件里的审批绑定测试）
python -m pytest tests/test_tool_governance.py::test_transfer_approval_binding -v

# 跑离线 demo，肉眼验证脱敏和 CONFIRM
python chapter02/tool_governance_demo.py

# 离线 demo 里重点看两行：

call_07 → "action": "confirm", "code": "APPROVAL_REQUIRED"（无审批先确认）
call_08 → "from": "ACC-A-****3456", "to": "ACC-A-****4321"（账号已脱敏）