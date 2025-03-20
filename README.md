# AI 长篇小说写作助手

一个基于本地大语言模型的全自动小说创作工具，支持24小时不间断创作，让AI成为你的专属写作伙伴。

![AI小说创作器](https://via.placeholder.com/800x400.png?text=AI小说创作助手)

## 功能特点

- 🤖 **自动创意生成**：自动生成创意十足的小说写作要求
- 📝 **智能内容创作**：基于写作要求自动创作连贯、有逻辑的小说内容
- 🔄 **连续创作循环**：支持24小时不间断自动创作，一篇接一篇
- 💾 **自动保存功能**：创作完成后自动保存为TXT文件，文件名包含字数和时间戳
- 📊 **实时状态监控**：显示当前创作状态和已生成字数
- 🎮 **灵活控制选项**：可随时开始、暂停或停止创作过程

## 系统要求

- Python 3.7+
- [OLLAMA](https://ollama.ai/) 或其他支持API访问的本地大语言模型

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/AI_writing_novel.git
cd AI_writing_novel
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装并配置OLLAMA

1. 从[OLLAMA官网](https://ollama.ai/)下载并安装
2. 拉取所需模型（推荐使用qwen、llama2等支持中文的模型）：

```bash
ollama pull qwq:latest
ollama pull huihui_ai/qwen2.5-1m-abliterated:14b
```

## 使用方法

### 启动应用

```bash
python writing_novel.py
```

### 基本操作

1. **手动创作模式**：
   - 在"写作要求"框中输入你的创作需求
   - 在"目标字数"框中设置期望的字数
   - 点击"开始生成"按钮开始创作
   - 随时可以点击"停止生成"按钮中断创作

2. **全自动创作模式**：
   - 点击"自动生成"按钮
   - 系统会自动生成创意写作要求并开始创作
   - 每篇小说完成后会自动保存并开始创作下一篇
   - 点击"停止自动生成"可以退出自动模式

### 查看创作结果

所有生成的小说都保存在`generated_novels`文件夹中，文件名格式为`[字数]字_[时间戳].txt`。

## 自定义配置

### 修改模型

在`writing_novel.py`文件中，找到以下代码行：

```python
model_name = 'huihui_ai/qwen2.5-1m-abliterated:14b'  # 模型名称
```

将其修改为你想使用的OLLAMA模型名称。

### 调整生成参数

你可以修改`request_data`字典中的参数来调整生成效果：

```python
request_data = {
    "model": model_name,
    "prompt": full_prompt,
    "max_tokens": 1000000,
    "temperature": 0.7,  # 调整创意程度：值越高，输出越多样
    "stream": True
}
```

## 常见问题

### Q: 程序无法连接到OLLAMA API

确保OLLAMA正在运行，并且API端口（默认11434）可访问。检查`http://localhost:11434/api/generate`是否可以访问。

### Q: 生成速度太慢

生成速度主要取决于：
1. 你的硬件配置（CPU/GPU）
2. 选择的模型大小
3. 目标字数设置

可以尝试使用较小的模型或降低目标字数来提高速度。

### Q: 按钮点击没有响应

这可能是因为程序正在进行密集计算。耐心等待，或重启应用。

## 高级用法

### 修改创意生成提示词

在`generate_user_prompt`函数中，你可以修改提示词以生成不同风格的写作要求：

```python
prompt = '''你是一个创意写作专家，请生成一个有趣的小说写作要求。要求：
...
'''
```

### 加入自定义主题

你可以修改提示词，加入特定主题或风格：

```python
prompt = '''你是一个创意写作专家，请生成一个科幻主题的小说写作要求。要求：
...
'''
```

## 贡献指南

欢迎提交Pull Request或Issues来帮助改进这个项目！贡献前请先查看现有Issues，确保不会重复工作。

## 许可证

本项目采用MIT许可证 - 详情请查看[LICENSE](LICENSE)文件。

## 致谢

- 感谢OLLAMA团队提供优秀的本地大语言模型运行环境
- 感谢所有开源AI模型的贡献者们

---

如有任何问题或建议，欢迎提Issue或联系项目维护者。

**享受AI辅助创作的乐趣吧！**
