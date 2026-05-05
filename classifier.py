import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MAX_SCORE = 10
THRESHOLD = 5

POINTS = {
    "carousel": 2, "reel": 1, "peak_hour": 2, "shoulder_hour": 1,
    "best_day": 1, "hashtag_sweet": 2, "hashtag_ok": 1,
    "long_caption": 1, "asks_for_interaction": 2
}

PEAK_HOURS = list(range(8, 11)) + list(range(19, 22))
SHOULDER_HOURS = list(range(11, 19))
BEST_DAYS = {"Tuesday", "Wednesday", "Thursday"}

def classify_engagement(content_type, posting_hour, num_hashtags, caption_length, asks_for_interaction, day_of_week):
    breakdown = {"content_type": 0, "posting_hour": 0, "day_of_week": 0, "num_hashtags": 0, "caption_length": 0, "asks_for_interaction": 0}
    
    if content_type == "carousel": breakdown["content_type"] = POINTS["carousel"]
    elif content_type == "reel": breakdown["content_type"] = POINTS["reel"]

    if posting_hour in PEAK_HOURS: breakdown["posting_hour"] = POINTS["peak_hour"]
    elif posting_hour in SHOULDER_HOURS: breakdown["posting_hour"] = POINTS["shoulder_hour"]

    if day_of_week in BEST_DAYS: breakdown["day_of_week"] = POINTS["best_day"]

    if 10 <= num_hashtags <= 25: breakdown["num_hashtags"] = POINTS["hashtag_sweet"]
    elif 5 <= num_hashtags < 10: breakdown["num_hashtags"] = POINTS["hashtag_ok"]

    if caption_length in ("medium", "long"): breakdown["caption_length"] = POINTS["long_caption"]

    if asks_for_interaction == "yes": breakdown["asks_for_interaction"] = POINTS["asks_for_interaction"]

    score = sum(breakdown.values())
    label = "High" if score >= THRESHOLD else "Low"
    return label, score, breakdown

