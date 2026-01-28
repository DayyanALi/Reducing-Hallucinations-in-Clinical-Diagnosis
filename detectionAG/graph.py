import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Load the Data
file_path = "E:\hallucination\Reducing-Hallucinations-in-Clinical-Diagnosis\detectionAG\Research_Paper_Metrics.xlsx"
df = pd.read_csv(file_path)

# --- CLEANING & PREPARATION ---
# Filter out rows with 0 total generations to avoid division errors
df = df[df['Gen_Total'] > 0] 

# Calculate specific rates
# Addition Rate = True Additions / Total Facts
df['Addition_Rate'] = df['Gen_Hallucinations'] / df['Gen_Total']
# Contradiction Rate = Contradictions / Total Facts
df['Contradiction_Rate'] = df['Gen_Contradictions'] / df['Gen_Total']
# Omission Rate = Gold Omissions / Total Gold Facts (Handle potential 0 gold totals)
df['Omission_Rate'] = df.apply(lambda x: x['Gold_Omissions'] / x['Gold_Total'] if x['Gold_Total'] > 0 else 0, axis=1)

# Set style
sns.set_theme(style="whitegrid")

# ==============================================================================
# GRAPH 1: Addition Rate by Section (All Models Combined)
# ==============================================================================
plt.figure(figsize=(10, 8))

# Aggregate sums first to get a weighted average per section
section_stats = df.groupby('Category')[['Gen_Hallucinations', 'Gen_Total']].sum().reset_index()
section_stats['Global_Addition_Rate'] = section_stats['Gen_Hallucinations'] / section_stats['Gen_Total']
section_stats = section_stats.sort_values('Global_Addition_Rate', ascending=False)

sns.barplot(data=section_stats, y='Category', x='Global_Addition_Rate', color='#4c72b0')
plt.title('Addition Rate by Section - All Models Combined', fontsize=14)
plt.xlabel('Addition Rate')
plt.ylabel('')
plt.tight_layout()
plt.show()

# ==============================================================================
# GRAPH 2: Addition Rate Heatmap (Section vs Model)
# ==============================================================================
plt.figure(figsize=(12, 10))

# Pivot: Index=Category, Columns=Model, Values=Addition_Rate
heatmap_add = df.pivot_table(index='Category', columns='Model', values='Addition_Rate', aggfunc='mean')

# Sort rows by average rate for better readability
heatmap_add['mean'] = heatmap_add.mean(axis=1)
heatmap_add = heatmap_add.sort_values('mean', ascending=False).drop(columns='mean')

sns.heatmap(heatmap_add, annot=True, fmt=".3f", cmap="Blues", linewidths=.5)
plt.title('Addition Rate by Section and Model', fontsize=16)
plt.tight_layout()
plt.show()

# ==============================================================================
# GRAPH 3: Mean Addition and Contradiction Rates by Model
# ==============================================================================
plt.figure(figsize=(12, 6))

# Aggregate sums by model
model_stats = df.groupby('Model')[['Gen_Hallucinations', 'Gen_Contradictions', 'Gen_Total']].sum().reset_index()
model_stats['Addition Rate'] = model_stats['Gen_Hallucinations'] / model_stats['Gen_Total']
model_stats['Contradiction Rate'] = model_stats['Gen_Contradictions'] / model_stats['Gen_Total']

# Melt for seaborn (Wide to Long format)
melted_stats = model_stats.melt(id_vars='Model', 
                                value_vars=['Addition Rate', 'Contradiction Rate'], 
                                var_name='Metric', value_name='Rate')

# Sort by Addition Rate
order = model_stats.sort_values('Addition Rate', ascending=True)['Model']

sns.barplot(data=melted_stats, x='Model', y='Rate', hue='Metric', order=order, palette=['#d62728', '#1f77b4'])
plt.title('Mean Addition and Contradiction Rates by Model', fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# ==============================================================================
# GRAPH 4: Omission Rate Heatmap (Section vs Model)
# ==============================================================================
plt.figure(figsize=(12, 10))

# Pivot data
heatmap_omit = df.pivot_table(index='Category', columns='Model', values='Omission_Rate', aggfunc='mean')

# Sort rows
heatmap_omit['mean'] = heatmap_omit.mean(axis=1)
heatmap_omit = heatmap_omit.sort_values('mean', ascending=False).drop(columns='mean')

sns.heatmap(heatmap_omit, annot=True, fmt=".3f", cmap="Reds", linewidths=.5)
plt.title('Omission Rate by Section and Model', fontsize=16)
plt.tight_layout()
plt.show()

# ==============================================================================
# GRAPH 5: Overall Omission Rate per Model
# ==============================================================================
plt.figure(figsize=(10, 6))

# Calculate global omission rate per model (Total Omitted / Total Gold)
omission_stats = df.groupby('Model')[['Gold_Omissions', 'Gold_Total']].sum().reset_index()
omission_stats['Global_Omission_Rate'] = omission_stats['Gold_Omissions'] / omission_stats['Gold_Total']
omission_stats = omission_stats.sort_values('Global_Omission_Rate', ascending=True)

sns.barplot(data=omission_stats, x='Model', y='Global_Omission_Rate', color='#d62728')
plt.title('Overall Omission Rate by Model', fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()