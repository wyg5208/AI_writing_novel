import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests
import json
import threading
import re
import time
import os
from datetime import datetime

# 全局变量，用于存储已生成的内容
generated_content = ""
is_generating = False  # 控制生成过程的标志
update_timer = None  # 用于存储更新计时器的ID
model_name = 'huihui_ai/qwen2.5-1m-abliterated:14b'  # 模型名称 
is_auto_generating = False 

# 生成写作提示的方法
def generate_user_prompt():
    try:
        api_url = 'http://localhost:11434/api/generate'
        prompt = '''你是一个创意写作专家，请生成一个严谨具体的小说写作要求。要求：
        1. 包含一个吸引人的小说名字；
        2. 小说的风格设定和描述,小说的风格以现代都市情感等元素为主。
        3. 包含具体的故事背景、人物设定，
        4. 输出具体的章节大纲和每一章节的剧情梗概；
        5. 要有创意，不要太过俗套；
        6. 只输出写作要求本身，不要包含任何其他说明；
        7. 每次生成的内容都要不一样，保持新颖性。
        8. 输出的小说要包含至少5个章节。
        9. 输出的小说的每一章节都要有具体的剧情梗概。
        '''
        
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "temperature": 0.9,  # 使用较高的温度以增加创意性
            "stream": False
        }
        
        response = requests.post(api_url, json=request_data, timeout=30)
        response.raise_for_status()
        
        # 获取生成的提示词
        result = response.json()
        new_prompt = result.get('response', '').strip()
        
        # 清空并更新提示词输入框
        prompt_entry.delete("1.0", tk.END)
        prompt_entry.insert("1.0", new_prompt)
        
        return True
    except Exception as e:
        update_status(f"生成写作要求时出错：{str(e)}")
        return False

# 自动生成的处理函数
def auto_generate():
    global is_auto_generating
    
    if is_generating:
        messagebox.showinfo("提示", "正在生成中，请稍候...")
        return
    
    is_auto_generating = True
    auto_generate_button.config(text="停止自动生成")
    
    # 开始第一轮生成
    if generate_user_prompt():
        generate_text()

# 停止自动生成
def stop_auto_generate():
    global is_auto_generating
    is_auto_generating = False
    auto_generate_button.config(text="自动生成")
    stop_generation()

# 切换自动生成状态
def toggle_auto_generate():
    if is_auto_generating:
        stop_auto_generate()
    else:
        auto_generate()


# 判断写作目标是否完成的方法
def is_writing_complete(content, target_word_count):
    # 计算中文字符数（每个中文字符算一个字）
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
    # 计算英文单词数（假设英文单词由空格分隔）
    english_words = re.findall(r'\b[a-zA-Z]+\b', content)
    
    # 总字数 = 中文字符数 + 英文单词数
    total_words = len(chinese_chars) + len(english_words)
    
    # 判断是否达到目标字数
    return total_words >= target_word_count

# 更新状态标签
def update_status(message):
    status_label.config(text=message)
    if "错误" in message:
        status_label.config(bg='#ffebee', fg='#c62828')  # 错误状态使用红色
    elif "完成" in message:
        status_label.config(bg='#e8f5e9', fg='#2e7d32')  # 完成状态使用绿色
    elif "生成中" in message:
        status_label.config(bg='#e3f2fd', fg='#1565c0')  # 生成中状态使用蓝色
    else:
        status_label.config(bg='#e8e8e8', fg='#333333')  # 默认状态
    root.update_idletasks()

# 定期更新状态的函数
def periodic_status_update():
    global update_timer
    if is_generating:
        word_count = len(re.findall(r'[\u4e00-\u9fff]', generated_content)) + len(re.findall(r'\b[a-zA-Z]+\b', generated_content))
        update_status(f"正在生成中...当前已生成约{word_count}字")
        # 每500毫秒更新一次状态
        update_timer = root.after(500, periodic_status_update)
    else:
        # 如果不再生成，则停止定期更新
        if update_timer:
            root.after_cancel(update_timer)
            update_timer = None

