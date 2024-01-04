import tkinter as tk

def on_select(event):
    # 获取所选项的索引

    selected_index = listbox.curselection()

    print(selected_index)

    # 清空文本框
    text.delete("1.0", tk.END)

    # 根据所选项的索引显示不同的内容
    if selected_index:
        index = selected_index[0]
        if index == 0:
            text.insert(tk.END, "Hello")
        elif index == 1:
            text.insert(tk.END, "World")
        else:
            text.insert(tk.END, "!!!")

# 创建主窗口
root = tk.Tk()
root.title("Listbox with Text Example")

menubar = tk.Menu(root).pack()        # 建立最上层菜单
# 建立菜单类别对象，并将此菜单类别命名为File
filemenu = tk.Menu(menubar,tearoff=False)
menubar.add_cascade(label="File",menu=filemenu)
# 在File菜单内建立菜单列表Exit
filemenu.add_command(label="Exit",command=root.destroy)

# 创建一个Listbox
listbox = tk.Listbox(root)
listbox.pack(side=tk.LEFT, padx=10, pady=10)

# 向Listbox中添加项
for item in ["Option 1", "Option 2", "Option 3"]:
    listbox.insert(tk.END, item)

# 设置选中项变化时的回调函数
listbox.bind("<<ListboxSelect>>", on_select)

# 创建一个Text组件
text = tk.Text(root, width=30, height=10)
text.pack(side=tk.LEFT, padx=10, pady=10)

root.config(menu=menubar)

# 运行主循环
root.mainloop()
