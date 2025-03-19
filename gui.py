import os
import json
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageLabelingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量数据标注系统")

        # 初始化变量
        self.image_folders = []
        self.current_folder_index = 0
        self.current_image_index = 0
        self.image_list = []
        self.json_data = {}
        self.current_photo = None
        self.parent_directory = ""

        # 预设标签选项（单选）
        self.label_options = [
            "0, Unrelated to the product.", 
            "0, Related to the product, but Just life sharing.", 
            "1, Obvious advertisement in the main text.", 
            "1, Advertisement in the comment / Image.", 
            "1, Product with a clear sales-oriented text."
        
        ]
        self.selected_label = tk.StringVar(value="")  # 绑定单选变量

        # 创建 GUI 界面
        self.setup_ui()

    def setup_ui(self):
        """创建 GUI 组件"""
    
        # **主布局**
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # **左侧区域 - 文本输入**
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.Y)

        tk.Label(self.left_frame, text="标题（Title）:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.entry_title = tk.Entry(self.left_frame, width=50, font=("Arial", 12))
        self.entry_title.pack(pady=5)

        tk.Label(self.left_frame, text="描述（Description）:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.text_description = tk.Text(self.left_frame, height=10, width=50, font=("Arial", 12))
        self.text_description.pack(pady=5)

        tk.Label(self.left_frame, text="评论（Comments）:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.text_comments = tk.Text(self.left_frame, height=30, width=50, font=("Arial", 12))
        self.text_comments.pack(pady=5)

        # **中间区域 - 图片显示和按钮**
        self.center_frame = tk.Frame(self.main_frame)
        self.center_frame.pack(side=tk.LEFT, padx=20, pady=10)

        self.folder_label = tk.Label(self.center_frame, text="当前文件夹: ", font=("Arial", 14, "bold"))
        self.folder_label.pack()

        self.img_label = tk.Label(self.center_frame)
        self.img_label.pack()

        # **切换按钮**
        self.btn_frame = tk.Frame(self.center_frame)
        self.btn_frame.pack(pady=10)

        self.btn_prev_folder = tk.Button(self.btn_frame, text="上一文件夹", command=self.prev_folder, font=("Arial", 12))
        self.btn_prev_folder.pack(side=tk.LEFT, padx=5)

        self.btn_prev_image = tk.Button(self.btn_frame, text="上一张", command=self.prev_image, font=("Arial", 12))
        self.btn_prev_image.pack(side=tk.LEFT, padx=5)

        self.btn_next_image = tk.Button(self.btn_frame, text="下一张", command=self.next_image, font=("Arial", 12))
        self.btn_next_image.pack(side=tk.LEFT, padx=5)

        self.btn_next_folder = tk.Button(self.btn_frame, text="下一文件夹", command=self.next_folder, font=("Arial", 12))
        self.btn_next_folder.pack(side=tk.LEFT, padx=5)

        # **加载文件夹**
        self.btn_load = tk.Button(self.center_frame, text="加载文件夹", command=self.load_folder, font=("Arial", 12, "bold"))
        self.btn_load.pack(pady=10)

        # **右侧区域 - 选项**
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.Y)

        self.progress_label = tk.Label(self.center_frame, text="标注进度: 0/0 (0.00%)", font=("Arial", 12, "bold"), fg="blue")
        self.progress_label.pack(pady=5)

        tk.Label(self.right_frame, text="选择标签（单选）:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.radio_frame = tk.Frame(self.right_frame)
        self.radio_frame.pack(pady=5)

        for label in self.label_options:
            rb = tk.Radiobutton(self.radio_frame, text=label, variable=self.selected_label, value=label, font=("Arial", 12))
            rb.pack(anchor="w")

    def load_folder(self):
        """选择父文件夹并递归加载所有子文件夹（跳过已标注的），并显示标注进度"""
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return

        self.parent_directory = folder_selected  # 记录父目录路径
        all_folders = [os.path.join(folder_selected, d) for d in os.listdir(folder_selected) 
                    if os.path.isdir(os.path.join(folder_selected, d))]

        # 读取 CSV 中已标注的文件夹
        annotated_folders = set()
        csv_path = os.path.join(self.parent_directory, "annotations.csv")

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过表头
                annotated_folders = {row[0] for row in reader}

        # 只保留未标注的文件夹
        self.image_folders = [f for f in all_folders if os.path.basename(f) not in annotated_folders]

        # 计算进度
        total_folders = len(all_folders)
        completed_folders = len(annotated_folders)
        progress_percent = (completed_folders / total_folders) * 100 if total_folders > 0 else 0

        # 更新进度标签
        self.progress_label.config(text=f"标注进度: {completed_folders}/{total_folders} ({progress_percent:.2f}%)")

        if not self.image_folders:
            messagebox.showinfo("提示", "所有文件夹都已标注完成！")
            return

        self.current_folder_index = 0
        self.load_current_folder()



    def load_current_folder(self):
        """加载当前文件夹的图片和 JSON 文件"""
        if not self.image_folders:
            return

        current_folder = self.image_folders[self.current_folder_index]
        self.folder_label.config(text=f"当前文件夹: {os.path.basename(current_folder)}")

        # 获取当前文件夹的图片
        self.image_list = [os.path.join(current_folder, f) for f in os.listdir(current_folder)
                           if f.lower().endswith(('png', 'jpg', 'jpeg', 'webp'))]

        # 解析 JSON 数据
        json_path = os.path.join(current_folder, "data.json")
        self.json_data = {"title": "", "description": "", "comments": [], "label": ""}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.json_data = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("错误", "JSON 文件格式错误！")

        # 更新 UI
        self.update_json_fields()
        self.current_image_index = 0
        self.show_image()

    def update_json_fields(self):
        """更新 JSON 数据到 GUI"""
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, self.json_data.get("title", ""))

        self.text_description.delete("1.0", tk.END)
        self.text_description.insert("1.0", self.json_data.get("description", ""))

        self.text_comments.delete("1.0", tk.END)
        comments = self.json_data.get("comments", [])
        if isinstance(comments, list):
            self.text_comments.insert("1.0", "\n".join(comments))

        self.selected_label.set(self.json_data.get("label", ""))

    def show_image(self):
        """显示当前文件夹的当前图片"""
        if not self.image_list:
            self.img_label.config(image=None)
            return

        img_path = self.image_list[self.current_image_index]
        try:
            img = Image.open(img_path)
            img = img.resize((500, 400))  # 增大图片尺寸
            self.current_photo = ImageTk.PhotoImage(img)

            self.img_label.config(image=self.current_photo)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {e}")

    def prev_folder(self):
        """切换到上一文件夹，并更新进度"""
        self.save_annotation()
        if self.current_folder_index > 0:
            self.current_folder_index -= 1
            self.load_current_folder()
            self.update_progress()  # 更新进度显示

    def next_folder(self):
        """切换到下一文件夹，并更新进度"""
        self.save_annotation()
        if self.current_folder_index < len(self.image_folders) - 1:
            self.current_folder_index += 1
            self.load_current_folder()
            self.update_progress()  # 更新进度显示

    def update_progress(self):
        """更新标注进度"""
        total_folders = len(self.image_folders) + len(self.get_annotated_folders())  # 计算所有文件夹
        completed_folders = len(self.get_annotated_folders())  # 已标注的文件夹数
        progress_percent = (completed_folders / total_folders) * 100 if total_folders > 0 else 0

        self.progress_label.config(text=f"标注进度: {completed_folders}/{total_folders} ({progress_percent:.2f}%)")

    def get_annotated_folders(self):
        """获取已标注的文件夹列表"""
        annotated_folders = set()
        csv_path = os.path.join(self.parent_directory, "annotations.csv")

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过表头
                annotated_folders = {row[0] for row in reader}

        return annotated_folders

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_image_index < len(self.image_list) - 1:
            self.current_image_index += 1
            self.show_image()

    def save_annotation(self):
        """保存 JSON 标注并自动更新 CSV"""
        if not self.image_folders:
            return

        current_folder = self.image_folders[self.current_folder_index]
        folder_name = os.path.basename(current_folder)
        json_path = os.path.join(current_folder, "data.json")

        # 获取选中的单选标签
        selected_label = self.selected_label.get()
        self.json_data["label"] = selected_label

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.json_data, f, ensure_ascii=False, indent=4)

        # 自动更新 CSV
        self.update_csv(folder_name, selected_label)

    def update_csv(self, folder_name, label):
        """更新 CSV 文件"""
        csv_path = os.path.join(self.parent_directory, "annotations.csv")
        data = {}

        # 读取现有 CSV 数据
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过表头
                data = {row[0]: row[1] for row in reader}

        # 更新当前文件夹的标注数据
        data[folder_name] = label

        # 写入 CSV
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Folder Name", "Label"])
            for folder, label in data.items():
                writer.writerow([folder, label])

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLabelingApp(root)
    root.mainloop()
