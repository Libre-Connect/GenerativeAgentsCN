# 实时模拟快速启动

## 30秒开始

```bash
cd /Users/sunyuefeng/GenerativeAgentsCN-1/generative_agents
python web_server.py
```

然后打开浏览器：
```
http://127.0.0.1:5000
```

**就这样！** 你会看到AI角色实时移动和对话。

## 界面说明

- **地图** - 显示整个小镇
- **角色** - 会自动移动和互动
- **对话气泡** - 显示角色活动和对话
- **右侧栏** - 角色列表和状态

## 控制

- **方向键** - 移动视角
- **滚轮** - 缩放
- **暂停/继续** - 右侧按钮（如果有）

## 没有角色？

创建一些测试角色：

```bash
python test_character_generator.py
```

选择"2"（智能选择），输入角色信息，就会自动创建并保存到正确位置。

## 终端会显示什么

```
=== 实时模拟已启动 ===
模拟名称: web_auto_xxxxx
使用真实AI: 是

--- 执行步骤 1 ---
[步骤 1] 张三: 张三正在工作 at [50, 50]
[步骤 1] 李四: 李四在休息 at [45, 55]
✓ 已发送更新到前端，包含 X 个角色
```

## 调整速度

编辑 `web_server.py` 第848行：

```python
time.sleep(2)  # 改成1=更快，5=更慢
```

## 常见问题

**Q: 角色不动？**  
A: 检查终端日志，确保看到"使用真实AI: 是"

**Q: 太慢了？**  
A: 减少角色数量，或改小 `time.sleep()` 的值

**Q: 如何保存？**  
A: 当前不自动保存。如需保存，用命令行模式：`python start.py`

## 完整文档

详细说明请看：
- `REALTIME_SIMULATION_GUIDE.md` - 完整指南
- `REALTIME_SIMULATION_SUMMARY.md` - 实现总结
- `CHARACTER_GENERATOR_GUIDE.md` - 角色创建

## 就是这么简单！

1. 启动：`python web_server.py`
2. 打开：`http://127.0.0.1:5000`
3. 观看：AI角色实时活动

🎉 享受吧！












