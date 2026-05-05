import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import classifier

class EngagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Engagement Analyzer")
        self.data = []
        self.post_id_counter = 1
        
        f1 = ttk.Frame(root, padding=5)
        f1.pack(fill=tk.X)
        self.var_type = tk.StringVar(value="reel")
        self.var_hour = tk.StringVar(value="18")
        self.var_hashtags = tk.StringVar(value="15")
        self.var_caption = tk.StringVar(value="medium")
        self.var_interaction = tk.StringVar(value="yes")
        self.var_day = tk.StringVar(value="Wednesday")
        self.var_engagement = tk.StringVar(value="Auto-Predict")
        
        ttk.Label(f1, text="Type:").grid(row=0, column=0)
        ttk.Combobox(f1, textvariable=self.var_type, values=["reel", "image", "carousel"]).grid(row=0, column=1)
        
        ttk.Label(f1, text="Hour:").grid(row=0, column=2)
        ttk.Spinbox(f1, from_=0, to=23, textvariable=self.var_hour).grid(row=0, column=3)
        
        ttk.Label(f1, text="Tags:").grid(row=0, column=4)
        ttk.Spinbox(f1, from_=0, to=30, textvariable=self.var_hashtags).grid(row=0, column=5)
        
        ttk.Label(f1, text="Caption:").grid(row=1, column=0)
        ttk.Combobox(f1, textvariable=self.var_caption, values=["short", "medium", "long"]).grid(row=1, column=1)
        
        ttk.Label(f1, text="Asks Interaction?:").grid(row=1, column=2)
        ttk.Combobox(f1, textvariable=self.var_interaction, values=["yes", "no"]).grid(row=1, column=3)
        
        ttk.Label(f1, text="Day:").grid(row=1, column=4)
        ttk.Combobox(f1, textvariable=self.var_day, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).grid(row=1, column=5)
        
        ttk.Label(f1, text="Result:").grid(row=2, column=0)
        ttk.Combobox(f1, textvariable=self.var_engagement, values=["Auto-Predict", "High", "Low"]).grid(row=2, column=1)
        ttk.Button(f1, text="Add Post", command=self.add_post).grid(row=2, column=2, columnspan=2)

        f2 = ttk.Frame(root)
        f2.pack(fill=tk.BOTH, expand=True)
        cols = ("id", "type", "hour", "hashtags", "caption", "asks_interaction", "day", "engagement", "score")
        self.tree = ttk.Treeview(f2, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Delete>", self.delete_selected)

        f3 = ttk.Frame(root, padding=5)
        f3.pack(fill=tk.X)
        ttk.Button(f3, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT)
        ttk.Button(f3, text="Save to CSV", command=self.save_csv).pack(side=tk.LEFT)
        ttk.Button(f3, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT)
        ttk.Button(f3, text="Analyze Trends", command=self.analyze_trends).pack(side=tk.RIGHT)
        ttk.Button(f3, text="Actionable Insights", command=self.show_insights).pack(side=tk.RIGHT)

    def add_post(self):
        try:
            ph = int(self.var_hour.get())
            ht = int(self.var_hashtags.get())
            pred, score, _ = classifier.classify_engagement(
                self.var_type.get(), ph, ht, self.var_caption.get(),
                self.var_interaction.get(), self.var_day.get()
            )
            eng = pred if self.var_engagement.get() == "Auto-Predict" else self.var_engagement.get()
            
            row = {"post_id": self.post_id_counter, "content_type": self.var_type.get(),
                   "posting_hour": ph, "num_hashtags": ht, "caption_length": self.var_caption.get(),
                   "asks_for_interaction": self.var_interaction.get(), "day_of_week": self.var_day.get(),
                   "engagement": eng, "score": score}
            
            self.data.append(row)
            self.tree.insert("", tk.END, iid=self.post_id_counter, values=tuple(row.values()))
            self.post_id_counter += 1
        except ValueError:
            messagebox.showerror("Error", "Invalid inputs.")

    def load_csv(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            _, score, _ = classifier.classify_engagement(
                row["content_type"], row["posting_hour"], row["num_hashtags"],
                row["caption_length"], row["asks_for_interaction"], row["day_of_week"]
            )
            row_dict = row.to_dict()
            row_dict["post_id"] = self.post_id_counter
            row_dict["score"] = score
            self.data.append(row_dict)
            self.tree.insert("", tk.END, iid=self.post_id_counter, values=tuple(row_dict.values()))
            self.post_id_counter += 1

    def save_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv")
        if filepath: pd.DataFrame(self.data).to_csv(filepath, index=False)

    def delete_selected(self, event=None):
        for item in self.tree.selection():
            self.data = [d for d in self.data if d["post_id"] != int(item)]
            self.tree.delete(item)

    def clear_data(self):
        self.tree.delete(*self.tree.get_children())
        self.data.clear()

    def analyze_trends(self):
        if self.data: classifier.plot_visualizations(pd.DataFrame(self.data))

    def show_insights(self):
        if not self.data: return
        top = tk.Toplevel(self.root)
        top.title("Insights")
        txt = tk.Text(top, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True)
        for i in classifier.generate_insights(pd.DataFrame(self.data)):
            txt.insert(tk.END, "- " + i + "\n\n")

if __name__ == "__main__":
    app = EngagementApp(tk.Tk())
    app.root.mainloop()