def load_and_predict(csv_path):
    df = pd.read_csv(csv_path)
    results = df.apply(lambda row: pd.Series(classify_engagement(
        row["content_type"], row["posting_hour"], row["num_hashtags"],
        row["caption_length"], row["asks_for_interaction"], row["day_of_week"]
    )[:2]), axis=1)
    
    df[["predicted", "score"]] = results
    df["correct"] = df["engagement"] == df["predicted"]
    accuracy = df["correct"].mean() * 100
    
    tp = ((df["predicted"] == "High") & (df["engagement"] == "High")).sum()
    tn = ((df["predicted"] == "Low")  & (df["engagement"] == "Low")).sum()
    fp = ((df["predicted"] == "High") & (df["engagement"] == "Low")).sum()
    fn = ((df["predicted"] == "Low")  & (df["engagement"] == "High")).sum()

    print("Overall Accuracy:", accuracy, "%")
    print(f"TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    return df, accuracy, (tp, tn, fp, fn)

def plot_visualizations(df):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    colors = ["green", "red"]

    ct = df.groupby(["content_type", "engagement"]).size().unstack(fill_value=0).reindex(columns=["High", "Low"], fill_value=0)
    ct.plot(kind="bar", ax=axes[0], title="Engagement by Content Type", color=colors)

    for label, grp in df.groupby("engagement"):
        color = "green" if label == "High" else "red"
        axes[1].scatter(grp["posting_hour"], [label]*len(grp), label=label, color=color)
    axes[1].set_title("Posting Hour vs Engagement")

    for label in ["High", "Low"]:
        data = df[df["engagement"] == label]["num_hashtags"]
        color = "green" if label == "High" else "red"
        if not data.empty: axes[2].hist(data, alpha=0.5, label=label, color=color)
    axes[2].set_title("Hashtag Count Distribution")

    interaction = df.groupby(["asks_for_interaction", "engagement"]).size().unstack(fill_value=0).reindex(index=["no", "yes"], columns=["High", "Low"], fill_value=0)
    interaction.plot(kind="bar", ax=axes[3], title="Impact of Interaction Request", color=colors)

    for label in ["High", "Low"]:
        scores = df[df["engagement"] == label]["score"]
        color = "green" if label == "High" else "red"
        if not scores.empty: axes[4].hist(scores, alpha=0.5, label=label, color=color)
    axes[4].set_title("Score Distribution")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_data = df.groupby(["day_of_week", "engagement"]).size().unstack(fill_value=0).reindex(index=day_order, columns=["High", "Low"], fill_value=0)
    day_data.plot(kind="bar", ax=axes[5], title="Engagement by Day of Week", color=colors)

    plt.tight_layout()
    plt.savefig("engagement_analysis.png")
    plt.show()

def run_decision_tree(df):
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        return
        
    df_enc = df.copy()
    for col in ["content_type", "caption_length", "asks_for_interaction", "day_of_week"]:
        df_enc[col] = LabelEncoder().fit_transform(df_enc[col])

    cols = ["content_type", "posting_hour", "num_hashtags", "caption_length", "asks_for_interaction", "day_of_week"]
    X = df_enc[cols]
    y = (df_enc["engagement"] == "High").astype(int)

    tree = DecisionTreeClassifier(max_depth=4, random_state=42).fit(X, y)
    print("Decision Tree Accuracy:", tree.score(X, y))
    print(export_text(tree, feature_names=cols))

def generate_insights(df):
    insights = []
    if df.empty: return ["No data available."]

    high_df = df[df['engagement'] == 'High']
    low_df = df[df['engagement'] == 'Low']

    rate = (len(high_df) / len(df)) * 100
    insights.append(f"Overall Health: {rate:.1f}% High engagement rate.")

    if not high_df.empty:
        best_type = high_df['content_type'].mode()[0] if not high_df['content_type'].empty else ""
        insights.append(f"Top Performer: {best_type}s drive the most High engagement.")
        
        synergy = high_df.groupby(['content_type', 'day_of_week']).size()
        if not synergy.empty:
            best_syn = synergy.idxmax()
            insights.append(f"Golden Window: {best_syn[0]}s on {best_syn[1]}s is most successful.")
            
        reels = high_df[high_df['content_type'] == 'reel']
        if not reels.empty: insights.append(f"Reel Timing: Best posted around {reels['posting_hour'].mode()[0]}:00.")
            
        carousels = high_df[high_df['content_type'] == 'carousel']
        if not carousels.empty: insights.append(f"Carousel Timing: Peak engagement around {carousels['posting_hour'].mode()[0]}:00.")
            
        bins = pd.cut(high_df['num_hashtags'], bins=[-1, 5, 10, 15, 20, 25, 30], labels=["0-5", "6-10", "11-15", "16-20", "21-25", "26-30"])
        if not bins.mode().empty: insights.append(f"Hashtag Strategy: Use {bins.mode()[0]} hashtags.")
            
        cap = high_df['caption_length'].mode()
        if not cap.empty: insights.append(f"Caption Length: {cap[0]} captions resonate most.")

    impact = df.groupby('asks_for_interaction')['engagement'].apply(lambda x: (x == 'High').mean())
    if 'yes' in impact and 'no' in impact:
        insights.append(f"Interaction Request Impact: difference is {(impact['yes'] - impact['no'])*100:.1f}%.")

    if not low_df.empty:
        worst = low_df['posting_hour'].mode()
        if not worst.empty: insights.append(f"Dead Zone: Posts at {worst[0]}:00 tend to underperform.")

    return insights

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", action="store_true")
    args = parser.parse_args()
    
    csv_path = os.path.join(os.path.dirname(__file__), "dataset.csv")
    if os.path.exists(csv_path):
        df, acc, conf = load_and_predict(csv_path)
        plot_visualizations(df)
        if args.tree: run_decision_tree(df)