# 保存生成的内容到文件
def save_content_to_file():
    if not generated_content.strip():
        return
        
    # 确保输出目录存在
    output_dir = "generated_novels"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 计算当前内容的字数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', generated_content))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', generated_content))
    total_words = chinese_chars + english_words
    
    # 生成文件名：字数_时间戳.txt
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{total_words}字_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(generated_content)
        update_status(f"内容已保存至：{filename}")

                # 如果是自动生成模式，则继续生成下一个故事
        if is_auto_generating:
            root.after(2000, lambda: continue_auto_generate())

    except Exception as e:
        update_status(f"保存文件时出错：{str(e)}")

# 继续自动生成的方法
def continue_auto_generate():
    if is_auto_generating and not is_generating:
        if generate_user_prompt():
            generate_text()




# 生成文本的线程函数
def generate_text_thread():
    global generated_content, is_generating, update_timer
    
    try:
        # 获取用户输入的提示和目标字数
        user_prompt = prompt_entry.get("1.0", tk.END).strip()       
        try:
            target_word_count = int(word_count_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的目标字数")
            is_generating = False
            return
        
        # 清空显示区域
        output_text.delete(1.0, tk.END)
        generated_content = ""
        
        # 循环生成文本，直到达到目标字数
        while not is_writing_complete(generated_content, target_word_count) and is_generating:
            # 构造提示词（包括已生成的内容）
            if generated_content:
                full_prompt = f'''
                你是一个小说作家，擅长写现代都市情感的小说，请根据以下用户写作要求和已经写作的内容，开始或者继续创作：
                ## 用户的写作要求：
                 {user_prompt}

                ## 已经写作的内容：
                {generated_content}

                ## 注意事项：
                1. 请根据用户写作要求和已经写作的内容，继续创作。
                2. 每次生成并输出一个章节的内容，不要输出多个章节的内容。
                3. 请保持故事的连贯性和逻辑性。
                4. 请保持故事的节奏感，不要出现过于冗长或重复的描述。
                5. 请保持故事的紧凑性，不要出现过于拖沓的情节。
                6. 请保持故事的新鲜感，不要出现过于俗套的情节。
                6. 请保使用中文写作；
                7. 只输出小说正文，不要输出任何解释、说明。
                8. 如果你觉得用户写作要求已经完成，请停止生成。
                '''
            else:
                full_prompt = user_prompt
            
            # 准备请求参数
           
            api_url = 'http://localhost:11434/api/generate'
            request_data = {
                "model": "qwq:latest",
                "prompt": full_prompt,
                "max_tokens": 1000000,
                "temperature": 0.7,
                "stream": True
            }
            
            # 发送请求并获取流式响应
            response = requests.post(api_url, json=request_data, stream=True, timeout=30)
            response.raise_for_status()
            
            # 处理本次生成的内容
            new_content = ""
            
            # 处理流式响应
            for line in response.iter_lines():
                # 如果已停止生成，则跳出响应处理循环
                if not is_generating:
                    break
                    
                if line:
                    # 解析 JSON 数据
                    data = json.loads(line.decode('utf-8'))
                    # 提取 response 字段
                    text_chunk = data.get('response', '')
                    # 更新显示区域
                    output_text.insert(tk.END, text_chunk)
                    output_text.see(tk.END)  # 自动滚动到最新内容
                    root.update_idletasks()  # 更新UI
                    # 累积新内容
                    new_content += text_chunk
                    
                    # 检查是否完成（当 done 为 true 时）
                    if data.get('done', False):
                        break
            
            # 如果已停止生成，则退出主循环
            if not is_generating:
                update_status("生成已停止")
                break
                
            # 更新已生成的内容
            generated_content += new_content
            
            # 检查是否应该继续生成
            if not is_generating:
                update_status("生成已停止")
                break
                
            # 模拟文本处理的延迟，避免过快请求
            root.after(1000)
        
        if is_generating and is_writing_complete(generated_content, target_word_count):
            update_status(f"写作完成！共生成{len(generated_content)}字")
            save_content_to_file()  # 自动保存内容
            
        elif not is_generating:
            update_status(f"用户已停止生成。当前已生成{len(generated_content)}字")
            save_content_to_file()  # 自动保存内容
        
    except requests.exceptions.RequestException as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
        update_status("生成过程出错")
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
        update_status("生成过程出错")
    finally:
        is_generating = False

# 调用模型并更新显示区域的函数
def generate_text():
    global generated_content, is_generating, update_timer
    
    if is_generating:
        messagebox.showinfo("提示", "正在生成中，请稍候...")
        return
    
    is_generating = True
    
    # 开始定期更新状态
    periodic_status_update()
    
    # 创建一个新线程来执行生成过程
    thread = threading.Thread(target=generate_text_thread)
    thread.daemon = True
    thread.start()

# 停止生成的函数
def stop_generation():
    global is_generating
    is_generating = False
    update_status("用户已停止生成")

# 创建主窗口
root = tk.Tk()
root.title("长篇小说写作助手")
root.geometry("1000x800")
root.configure(bg='#f0f0f0')  # 设置窗口背景色

# 创建主容器
main_container = tk.Frame(root, bg='#f0f0f0')
main_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# 创建标题
title_label = tk.Label(
    main_container,
    text="AI 长篇小说写作助手",
    font=('Microsoft YaHei UI', 16, 'bold'),
    bg='#f0f0f0',
    fg='#333333'
)
title_label.pack(pady=(0, 20))

# 创建输入区域框架
input_frame = tk.LabelFrame(
    main_container,
    text="写作设置",
    font=('Microsoft YaHei UI', 10),
    bg='#f0f0f0',
    fg='#333333',
    padx=10,
    pady=10
)
input_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

# 创建提示词输入区域
prompt_label = tk.Label(
    input_frame,
    text="写作要求：",
    font=('Microsoft YaHei UI', 10),
    bg='#f0f0f0',
    fg='#333333'
)
prompt_label.pack(side=tk.LEFT, padx=(5, 10), anchor='n')

# 创建一个Frame来容纳文本框
prompt_container = tk.Frame(input_frame, bg='#f0f0f0')
prompt_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

prompt_entry = tk.Text(
    prompt_container,
    width=50,
    height=5,
    font=('Microsoft YaHei UI', 10),
    wrap=tk.WORD,
    relief=tk.SOLID
)
prompt_entry.pack(fill=tk.BOTH, expand=True, padx=2)

# 创建字数设置区域
word_count_frame = tk.Frame(input_frame, bg='#f0f0f0')
word_count_frame.pack(side=tk.LEFT, padx=20)

word_count_label = tk.Label(
    word_count_frame,
    text="目标字数：",
    font=('Microsoft YaHei UI', 10),
    bg='#f0f0f0',
    fg='#333333'
)
word_count_label.pack(side=tk.LEFT)

word_count_entry = tk.Entry(
    word_count_frame,
    width=10,
    font=('Microsoft YaHei UI', 10),
    relief=tk.SOLID
)
word_count_entry.pack(side=tk.LEFT, padx=5)
word_count_entry.insert(0, "1000")

# 创建控制按钮区域
button_frame = tk.Frame(main_container, bg='#f0f0f0')
button_frame.pack(pady=10, fill=tk.X)

# 添加生成按钮
generate_button = tk.Button(
    button_frame,
    text="开始生成",
    command=generate_text,
    font=('Microsoft YaHei UI', 10)
)
generate_button.pack(side=tk.LEFT, padx=10)

# 添加停止按钮
stop_button = tk.Button(
    button_frame,
    text="停止生成",
    command=stop_generation,
    font=('Microsoft YaHei UI', 10)
)
stop_button.pack(side=tk.LEFT, padx=10)

# 添加自动生成按钮
auto_generate_button = tk.Button(
    button_frame,
    text="自动生成",
    command=toggle_auto_generate,
    font=('Microsoft YaHei UI', 10)
)
auto_generate_button.pack(side=tk.LEFT, padx=10)

# 添加状态标签（放在按钮右边）
status_label = tk.Label(
    button_frame,
    text="就绪",
    font=('Microsoft YaHei UI', 10),
    bg='#e8e8e8',
    fg='#333333',
    relief=tk.GROOVE,
    padx=10,
    pady=5
)
status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)    

# 创建显示区域
output_frame = tk.LabelFrame(
    main_container,
    text="写作内容",
    font=('Microsoft YaHei UI', 10),
    bg='#f0f0f0',
    fg='#333333',
    padx=10,
    pady=10
)
output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)

output_text = scrolledtext.ScrolledText(
    output_frame,
    wrap=tk.WORD,
    width=100,
    height=30,
    font=('Microsoft YaHei UI', 11),
    bg='#ffffff',
    fg='#333333'
)
output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# 启动主循环
root.mainloop()
